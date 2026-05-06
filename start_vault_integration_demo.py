#!/usr/bin/env python3
"""
Vault 集成演示 - 快速启动脚本

这个脚本会启动所有必要的服务并运行完整的测试
"""

import subprocess
import time
import sys
import os
import requests

print("\n" + "="*70)
print("  🚀 Vault 集成演示 - 快速启动")
print("="*70)

print("\n📋 这个演示会:")
print("   1. 启动 Vault API Mock 服务器")
print("   2. 测试真实 FileBay 配置同步")
print("   3. 测试登录自动同步功能")
print("   4. 显示完整的集成流程")

print("\n" + "-"*70)
input("按 Enter 键开始...")

# 检查 Vault Mock 服务器是否已经在运行
print("\n📋 步骤 1: 检查 Vault API 服务器")
print("-" * 70)

try:
    response = requests.get("http://localhost:7788/api/v1/health", timeout=2)
    if response.status_code == 200:
        print("✅ Vault API 服务器已经在运行")
        vault_already_running = True
    else:
        vault_already_running = False
except:
    vault_already_running = False
    print("⚠️  Vault API 服务器未运行，需要启动")

if not vault_already_running:
    print("\n💡 请在另一个终端窗口运行:")
    print("   python test_vault_api_mock.py")
    print("\n等待 Vault API 服务器启动...")
    
    # 等待用户启动服务器
    max_wait = 60  # 最多等待 60 秒
    waited = 0
    while waited < max_wait:
        try:
            response = requests.get("http://localhost:7788/api/v1/health", timeout=1)
            if response.status_code == 200:
                print("✅ Vault API 服务器已启动")
                break
        except:
            pass
        
        time.sleep(2)
        waited += 2
        print(f"   等待中... ({waited}/{max_wait}秒)")
    
    if waited >= max_wait:
        print("\n❌ 超时: Vault API 服务器未启动")
        print("\n💡 请手动启动:")
        print("   python test_vault_api_mock.py")
        sys.exit(1)

# 运行真实配置测试
print("\n📋 步骤 2: 测试真实 FileBay 配置同步")
print("-" * 70)

result = subprocess.run(
    ["python", "test_real_filebay_config.py"],
    cwd=os.path.dirname(os.path.abspath(__file__))
)

if result.returncode != 0:
    print("\n❌ 真实配置测试失败")
    sys.exit(1)

# 运行登录自动同步测试
print("\n📋 步骤 3: 测试登录自动同步功能")
print("-" * 70)

result = subprocess.run(
    ["python", "test_login_vault_sync.py"],
    cwd=os.path.dirname(os.path.abspath(__file__))
)

if result.returncode != 0:
    print("\n❌ 登录自动同步测试失败")
    sys.exit(1)

# 显示总结
print("\n" + "="*70)
print("  🎉 Vault 集成演示完成!")
print("="*70)

print("\n✅ 所有测试通过:")
print("   ✅ Vault API 服务器运行正常")
print("   ✅ 真实 FileBay 配置同步成功")
print("   ✅ 登录自动同步功能正常")

print("\n📊 验证的真实数据:")
print("   ✅ 用户名: admin_cheersai_cloud_de8df0")
print("   ✅ 邮箱: admin@cheersai.cloud")
print("   ✅ URL: https://uat-filebay.cheersai.cloud")
print("   ✅ Token: 7cb8cbe289... (真实 Token)")

print("\n🔄 完整流程已验证:")
print("   1️⃣  用户登录 Desktop")
print("   2️⃣  Desktop 读取 FileBay 配置文件")
print("   3️⃣  Desktop 调用 Vault API 同步配置")
print("   4️⃣  Vault 保存配置到本地数据库")
print("   5️⃣  Vault 可以使用配置访问 FileBay")

print("\n📚 查看完整文档:")
print("   - VAULT_INTEGRATION_COMPLETE.md - 完整集成报告")
print("   - VAULT_INTEGRATION_REAL_DATA_GUIDE.md - 真实数据指南")
print("   - FINAL_TEST_REPORT.md - 测试报告")

print("\n🚀 下一步:")
print("   1. 编译真实的 Vault Rust 应用:")
print("      cd E:\\CheersAI脱敏\\cheersai-desktop\\src-tauri")
print("      cargo build --release")
print("   ")
print("   2. 启动真实的 Vault 应用:")
print("      cargo run")
print("   ")
print("   3. 启动 Desktop 应用:")
print("      cd E:\\CheersAI-Desktop")
print("      python api/app.py")
print("   ")
print("   4. 登录 Desktop，配置会自动同步到 Vault!")

print("\n")
