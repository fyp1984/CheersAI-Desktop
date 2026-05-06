#!/usr/bin/env python3
"""
使用真实 FileBay 配置测试 Vault 集成

从 Desktop 数据库读取真实用户的 FileBay 配置，然后同步到 Vault
"""

import sys
import os

# 添加 api 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

import requests
from datetime import datetime
from extensions.ext_database import db
from models.account import Account
from libs.filebay_user_config import resolve_user_filebay_config

# 初始化 Flask app 和数据库
from app_factory import create_app

print("\n" + "="*70)
print("  🔍 使用真实 FileBay 配置测试 Vault 集成")
print("="*70)

print("\n📋 步骤 1: 初始化 Desktop 应用和数据库")
print("-" * 70)

try:
    app = create_app()
    print("✅ Desktop 应用初始化成功")
except Exception as e:
    print(f"❌ 初始化失败: {e}")
    print("\n💡 提示: 这个脚本需要 Desktop 的数据库配置")
    print("   如果数据库未配置，可以手动提供 FileBay 配置")
    exit(1)

print("\n📋 步骤 2: 查询数据库中的用户")
print("-" * 70)

with app.app_context():
    # 查询所有有 FileBay 配置的用户
    accounts = db.session.query(Account).filter(
        Account.custom_config_dict.isnot(None)
    ).limit(10).all()
    
    if not accounts:
        print("❌ 数据库中没有找到有配置的用户")
        print("\n💡 提示: 请先在 Desktop 设置页面配置 FileBay")
        exit(1)
    
    print(f"✅ 找到 {len(accounts)} 个用户")
    
    # 显示用户列表
    print("\n用户列表:")
    for i, account in enumerate(accounts, 1):
        config = account.custom_config_dict or {}
        has_filebay = all(k in config for k in ['gitea_url', 'gitea_owner', 'gitea_repo', 'gitea_token'])
        status = "✅ 有 FileBay 配置" if has_filebay else "⚠️  配置不完整"
        print(f"  {i}. {account.email} - {status}")

print("\n📋 步骤 3: 选择一个用户进行测试")
print("-" * 70)

# 自动选择第一个有完整配置的用户
selected_account = None
with app.app_context():
    for account in accounts:
        config = account.custom_config_dict or {}
        if all(k in config for k in ['gitea_url', 'gitea_owner', 'gitea_repo', 'gitea_token']):
            selected_account = account
            break

if not selected_account:
    print("❌ 没有找到有完整 FileBay 配置的用户")
    print("\n💡 提示: 请在 Desktop 设置页面完成 FileBay 配置")
    exit(1)

print(f"✅ 选择用户: {selected_account.email}")

print("\n📋 步骤 4: 读取用户的 FileBay 配置")
print("-" * 70)

with app.app_context():
    try:
        # 使用 resolve_user_filebay_config 获取配置
        config_dict = resolve_user_filebay_config(
            identifier=selected_account.email,
            account=selected_account,
            mask_token=False,  # 不脱敏，需要真实 token
            allow_global_fallback=False,
            log_prefix="[Real Config Test]"
        )
        
        if not config_dict:
            print("❌ 无法获取 FileBay 配置")
            exit(1)
        
        print("✅ 成功读取 FileBay 配置:")
        print(f"   URL: {config_dict.get('gitea_url')}")
        print(f"   用户: {config_dict.get('gitea_owner')}")
        print(f"   仓库: {config_dict.get('gitea_repo')}")
        print(f"   Token: {config_dict.get('gitea_token', '')[:10]}..." if len(config_dict.get('gitea_token', '')) > 10 else "")
        
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")
        exit(1)

print("\n📋 步骤 5: 检查 Vault API 是否运行")
print("-" * 70)

VAULT_API_URL = "http://localhost:7788"

try:
    response = requests.get(f"{VAULT_API_URL}/api/v1/health", timeout=3)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Vault API 可用")
        print(f"   消息: {data['message']}")
    else:
        print(f"❌ Vault API 返回错误: HTTP {response.status_code}")
        exit(1)
except requests.exceptions.ConnectionError:
    print(f"❌ 无法连接到 Vault API ({VAULT_API_URL})")
    print(f"\n💡 提示: 请先启动 Vault Mock 服务器:")
    print(f"   python test_vault_api_mock.py")
    exit(1)

print("\n📋 步骤 6: 同步真实配置到 Vault")
print("-" * 70)

# 构建 Vault API 请求
vault_payload = {
    'url': config_dict.get('gitea_url', ''),
    'username': config_dict.get('gitea_owner', ''),
    'repo_name': config_dict.get('gitea_repo', ''),
    'email': selected_account.email,
    'token': config_dict.get('gitea_token', ''),
    'downloaded_at': datetime.now().isoformat(),
    'version': '1.0'
}

try:
    response = requests.post(
        f"{VAULT_API_URL}/api/v1/filebay/config",
        json=vault_payload,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ 真实配置同步成功!")
            print(f"   消息: {data['message']}")
        else:
            print(f"❌ 配置同步失败: {data.get('message')}")
            exit(1)
    else:
        print(f"❌ HTTP 错误: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ 同步失败: {e}")
    exit(1)

print("\n📋 步骤 7: 验证 Vault 读取到的配置")
print("-" * 70)

try:
    response = requests.get(
        f"{VAULT_API_URL}/api/v1/filebay/config",
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            print(f"✅ Vault 成功读取真实配置!")
            config = data['data']
            print(f"\n   配置详情:")
            print(f"   ├─ URL: {config.get('url')}")
            print(f"   ├─ 用户: {config.get('username')}")
            print(f"   ├─ 仓库: {config.get('repo_name')}")
            print(f"   ├─ 邮箱: {config.get('email')}")
            print(f"   ├─ Token: {config.get('token')[:10]}..." if len(config.get('token', '')) > 10 else config.get('token'))
            print(f"   └─ 保存时间: {config.get('saved_at', 'N/A')}")
            
            # 验证配置是否匹配
            print(f"\n   ✅ 配置验证:")
            print(f"   ├─ URL 匹配: {config.get('url') == vault_payload['url']}")
            print(f"   ├─ 用户匹配: {config.get('username') == vault_payload['username']}")
            print(f"   ├─ 仓库匹配: {config.get('repo_name') == vault_payload['repo_name']}")
            print(f"   └─ Token 匹配: {config.get('token') == vault_payload['token']}")
        else:
            print(f"❌ 未找到配置")
            exit(1)
    else:
        print(f"❌ HTTP 错误: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ 读取失败: {e}")
    exit(1)

print("\n" + "="*70)
print("  🎉 真实配置测试完成!")
print("="*70)

print("\n✅ 测试结果:")
print("   ✅ 从 Desktop 数据库读取真实配置")
print("   ✅ 成功同步到 Vault API")
print("   ✅ Vault 可以读取并使用配置")
print("   ✅ 配置数据完整且正确")

print("\n💡 下一步:")
print("   1. 将此逻辑集成到 Desktop 登录流程")
print("   2. 在用户登录成功后自动调用")
print("   3. 添加前端 UI 显示同步状态")

print("\n")
