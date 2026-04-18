#!/usr/bin/env python3
"""测试 FileBay 仓库访问权限"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from extensions.ext_database import db
from models.account import Account
from services.gitea_storage_service import NoSNIHTTPSClient

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
    print(f"  Token: {config.get('gitea_token')[:10]}...{config.get('gitea_token')[-4:]}")
    
    # 创建客户端
    client = NoSNIHTTPSClient(
        config['gitea_url'],
        config['gitea_token'],
        timeout=30
    )
    
    print(f"\n测试 API 访问...")
    print("-" * 80)
    
    # 测试 1: 获取用户信息
    print(f"\n1. 测试获取用户信息 (/api/v1/user)")
    try:
        status_code, content = client.get("/api/v1/user")
        print(f"   状态码: {status_code}")
        if status_code == 200:
            import json
            data = json.loads(content.decode('utf-8'))
            print(f"   ✓ 用户名: {data.get('login')}")
            print(f"   ✓ 邮箱: {data.get('email')}")
        else:
            print(f"   ✗ 失败: {content.decode('utf-8', errors='ignore')[:200]}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    
    # 测试 2: 获取仓库信息
    print(f"\n2. 测试获取仓库信息 (/api/v1/repos/{config['gitea_owner']}/{config['gitea_repo']})")
    try:
        path = f"/api/v1/repos/{config['gitea_owner']}/{config['gitea_repo']}"
        status_code, content = client.get(path)
        print(f"   状态码: {status_code}")
        if status_code == 200:
            import json
            data = json.loads(content.decode('utf-8'))
            print(f"   ✓ 仓库名: {data.get('name')}")
            print(f"   ✓ 私有: {data.get('private')}")
            print(f"   ✓ 默认分支: {data.get('default_branch')}")
        else:
            print(f"   ✗ 失败: {content.decode('utf-8', errors='ignore')[:200]}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    
    # 测试 3: 列出根目录文件
    print(f"\n3. 测试列出根目录文件 (/api/v1/repos/{config['gitea_owner']}/{config['gitea_repo']}/contents/)")
    try:
        path = f"/api/v1/repos/{config['gitea_owner']}/{config['gitea_repo']}/contents/"
        status_code, content = client.get(path)
        print(f"   状态码: {status_code}")
        if status_code == 200:
            import json
            data = json.loads(content.decode('utf-8'))
            print(f"   ✓ 文件/目录数量: {len(data)}")
            for item in data[:5]:
                print(f"     - {item.get('name')} ({item.get('type')})")
        else:
            print(f"   ✗ 失败: {content.decode('utf-8', errors='ignore')[:200]}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    
    # 测试 4: 列出 masked 目录文件
    print(f"\n4. 测试列出 masked 目录文件 (/api/v1/repos/{config['gitea_owner']}/{config['gitea_repo']}/contents/masked)")
    try:
        path = f"/api/v1/repos/{config['gitea_owner']}/{config['gitea_repo']}/contents/masked"
        status_code, content = client.get(path)
        print(f"   状态码: {status_code}")
        if status_code == 200:
            import json
            data = json.loads(content.decode('utf-8'))
            print(f"   ✓ 文件/目录数量: {len(data)}")
            for item in data[:5]:
                print(f"     - {item.get('name')} ({item.get('type')})")
        else:
            print(f"   ✗ 失败: {content.decode('utf-8', errors='ignore')[:200]}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    
    print(f"\n{'='*80}")
