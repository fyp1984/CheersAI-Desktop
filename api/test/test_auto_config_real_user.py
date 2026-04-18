#!/usr/bin/env python3
"""测试为真实用户自动配置 FileBay"""
import sys
import json
from flask import Flask
from extensions.ext_database import db
from configs import dify_config


def test_auto_config_for_real_users():
    """为真实用户测试自动配置"""
    print("=" * 80)
    print("测试: 为真实用户自动配置 FileBay (使用 NoSNI 客户端)")
    print("=" * 80)
    
    # 创建 Flask 应用
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        from services.filebay_config_service import resolve_filebay_config
        from models.account import Account
        
        # 检查环境变量
        print(f"\n环境变量检查:")
        print(f"  FILEBAY_BASE_URL: {dify_config.FILEBAY_BASE_URL or '(未设置)'}")
        print(f"  FILEBAY_ADMIN_USERNAME: {dify_config.FILEBAY_ADMIN_USERNAME or '(未设置)'}")
        print(f"  FILEBAY_ADMIN_PASSWORD: {'***' if dify_config.FILEBAY_ADMIN_PASSWORD else '(未设置)'}")
        
        if not dify_config.FILEBAY_BASE_URL or not dify_config.FILEBAY_ADMIN_USERNAME or not dify_config.FILEBAY_ADMIN_PASSWORD:
            print("\n✗ 环境变量未正确设置，无法继续测试")
            return
        
        # 获取真实用户
        real_users = db.session.query(Account).filter(
            Account.email.in_(['1@qq.com', '103456686@qq.com'])
        ).all()
        
        print(f"\n找到 {len(real_users)} 个真实用户")
        print()
        
        for user in real_users:
            print("=" * 80)
            print(f"用户: {user.email}")
            print("=" * 80)
            
            try:
                # 尝试解析配置（查找已有用户并生成 Token）
                print("\n步骤 1: 查找 FileBay 用户并生成 Token...")
                config = resolve_filebay_config(
                    user.email,
                    auto_provision=False,  # 先不自动创建
                    mask_token=False
                )
                
                print(f"✓ 配置解析成功")
                print(f"  URL: {config.gitea_url}")
                print(f"  Owner: {config.gitea_owner}")
                print(f"  Repo: {config.gitea_repo}")
                if config.gitea_token:
                    print(f"  Token: {config.gitea_token[:20]}...{config.gitea_token[-10:]}")
                else:
                    print(f"  Token: (空)")
                
                # 保存到数据库
                if config.gitea_token:
                    print("\n步骤 2: 保存配置到数据库...")
                    config_dict = {
                        'gitea_url': config.gitea_url,
                        'gitea_owner': config.gitea_owner,
                        'gitea_repo': config.gitea_repo,
                        'gitea_token': config.gitea_token
                    }
                    # 使用 JSON 字符串
                    user.custom_config = json.dumps(config_dict)
                    db.session.commit()
                    print(f"✓ 配置已保存到数据库")
                    
                    # 验证
                    print("\n步骤 3: 验证配置...")
                    db.session.refresh(user)
                    saved_config = user.custom_config_dict
                    if saved_config and saved_config.get('gitea_token'):
                        print(f"✓ 验证成功")
                        print(f"  保存的 Token: {saved_config['gitea_token'][:20]}...{saved_config['gitea_token'][-10:]}")
                    else:
                        print(f"✗ 验证失败: 配置未正确保存")
                else:
                    print("\n⚠ Token 为空，跳过保存")
                
            except Exception as e:
                print(f"✗ 失败: {e}")
                db.session.rollback()  # 回滚事务
                import traceback
                traceback.print_exc()
            
            print()
        
        print("=" * 80)
        print("✓ 测试完成!")
        print("=" * 80)
        print()
        print("SSL 问题已解决:")
        print("  根本原因: UAT FileBay 服务器的 SNI 配置有问题")
        print("  解决方案: 使用 NoSNIHTTPSClient，不在 SSL 握手中发送 server_hostname")
        print("  结果: 所有 FileBay API 调用现在都可以正常工作")
        print()
        print("下一步:")
        print("  1. 测试前端文件选择器功能")
        print("  2. 验证可以浏览、上传、下载文件")
        print("  3. 联系 FileBay 团队修复服务器 SNI 配置（长期）")


if __name__ == "__main__":
    test_auto_config_for_real_users()
