#!/usr/bin/env python3
"""
服务状态检查脚本

快速检查 Vault 和 Desktop 服务是否正常运行
"""

import requests

print("\n" + "="*70)
print("  🔍 服务状态检查")
print("="*70)

# 检查 Vault
print("\n📋 Vault 服务 (http://localhost:7788)")
print("-" * 70)
try:
    response = requests.get("http://localhost:7788/api/v1/health", timeout=2)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 状态: 运行中")
        print(f"   消息: {data.get('message')}")
        
        # 检查是否有配置
        try:
            config_response = requests.get("http://localhost:7788/api/v1/filebay/config", timeout=2)
            if config_response.status_code == 200:
                config_data = config_response.json()
                if config_data.get('success') and config_data.get('data'):
                    config = config_data['data']
                    print(f"   配置: 已保存")
                    print(f"   用户: {config.get('username')}")
                    print(f"   邮箱: {config.get('email')}")
                else:
                    print(f"   配置: 未保存")
        except:
            pass
    else:
        print(f"❌ 状态: 错误 (HTTP {response.status_code})")
except requests.exceptions.ConnectionError:
    print(f"❌ 状态: 未运行")
    print(f"   提示: cd E:\\CheersAI脱敏\\cheersai-desktop\\src-tauri && cargo run")
except Exception as e:
    print(f"❌ 状态: 错误 ({e})")

# 检查 Desktop
print("\n📋 Desktop 服务 (http://localhost:5001)")
print("-" * 70)
try:
    response = requests.get("http://localhost:5001/console/api/setup", timeout=2)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 状态: 运行中")
        print(f"   设置: {data.get('step')}")
    else:
        print(f"❌ 状态: 错误 (HTTP {response.status_code})")
except requests.exceptions.ConnectionError:
    print(f"❌ 状态: 未运行")
    print(f"   提示: cd E:\\CheersAI-Desktop && python api/app.py")
except Exception as e:
    print(f"❌ 状态: 错误 ({e})")

print("\n" + "="*70)
print("  ✅ 检查完成")
print("="*70)
print()
