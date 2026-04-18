#!/usr/bin/env python3
"""检查当前登录用户的 FileBay 配置"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from extensions.ext_database import db
from models.account import Account

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
    # 查找最近登录的用户
    accounts = db.session.query(Account).filter(
        Account.last_login_at.isnot(None)
    ).order_by(Account.last_login_at.desc()).limit(5).all()
    
    print("\n最近登录的用户:")
    print("=" * 80)
    
    for account in accounts:
        print(f"\n邮箱: {account.email}")
        print(f"姓名: {account.name}")
        print(f"最后登录: {account.last_login_at}")
        print(f"状态: {account.status}")
        
        # 检查 FileBay 配置
        config = account.custom_config_dict
        print(f"\nFileBay 配置:")
        if config and config.get('gitea_url'):
            print(f"  ✓ URL:   {config.get('gitea_url')}")
            print(f"  ✓ Owner: {config.get('gitea_owner')}")
            print(f"  ✓ Repo:  {config.get('gitea_repo')}")
            print(f"  ✓ Token: {'***' if config.get('gitea_token') else 'None'}")
        else:
            print(f"  ✗ 未配置")
            print(f"  custom_config 原始值: {account.custom_config}")
        
        print("-" * 80)
