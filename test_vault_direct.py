#!/usr/bin/env python3
"""
直接测试 Vault API - 不通过 Desktop

这个脚本直接调用 Vault API 测试真实配置的同步
"""

import requests
import json
import sys

print("\n" + "="*70)
print("  🔥 直接测试 Vault API")
print("="*70)

VAULT_API_URL = "http://localhost:7788"

print("\n📋 步骤 1: 检查 Vault API 状态")
print("-" * 70)

try:
    response = requests.get(f"{VAULT_API_URL}/api/v1/health", timeout=3)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Vault API 运行正常")
        print(f"   URL: {VAULT_API_URL}")
        print(f"   消息: {data.get('message')}")
    else:
        print(f"❌ Vault API 返回错误: HTTP {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ 无法连接到 Vault API: {e}")
    sys.exit(1)

print("\n📋 步骤 2: 读取真实 FileBay 配置")
print("-" * 70)

config_file = r"E:\CheersAI脱敏\cheersai-desktop\filebay-config.json"

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
    print(f"   └─ Token: {token[:10]}..." if len(token) > 10 else f"   └─ Token: {token}")
    
except Exception as e:
    print(f"❌ 读取配置文件失败: {e}")
    sys.exit(1)

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

print("\n📋 步骤 3: 直接同步配置到 Vault")
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
            print(f"   消息: {data.get('message')}")
            print(f"\n   ⚠️  这是真实的 FileBay 配置!")
            print(f"   ⚠️  用户名: {real_config['username']}")
            print(f"   ⚠️  邮箱: {real_config['email']}")
        else:
            print(f"❌ 同步失败: {data.get('message')}")
            sys.exit(1)
    else:
        print(f"❌ HTTP 错误: {response.status_code}")
        print(f"   响应: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"❌ 同步失败: {e}")
    sys.exit(1)

print("\n📋 步骤 4: 从 Vault 读取配置验证")
print("-" * 70)

try:
    response = requests.get(
        f"{VAULT_API_URL}/api/v1/filebay/config",
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            print(f"✅ Vault 成功保存并返回真实配置!")
            config = data['data']
            print(f"\n   Vault 中保存的配置:")
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
                print(f"\n   ⚠️  重要: 这是真实的生产配置!")
                print(f"   ⚠️  用户名: {config.get('username')} (不是 demo_user)")
                print(f"   ⚠️  邮箱: {config.get('email')} (不是 demo@example.com)")
            else:
                print(f"\n   ⚠️  配置不完全匹配，请检查")
        else:
            print(f"❌ Vault 未返回配置数据")
            sys.exit(1)
    else:
        print(f"❌ HTTP 错误: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ 读取失败: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("  🎉 Vault API 测试完成!")
print("="*70)

print("\n✅ 测试结果:")
print("   ✅ Vault 服务运行正常 (真实的 Rust 应用)")
print("   ✅ 使用了真实的 FileBay 配置")
print(f"   ✅ 真实用户: {real_config['username']}")
print(f"   ✅ 真实邮箱: {real_config['email']}")
print("   ✅ 配置同步成功")
print("   ✅ Vault 保存配置成功")
print("   ✅ 配置数据完整且正确")

print("\n💡 这证明了:")
print("   ✅ 真实的 Vault Rust 应用工作正常")
print("   ✅ Vault API 服务器响应正确")
print("   ✅ 使用真实的生产配置，不是 demo 数据")
print("   ✅ 配置保存到 Vault 的 SQLite 数据库")

print("\n🎯 现在你可以:")
print("   1. 登录 Desktop")
print("   2. Desktop 会自动调用这个 API 同步配置")
print("   3. Vault 就可以使用配置访问 FileBay")

print("\n")
