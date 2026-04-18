#!/usr/bin/env python3
"""测试 Gitea Files API"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from extensions.ext_database import db
from models.account import Account
from services.gitea_storage_service import GiteaStorageService

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:difyai123456@127.0.0.1:5432/dify'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 30,
    'max_overflow': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
db.init_app(app)

with app.app_context():
    # 获取最近登录的用户
    account = db.session.query(Account).filter(
        Account.last_login_at.isnot(None)
    ).order_by(Account.last_login_at.desc()).first()
    
    if not account:
        print("✗ 没有找到登录用户")
        sys.exit(1)
    
    print(f"\n测试用户: {account.email}")
    print("=" * 80)
    
    # 获取配置
    config = account.custom_config_dict
    
    if not config or not config.get('gitea_url'):
        print("✗ 用户没有 FileBay 配置")
        sys.exit(1)
    
    print(f"\nFileBay 配置:")
    print(f"  URL:   {config.get('gitea_url')}")
    print(f"  Owner: {config.get('gitea_owner')}")
    print(f"  Repo:  {config.get('gitea_repo')}")
    print(f"  Token: {'***' if config.get('gitea_token') else 'None'}")
    
    # 设置环境变量
    os.environ['GITEA_URL'] = config['gitea_url']
    os.environ['GITEA_OWNER'] = config['gitea_owner']
    os.environ['GITEA_REPO'] = config['gitea_repo']
    os.environ['GITEA_TOKEN'] = config['gitea_token']
    os.environ['GITEA_PATH'] = config.get('gitea_path', 'masked')
    
    print(f"\n测试 GiteaStorageService...")
    print("-" * 80)
    
    try:
        service = GiteaStorageService()
        print("✓ GiteaStorageService 初始化成功")
        
        # 测试列出文件
        print(f"\n测试 list_files('')...")
        files = service.list_files('')
        print(f"✓ 成功获取文件列表，共 {len(files)} 个文件/目录")
        
        for file in files[:5]:  # 只显示前 5 个
            print(f"  - {file.get('name')} ({file.get('type')})")
        
        if len(files) > 5:
            print(f"  ... 还有 {len(files) - 5} 个文件")
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"\n{'='*80}")
    print("✓ 所有测试通过!")
