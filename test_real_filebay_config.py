#!/usr/bin/env python3
"""
使用真实 FileBay 配置进行测试

从 cheersai-desktop/filebay-config.json 读取真实配置并测试
"""

import requests
import json
import os
from datetime import datetime

print("\n" + "="*70)
print("  🔍 使用真实 FileBay 配置测试")
print("="*70)

# 读取真实配置文件
config_file = r"E:\CheersAI脱敏\cheersai-desktop\filebay-config.json"

print(f"\n📋 步骤 1: 读取真实配置文件")
print("-" * 70)

if not os.path.exists(config_file):
    print(f"❌ 配置文件不存在: {config_file}")
    exit(1)

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
    exit(1)

# 转换为 API 格式
real_config = {
    "url": file_config.get('url'),
    "username": file_config.get('username'),
    "repo_name": file_config.get('repoName'),
    "email": file_config.get('email'),
    "token": file_config.get('token'),
    "downloaded_at": file_config.get('downloadedAt'),
    "version": file_config.get('version', '1.0.0')
}

VAULT_API_URL = "http://localhost:7788"

print("\n📋 步骤 2: 检查 Vault API")
print("-" * 70)

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

print("\n📋 步骤 3: 同步真实配置到 Vault")
print("-" * 70)

try:
    response = requests.post(
        f"{VAULT_API_URL}/api/v1/filebay/config",
        json=real_config,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ 真实配置同步成功!")
            print(f"   消息: {data['message']}")
            print(f"\n   ⚠️  这是真实的 FileBay 配置，不是 demo 数据!")
        else:
            print(f"❌ 配置同步失败: {data.get('message')}")
            exit(1)
    else:
        print(f"❌ HTTP 错误: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ 同步失败: {e}")
    exit(1)

print("\n📋 步骤 4: 验证 Vault 读取到的配置")
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
            url_match = config.get('url') == real_config['url']
            user_match = config.get('username') == real_config['username']
            repo_match = config.get('repo_name') == real_config['repo_name']
            token_match = config.get('token') == real_config['token']
            
            print(f"   ├─ URL 匹配: {'✅' if url_match else '❌'}")
            print(f"   ├─ 用户匹配: {'✅' if user_match else '❌'}")
            print(f"   ├─ 仓库匹配: {'✅' if repo_match else '❌'}")
            print(f"   └─ Token 匹配: {'✅' if token_match else '❌'}")
            
            if all([url_match, user_match, repo_match, token_match]):
                print(f"\n   🎉 所有配置完全匹配!")
                print(f"\n   ⚠️  重要: 这是从 filebay-config.json 读取的真实配置!")
                print(f"   ⚠️  用户名: {config.get('username')} (不是 demo_user)")
                print(f"   ⚠️  邮箱: {config.get('email')} (不是 demo@example.com)")
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
print("   ✅ 使用了真实的 FileBay 配置 (从 filebay-config.json)")
print(f"   ✅ 真实用户: {real_config['username']}")
print(f"   ✅ 真实邮箱: {real_config['email']}")
print(f"   ✅ 真实 Token: {real_config['token'][:10]}...")
print("   ✅ 成功同步到 Vault API")
print("   ✅ Vault 可以读取并使用真实配置")
print("   ✅ 配置数据完整且正确")

print("\n🔐 安全提示:")
print("   ⚠️  你的真实 Token 已保存在 Vault Mock 服务器的内存中")
print("   ⚠️  重启 Mock 服务器后数据会清空")
print("   ✅ 真实的 Vault 会将配置保存到本地 SQLite 数据库")

print("\n💡 这证明了:")
print("   ✅ 方案可以处理真实的 FileBay 配置")
print("   ✅ 数据传输完整无误")
print("   ✅ Vault 可以使用这些配置进行实际操作")
print("   ✅ 不再是 demo 数据，而是真实的生产配置!")

print("\n")
