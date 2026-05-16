#!/usr/bin/env python3
"""为真实用户配置 FileBay"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import logging

from flask import Flask

from extensions.ext_database import db
from models.account import Account
from services.filebay_auto_provision_service import FileBayAutoProvisionService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def provision_user(email):
    """为单个用户配置 FileBay"""
    from configs import dify_config
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        logger.info("=" * 80)
        logger.info("为用户配置 FileBay: %s", email)
        logger.info("=" * 80)
        
        # 查询账号
        account = db.session.query(Account).filter_by(email=email).first()
        
        if not account:
            logger.error("✗ 未找到账号: %s", email)
            return False
        
        logger.info(f"✓ 找到账号: {account.id}")
        logger.info(f"  姓名: {account.name}")
        logger.info(f"  状态: {account.status}")
        
        # 检查是否已有配置
        if account.custom_config_dict and account.custom_config_dict.get('gitea_url'):
            logger.info("✓ 账号已有 FileBay 配置")
            config = account.custom_config_dict
            logger.info(f"  URL:   {config.get('gitea_url')}")
            logger.info(f"  Owner: {config.get('gitea_owner')}")
            logger.info(f"  Repo:  {config.get('gitea_repo')}")
            return True
        
        # 执行自动配置
        logger.info("\n开始自动配置...")
        
        try:
            service = FileBayAutoProvisionService()
            config = service.auto_provision(email)
            
            logger.info("\n✓ 自动配置成功!")
            logger.info(f"  URL:   {config['gitea_url']}")
            logger.info(f"  Owner: {config['gitea_owner']}")
            logger.info(f"  Repo:  {config['gitea_repo']}")
            logger.info(f"  Token: {config['gitea_token'][:20]}...")
            
            # 保存到数据库
            logger.info("\n保存配置到数据库...")
            account.custom_config_dict = config
            db.session.commit()
            
            # 验证保存
            db.session.refresh(account)
            saved_config = account.custom_config_dict
            
            if saved_config.get('gitea_url') == config['gitea_url']:
                logger.info("✓ 配置已保存到数据库")
                return True
            else:
                logger.error("✗ 配置保存失败")
                return False
            
        except Exception as e:
            logger.error("✗ 自动配置失败: %s", e, exc_info=True)
            return False


def provision_all_real_users():
    """为所有真实用户配置 FileBay"""
    real_users = [
        "1@qq.com",
        "103456686@qq.com",
    ]
    
    logger.info("\n" + "=" * 80)
    logger.info("为所有真实用户配置 FileBay")
    logger.info("=" * 80)
    logger.info(f"用户列表: {', '.join(real_users)}")
    logger.info("")
    
    results = []
    
    for email in real_users:
        success = provision_user(email)
        results.append((email, success))
        logger.info("")
    
    # 汇总结果
    logger.info("=" * 80)
    logger.info("配置结果汇总")
    logger.info("=" * 80)
    
    for email, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        logger.info(f"{status:10} {email}")
    
    success_count = sum(1 for _, success in results if success)
    logger.info("")
    logger.info(f"成功: {success_count}/{len(results)}")
    logger.info("=" * 80)
    
    return all(success for _, success in results)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 为特定用户配置
        email = sys.argv[1]
        success = provision_user(email)
        sys.exit(0 if success else 1)
    else:
        # 为所有真实用户配置
        success = provision_all_real_users()
        sys.exit(0 if success else 1)
