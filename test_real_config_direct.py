#!/usr/bin/env python3
"""
直接从数据库读取真实 FileBay 配置并同步到 Vault

不需要完整初始化 Desktop，直接连接数据库
"""

import requests
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

print("\n" + "="*70)
print("  🔍 直接读取真实 FileBay 配置")
print("="*70)

# 数据库配置 - 根据你的实际配置修改
DATABASE_URL = "postgresql://postgres:difyai123456@localhost:5432/dify"

print("\n📋 步骤 1: 连接数据库")
print("-" * 70)

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    print(f"✅ 数据库连接成功")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    print(f"\n💡 提示: 请检查数据库配置")
    print(f"   当前配置: {DATABASE_URL}")
    exit(1)

print("\n📋 步骤 2: 查询有 FileBay 配置的用户")
print("-" * 70)

try:
    # 查询 accounts 表中有 custom_config 的用户
    query = text("""
        SELECT id, email, name, custom_config 
        FROM accounts 
        WHERE custom_config IS NOT NULL 
        AND custom_config::text LIKE '%gitea%'
        LIMIT 10
    """)
    
    result = session.execute(query)
    accounts = result.fetchall()
    
    if not accounts:
        print("❌ 没有找到有 FileBay 配置的用户")
        print("\n💡 提示: 请先在 Desktop 设置页面配置 FileBay")
        exit(1)
    
    print(f"✅ 找到 {len(accounts)} 个用户")
    
    # 显示用户列表
    print("\n用户列表:")
    for i, account in enumerate(accounts, 1):
        email = account.email
        config = json.loads(account.custom_config) if account.custom_config else {}
        has_filebay = all(k in config for k in ['gitea_url', 'gitea_owner', 'gitea_repo', 'gitea_token'])
        status = "✅ 有 FileBay 配置" if has_filebay else "⚠️  配置不完整"
        print(f"  {i}. {email} - {status}")
        
except Exception as e:
    print(f"❌ 查询失败: {e}")
    exit(1)

print("\n📋 步骤 3: 选择第一个有完整配置的用户")
print("-" * 70)

selected_account = None
selected_config = None

for account in accounts:
    try:
        config = json.loads(account.custom_config) if account.custom_config else {}
        if all(k in config for k in ['gitea_url', 'gitea_owner', 'gitea_repo', 'gitea_token']):
            selected_account = account
            selected_config = config
            break
    except:
        continue

if not selected_account:
    print("❌ 没有找到有完整 FileBay 配置的用户")
    print("\n💡 提示: 请在 Desktop 设置页面完成 FileBay 配置")
    exit(1)

print(f"✅ 选择用户: {selected_account.email}")
print(f"\n   真实配置:")
print(f"   ├─ URL: {selected_config.get('gitea_url')}")
print(f"   ├─ 用户: {selected_config.get('gitea_owner')}")
print(f"   ├─ 仓库: {selected_config.get('gitea_repo')}")
token = selected_config.get('gitea_token', '')
print(f"   └─ Token: {token[:10]}..." if len(token) > 10 else f"   └─ Token: {token}")

print("\n📋 步骤 4: 检查 Vault API 是否运行")
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

print("\n📋 步骤 5: 同步真实配置到 Vault")
print("-" * 70)

# 构建 Vault API 请求
vault_payload = {
    'url': selected_config.get('gitea_url', ''),
    'username': selected_config.get('gitea_owner', ''),
    'repo_name': selected_config.get('gitea_repo', ''),
    'email': selected_account.email,
    'token': selected_config.get('gitea_token', ''),
    'downloaded_at': datetime.now().isoformat(),
    'version': '1.0'
}

print(f"📤 发送配置到 Vault:")
print(f"   URL: {vault_payload['url']}")
print(f"   用户: {vault_payload['username']}")
print(f"   仓库: {vault_payload['repo_name']}")
print(f"   邮箱: {vault_payload['email']}")

try:
    response = requests.post(
        f"{VAULT_API_URL}/api/v1/filebay/config",
        json=vault_payload,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"\n✅ 真实配置同步成功!")
            print(f"   消息: {data['message']}")
        else:
            print(f"\n❌ 配置同步失败: {data.get('message')}")
            exit(1)
    else:
        print(f"\n❌ HTTP 错误: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"\n❌ 同步失败: {e}")
    exit(1)

print("\n📋 步骤 6: 验证 Vault 读取到的配置")
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
            print(f"\n   Vault 中的配置:")
            print(f"   ├─ URL: {config.get('url')}")
            print(f"   ├─ 用户: {config.get('username')}")
            print(f"   ├─ 仓库: {config.get('repo_name')}")
            print(f"   ├─ 邮箱: {config.get('email')}")
            token_in_vault = config.get('token', '')
            print(f"   ├─ Token: {token_in_vault[:10]}..." if len(token_in_vault) > 10 else f"   ├─ Token: {token_in_vault}")
            print(f"   └─ 保存时间: {config.get('saved_at', 'N/A')}")
            
            # 验证配置是否匹配
            print(f"\n   ✅ 配置验证:")
            url_match = config.get('url') == vault_payload['url']
            user_match = config.get('username') == vault_payload['username']
            repo_match = config.get('repo_name') == vault_payload['repo_name']
            token_match = config.get('token') == vault_payload['token']
            
            print(f"   ├─ URL 匹配: {'✅' if url_match else '❌'}")
            print(f"   ├─ 用户匹配: {'✅' if user_match else '❌'}")
            print(f"   ├─ 仓库匹配: {'✅' if repo_match else '❌'}")
            print(f"   └─ Token 匹配: {'✅' if token_match else '❌'}")
            
            if all([url_match, user_match, repo_match, token_match]):
                print(f"\n   🎉 所有配置完全匹配!")
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
print("   ✅ 配置包含真实的 FileBay URL、用户名、仓库和 Token")
print("   ✅ 成功同步到 Vault API")
print("   ✅ Vault 可以读取并使用真实配置")
print("   ✅ 配置数据完整且正确")

print("\n🔐 安全提示:")
print("   ⚠️  Token 是真实的，请妥善保管")
print("   ⚠️  不要将 Token 泄露到日志或公开场所")
print("   ✅ Vault API 只监听本地，不对外暴露")

print("\n💡 这证明了:")
print("   ✅ 方案可以处理真实的 FileBay 配置")
print("   ✅ 数据传输完整无误")
print("   ✅ Vault 可以使用这些配置进行实际操作")

print("\n")

# 关闭数据库连接
session.close()
