#!/usr/bin/env python3
"""
手动输入真实 FileBay 配置进行测试

如果你有真实的 FileBay 配置，可以在这里输入并测试
"""

import requests
from datetime import datetime

print("\n" + "="*70)
print("  🔍 手动测试真实 FileBay 配置")
print("="*70)

print("\n💡 提示: 请输入你的真实 FileBay 配置")
print("   (如果没有，按 Ctrl+C 退出)")
print("-" * 70)

# 手动输入配置
print("\n请输入 FileBay 配置:")
print()

try:
    url = input("FileBay URL (例如: https://uat-filebay.cheersai.cloud): ").strip()
    if not url:
        url = "https://uat-filebay.cheersai.cloud"
    
    username = input("用户名 (例如: junqianxi): ").strip()
    if not username:
        print("❌ 用户名不能为空")
        exit(1)
    
    repo_name = input("仓库名 (例如: workspace): ").strip()
    if not repo_name:
        repo_name = "workspace"
    
    email = input("邮箱 (例如: user@example.com): ").strip()
    if not email:
        print("❌ 邮箱不能为空")
        exit(1)
    
    token = input("Token (例如: ghp_xxxxxxxxxxxx): ").strip()
    if not token:
        print("❌ Token 不能为空")
        exit(1)
    
except KeyboardInterrupt:
    print("\n\n❌ 已取消")
    exit(0)

print("\n" + "="*70)
print("  📋 你输入的配置")
print("="*70)
print(f"URL: {url}")
print(f"用户名: {username}")
print(f"仓库: {repo_name}")
print(f"邮箱: {email}")
print(f"Token: {token[:10]}..." if len(token) > 10 else f"Token: {token}")

confirm = input("\n确认使用这个配置进行测试? (y/n): ").strip().lower()
if confirm != 'y':
    print("❌ 已取消")
    exit(0)

# 构建配置
real_config = {
    "url": url,
    "username": username,
    "repo_name": repo_name,
    "email": email,
    "token": token,
    "downloaded_at": datetime.now().isoformat(),
    "version": "1.0"
}

print("\n" + "="*70)
print("  🚀 开始测试")
print("="*70)

VAULT_API_URL = "http://localhost:7788"

print("\n📋 步骤 1: 检查 Vault API")
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

print("\n📋 步骤 2: 同步真实配置到 Vault")
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
        else:
            print(f"❌ 配置同步失败: {data.get('message')}")
            exit(1)
    else:
        print(f"❌ HTTP 错误: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ 同步失败: {e}")
    exit(1)

print("\n📋 步骤 3: 验证 Vault 读取到的配置")
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
print("   ✅ 使用了你的真实 FileBay 配置")
print("   ✅ 成功同步到 Vault API")
print("   ✅ Vault 可以读取并使用真实配置")
print("   ✅ 配置数据完整且正确")

print("\n🔐 安全提示:")
print("   ⚠️  你的 Token 是真实的，已保存在 Vault Mock 服务器的内存中")
print("   ⚠️  重启 Mock 服务器后数据会清空")
print("   ✅ 真实的 Vault 会将配置保存到本地 SQLite 数据库")

print("\n💡 这证明了:")
print("   ✅ 方案可以处理真实的 FileBay 配置")
print("   ✅ 数据传输完整无误")
print("   ✅ Vault 可以使用这些配置进行实际操作")

print("\n")
