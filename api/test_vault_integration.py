#!/usr/bin/env python3
"""
Vault 集成测试脚本

测试 Desktop 与 Vault 的集成功能
"""

import requests
import json
import time
import sys

# 配置
VAULT_API_URL = "http://localhost:7788"
DESKTOP_API_URL = "http://localhost:5001"

def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_vault_health():
    """测试 Vault 健康检查"""
    print_section("测试 1: Vault 健康检查")
    
    try:
        response = requests.get(f"{VAULT_API_URL}/api/v1/health", timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Vault API 可用")
            print(f"   响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Vault API 返回错误: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到 Vault API ({VAULT_API_URL})")
        print(f"   请确保 Vault 应用正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_save_config():
    """测试保存配置"""
    print_section("测试 2: 保存 FileBay 配置")
    
    test_config = {
        "url": "https://uat-filebay.cheersai.cloud",
        "username": "test_user",
        "repo_name": "workspace",
        "email": "test@example.com",
        "token": "test_token_123456",
        "downloaded_at": "2024-01-01T00:00:00Z",
        "version": "1.0"
    }
    
    try:
        response = requests.post(
            f"{VAULT_API_URL}/api/v1/filebay/config",
            json=test_config,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ 配置保存成功")
                print(f"   响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"❌ 配置保存失败: {data.get('message')}")
                return False
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_get_config():
    """测试获取配置"""
    print_section("测试 3: 获取 FileBay 配置")
    
    try:
        response = requests.get(
            f"{VAULT_API_URL}/api/v1/filebay/config",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                print(f"✅ 配置获取成功")
                print(f"   配置内容:")
                config = data['data']
                print(f"     URL: {config.get('url')}")
                print(f"     Username: {config.get('username')}")
                print(f"     Repo: {config.get('repo_name')}")
                print(f"     Email: {config.get('email')}")
                return True
            else:
                print(f"❌ 未找到配置")
                return False
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_delete_config():
    """测试删除配置"""
    print_section("测试 4: 删除 FileBay 配置")
    
    try:
        response = requests.delete(
            f"{VAULT_API_URL}/api/v1/filebay/config",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ 配置删除成功")
                return True
            else:
                print(f"❌ 配置删除失败: {data.get('message')}")
                return False
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_desktop_health_check():
    """测试 Desktop 健康检查接口"""
    print_section("测试 5: Desktop Vault 健康检查接口")
    
    try:
        response = requests.get(
            f"{DESKTOP_API_URL}/console/api/vault/health",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Desktop API 可用")
            print(f"   Vault 状态: {'可用' if data.get('available') else '不可用'}")
            print(f"   消息: {data.get('message')}")
            return True
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到 Desktop API ({DESKTOP_API_URL})")
        print(f"   请确保 Desktop API 正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("  Vault 集成测试")
    print("🚀" * 30)
    
    results = []
    
    # 测试 1: Vault 健康检查
    results.append(("Vault 健康检查", test_vault_health()))
    
    if not results[0][1]:
        print("\n❌ Vault 未运行，跳过后续测试")
        print_summary(results)
        return
    
    # 测试 2: 保存配置
    results.append(("保存配置", test_save_config()))
    
    # 测试 3: 获取配置
    results.append(("获取配置", test_get_config()))
    
    # 测试 4: 删除配置
    results.append(("删除配置", test_delete_config()))
    
    # 测试 5: Desktop 健康检查
    results.append(("Desktop 健康检查", test_desktop_health_check()))
    
    # 打印总结
    print_summary(results)

def print_summary(results):
    """打印测试总结"""
    print_section("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}  {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
        sys.exit(1)
