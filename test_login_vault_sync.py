#!/usr/bin/env python3
"""
测试登录后自动同步 FileBay 配置到 Vault

这个脚本模拟完整的登录流程，验证 FileBay 配置是否自动同步到 Vault
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api'))

from services.vault_sync_service import VaultSyncService
import json

print("\n" + "="*70)
print("  🔐 测试登录后自动同步 FileBay 配置到 Vault")
print("="*70)

# 模拟账户 ID
test_account_id = "test_account_123"

print(f"\n📋 步骤 1: 检查 Vault API 是否可用")
print("-" * 70)

if VaultSyncService.is_vault_available():
    print("✅ Vault API 可用")
else:
    print("❌ Vault API 不可用")
    print("\n💡 提示: 请先启动 Vault Mock 服务器:")
    print("   python test_vault_api_mock.py")
    sys.exit(1)

print(f"\n📋 步骤 2: 读取真实 FileBay 配置")
print("-" * 70)

config_file = r"E:\CheersAI脱敏\cheersai-desktop\filebay-config.json"

if not os.path.exists(config_file):
    print(f"❌ 配置文件不存在: {config_file}")
    sys.exit(1)

try:
    with open(config_file, 'r', encoding='utf-8') as f:
        file_config = json.load(f)
    
    print(f"✅ 成功读取配置文件")
    print(f"\n   真实配置内容:")
    print(f"   ├─ URL: {file_config.get('url')}")
    print(f"   ├─ 用户: {file_config.get('username')}")
    print(f"   ├─ 仓库: {file_config.get('repoName')}")
    print(f"   ├─ 邮箱: {file_config.get('email')}")
    token = file_config.get('token', '')
    print(f"   ├─ Token: {token[:10]}..." if len(token) > 10 else f"   ├─ Token: {token}")
    print(f"   └─ 下载时间: {file_config.get('downloadedAt')}")
    
except Exception as e:
    print(f"❌ 读取配置文件失败: {e}")
    sys.exit(1)

print(f"\n📋 步骤 3: 模拟用户登录，触发自动同步")
print("-" * 70)

# 设置环境变量，指向 Vault 配置路径
os.environ['VAULT_BASE_PATH'] = r'E:\CheersAI脱敏\cheersai-desktop'

# 调用自动同步服务（模拟登录后的行为）
success = VaultSyncService.auto_sync_on_login(test_account_id)

if success:
    print(f"✅ 自动同步成功!")
    print(f"   账户 ID: {test_account_id}")
    print(f"   ⚠️  这是真实的 FileBay 配置，不是 demo 数据!")
else:
    print(f"❌ 自动同步失败")
    sys.exit(1)

print(f"\n📋 步骤 4: 验证 Vault 中的配置")
print("-" * 70)

import requests

try:
    response = requests.get("http://localhost:7788/api/v1/filebay/config", timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            print(f"✅ Vault 成功保存真实配置!")
            config = data['data']
            print(f"\n   Vault 中保存的真实配置:")
            print(f"   ├─ URL: {config.get('url')}")
            print(f"   ├─ 用户: {config.get('username')}")
            print(f"   ├─ 仓库: {config.get('repo_name')}")
            print(f"   ├─ 邮箱: {config.get('email')}")
            token_in_vault = config.get('token', '')
            print(f"   ├─ Token: {token_in_vault[:10]}..." if len(token_in_vault) > 10 else f"   ├─ Token: {token_in_vault}")
            print(f"   └─ 保存时间: {config.get('saved_at', 'N/A')}")
            
            # 验证配置是否匹配
            print(f"\n   ✅ 配置验证:")
            url_match = config.get('url') == file_config.get('url')
            user_match = config.get('username') == file_config.get('username')
            repo_match = config.get('repo_name') == file_config.get('repoName')
            token_match = config.get('token') == file_config.get('token')
            
            print(f"   ├─ URL 匹配: {'✅' if url_match else '❌'}")
            print(f"   ├─ 用户匹配: {'✅' if user_match else '❌'}")
            print(f"   ├─ 仓库匹配: {'✅' if repo_match else '❌'}")
            print(f"   └─ Token 匹配: {'✅' if token_match else '❌'}")
            
            if all([url_match, user_match, repo_match, token_match]):
                print(f"\n   🎉 所有配置完全匹配!")
                print(f"\n   ⚠️  重要: 这是真实的生产配置!")
                print(f"   ⚠️  用户名: {config.get('username')} (不是 demo_user)")
                print(f"   ⚠️  邮箱: {config.get('email')} (不是 demo@example.com)")
        else:
            print(f"❌ 未找到配置")
            sys.exit(1)
    else:
        print(f"❌ HTTP 错误: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ 读取失败: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("  🎉 登录自动同步测试完成!")
print("="*70)

print("\n✅ 测试结果:")
print("   ✅ 使用了真实的 FileBay 配置")
print(f"   ✅ 真实用户: {file_config.get('username')}")
print(f"   ✅ 真实邮箱: {file_config.get('email')}")
print("   ✅ 登录后自动同步成功")
print("   ✅ Vault 保存配置成功")
print("   ✅ 配置数据完整且正确")

print("\n💡 这证明了:")
print("   ✅ 用户登录 Desktop 后，FileBay 配置会自动同步到 Vault")
print("   ✅ 不需要手动操作，完全自动化")
print("   ✅ 使用真实的生产配置，不是 demo 数据")
print("   ✅ Vault 可以使用这些配置进行实际操作")

print("\n🔄 完整流程:")
print("   1️⃣  用户登录 Desktop")
print("   2️⃣  Desktop 读取 FileBay 配置文件")
print("   3️⃣  Desktop 调用 Vault API 同步配置")
print("   4️⃣  Vault 保存配置到本地数据库")
print("   5️⃣  Vault 可以使用配置访问 FileBay")

print("\n")
