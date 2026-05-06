#!/usr/bin/env python3
"""
Vault 集成演示脚本

演示 Desktop 如何与 Vault API 集成
"""

import requests
import json
from datetime import datetime

print("\n" + "="*70)
print("  🎯 Vault 集成演示")
print("="*70)

# 配置
VAULT_API_URL = "http://localhost:7788"

# 模拟用户登录后获取的 FileBay 配置
user_filebay_config = {
    "url": "https://uat-filebay.cheersai.cloud",
    "username": "demo_user",
    "repo_name": "workspace",
    "email": "demo@example.com",
    "token": "demo_token_abc123xyz",
    "downloaded_at": datetime.now().isoformat(),
    "version": "1.0"
}

print("\n📋 步骤 1: 检查 Vault 是否运行")
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
    print(f"   请确保 Vault Mock 服务器正在运行:")
    print(f"   python test_vault_api_mock.py")
    exit(1)

print("\n📋 步骤 2: 模拟用户登录 Desktop")
print("-" * 70)
print(f"用户邮箱: {user_filebay_config['email']}")
print(f"FileBay URL: {user_filebay_config['url']}")
print(f"FileBay 用户: {user_filebay_config['username']}")
print(f"FileBay 仓库: {user_filebay_config['repo_name']}")

print("\n📋 步骤 3: Desktop 自动同步配置到 Vault")
print("-" * 70)

try:
    response = requests.post(
        f"{VAULT_API_URL}/api/v1/filebay/config",
        json=user_filebay_config,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ 配置同步成功!")
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

print("\n📋 步骤 4: Vault 读取配置")
print("-" * 70)

try:
    response = requests.get(
        f"{VAULT_API_URL}/api/v1/filebay/config",
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            print(f"✅ Vault 成功读取配置!")
            config = data['data']
            print(f"\n   配置详情:")
            print(f"   ├─ URL: {config.get('url')}")
            print(f"   ├─ 用户: {config.get('username')}")
            print(f"   ├─ 仓库: {config.get('repo_name')}")
            print(f"   ├─ 邮箱: {config.get('email')}")
            print(f"   ├─ Token: {config.get('token')[:10]}..." if len(config.get('token', '')) > 10 else config.get('token'))
            print(f"   └─ 保存时间: {config.get('saved_at', 'N/A')}")
        else:
            print(f"❌ 未找到配置")
            exit(1)
    else:
        print(f"❌ HTTP 错误: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ 读取失败: {e}")
    exit(1)

print("\n📋 步骤 5: Vault 使用配置进行文件脱敏")
print("-" * 70)
print("✅ Vault 现在可以使用这个配置:")
print("   - 上传脱敏后的文件到 FileBay")
print("   - 从 FileBay 下载文件")
print("   - 管理用户的文件仓库")

print("\n" + "="*70)
print("  🎉 演示完成!")
print("="*70)

print("\n💡 关键优势:")
print("   ✅ 无文件权限问题 - 通过 HTTP API 通信")
print("   ✅ 自动同步 - 用户登录后自动完成")
print("   ✅ 不影响登录 - 同步失败不影响用户登录")
print("   ✅ 安全 - API 只监听本地,不对外暴露")

print("\n📚 相关文档:")
print("   - 详细方案: docs/VAULT_INTEGRATION.md")
print("   - 使用指南: docs/VAULT_INTEGRATION_USAGE.md")
print("   - 快速参考: VAULT_INTEGRATION_QUICK_REFERENCE.md")

print("\n")
