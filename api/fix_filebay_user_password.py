#!/usr/bin/env python3
"""修复 FileBay 用户的 must_change_password 设置"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.filebay_config_service import _filebay_admin_request

# 用户名
username = "103456686_qq_com_nzvhyt"

print(f"\n修复 FileBay 用户: {username}")
print("=" * 80)

# 先获取用户信息
print("\n获取用户信息...")
try:
    status_code, user_data = _filebay_admin_request(
        method="GET",
        path=f"/api/v1/users/{username}"
    )
    
    if status_code != 200:
        print(f"✗ 获取用户信息失败: {status_code} {user_data}")
        sys.exit(1)
    
    print("✓ 用户信息:")
    print(f"  用户名: {user_data.get('login')}")
    print(f"  邮箱: {user_data.get('email')}")
    print(f"  must_change_password: {user_data.get('must_change_password')}")
    
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 更新用户设置
print("\n更新 must_change_password 为 False...")
try:
    update_payload = {
        "login_name": user_data.get('login'),
        "email": user_data.get('email'),
        "must_change_password": False,
    }
    status_code, data = _filebay_admin_request(
        method="PATCH",
        path=f"/api/v1/admin/users/{username}",
        json_payload=update_payload
    )
    
    print(f"状态码: {status_code}")
    if status_code in (200, 201):
        print("✓ 成功更新用户设置")
    else:
        print(f"✗ 失败: {data}")
        sys.exit(1)
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n{'=' * 80}")
print("✓ 修复完成！请刷新浏览器重试")
