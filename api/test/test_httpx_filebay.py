#!/usr/bin/env python3
"""使用 httpx 测试 FileBay 连接"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import httpx
from dotenv import load_dotenv
import os

load_dotenv()

FILEBAY_URL = "https://uat-filebay.cheersai.cloud"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "3DIS9cqlR8@E"


def test_httpx_connection():
    """测试 httpx 连接"""
    print("=" * 80)
    print("测试 httpx 连接到 FileBay")
    print("=" * 80)
    print()
    
    # 创建一个非常宽松的 SSL 配置
    import ssl
    
    # 方法 1: 使用 httpx 的 verify=False
    print("方法 1: httpx with verify=False")
    print("-" * 80)
    try:
        with httpx.Client(verify=False, timeout=30.0) as client:
            response = client.get(
                f"{FILEBAY_URL}/api/v1/version",
                auth=(ADMIN_USERNAME, ADMIN_PASSWORD)
            )
            print(f"✓ 连接成功!")
            print(f"  状态码: {response.status_code}")
            print(f"  响应: {response.text[:200]}")
            return True
    except Exception as e:
        print(f"✗ 连接失败: {e}")
    
    print()
    
    # 方法 2: 使用自定义 SSL 上下文
    print("方法 2: httpx with custom SSL context")
    print("-" * 80)
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        # 设置最低安全级别
        try:
            ssl_context.set_ciphers('DEFAULT@SECLEVEL=0')
        except:
            ssl_context.set_ciphers('DEFAULT')
        
        with httpx.Client(verify=ssl_context, timeout=30.0) as client:
            response = client.get(
                f"{FILEBAY_URL}/api/v1/version",
                auth=(ADMIN_USERNAME, ADMIN_PASSWORD)
            )
            print(f"✓ 连接成功!")
            print(f"  状态码: {response.status_code}")
            print(f"  响应: {response.text[:200]}")
            return True
    except Exception as e:
        print(f"✗ 连接失败: {e}")
    
    print()
    
    # 方法 3: 使用 HTTP/1.1
    print("方法 3: httpx with HTTP/1.1 only")
    print("-" * 80)
    try:
        with httpx.Client(verify=False, timeout=30.0, http1=True, http2=False) as client:
            response = client.get(
                f"{FILEBAY_URL}/api/v1/version",
                auth=(ADMIN_USERNAME, ADMIN_PASSWORD)
            )
            print(f"✓ 连接成功!")
            print(f"  状态码: {response.status_code}")
            print(f"  响应: {response.text[:200]}")
            return True
    except Exception as e:
        print(f"✗ 连接失败: {e}")
    
    print()
    return False


def test_search_user():
    """测试搜索用户"""
    print("=" * 80)
    print("测试搜索用户")
    print("=" * 80)
    print()
    
    try:
        with httpx.Client(verify=False, timeout=30.0) as client:
            # 搜索用户
            response = client.get(
                f"{FILEBAY_URL}/api/v1/admin/emails/search",
                params={"q": "1@qq.com", "limit": 10},
                auth=(ADMIN_USERNAME, ADMIN_PASSWORD)
            )
            
            print(f"✓ 搜索成功!")
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                users = response.json()
                print(f"  找到用户数: {len(users) if isinstance(users, list) else 'N/A'}")
                
                if isinstance(users, list):
                    for user in users:
                        print(f"\n  用户信息:")
                        print(f"    邮箱: {user.get('email')}")
                        print(f"    用户名: {user.get('username')}")
                        print(f"    ID: {user.get('id')}")
                else:
                    print(f"  响应: {response.text[:500]}")
            else:
                print(f"  响应: {response.text[:500]}")
            
            return True
    except Exception as e:
        print(f"✗ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_token():
    """测试创建 Token"""
    print("=" * 80)
    print("测试创建 Token")
    print("=" * 80)
    print()
    
    # 首先搜索用户获取用户名
    print("步骤 1: 搜索用户获取用户名")
    print("-" * 80)
    
    try:
        with httpx.Client(verify=False, timeout=30.0) as client:
            response = client.get(
                f"{FILEBAY_URL}/api/v1/admin/emails/search",
                params={"q": "1@qq.com", "limit": 10},
                auth=(ADMIN_USERNAME, ADMIN_PASSWORD)
            )
            
            if response.status_code != 200:
                print(f"✗ 搜索用户失败: {response.status_code}")
                return False
            
            users = response.json()
            if not users or not isinstance(users, list):
                print(f"✗ 未找到用户")
                return False
            
            user = users[0]
            username = user.get('username') or user.get('login')
            user_id = user.get('id')
            
            print(f"✓ 找到用户:")
            print(f"  用户名: {username}")
            print(f"  ID: {user_id}")
            print()
            
            # 创建 Token
            print("步骤 2: 创建 Token")
            print("-" * 80)
            
            token_payload = {
                "name": f"desktop-test-{user_id}",
                "scopes": ["read:user", "read:repository", "write:repository"]
            }
            
            response = client.post(
                f"{FILEBAY_URL}/api/v1/users/{username}/tokens",
                json=token_payload,
                headers={"Sudo": username},
                auth=(ADMIN_USERNAME, ADMIN_PASSWORD)
            )
            
            if response.status_code in (200, 201):
                token_data = response.json()
                token = token_data.get('sha1') or token_data.get('token')
                
                print(f"✓ Token 创建成功!")
                print(f"  Token: {token[:20]}...{token[-10:]}")
                print()
                
                # 验证 Token
                print("步骤 3: 验证 Token")
                print("-" * 80)
                
                response = client.get(
                    f"{FILEBAY_URL}/api/v1/user",
                    headers={"Authorization": f"token {token}"}
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    print(f"✓ Token 验证成功!")
                    print(f"  用户名: {user_info.get('login')}")
                    print(f"  邮箱: {user_info.get('email')}")
                    print()
                    
                    # 保存配置
                    print("=" * 80)
                    print("配置信息（可用于保存）")
                    print("=" * 80)
                    print(f"邮箱: 1@qq.com")
                    print(f"用户名: {username}")
                    print(f"仓库: workspace")
                    print(f"Token: {token}")
                    print()
                    print("保存命令:")
                    print(f'python save_filebay_token.py "1@qq.com" "{username}" "workspace" "{token}"')
                    
                    return True
                else:
                    print(f"✗ Token 验证失败: {response.status_code}")
            else:
                print(f"✗ Token 创建失败: {response.status_code}")
                print(f"  响应: {response.text[:500]}")
            
            return False
            
    except Exception as e:
        print(f"✗ 操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 测试连接
    if test_httpx_connection():
        print()
        
        # 测试搜索用户
        if test_search_user():
            print()
            
            # 测试创建 Token
            test_create_token()
    
    print()
    print("=" * 80)
    print("测试完成")
    print("=" * 80)
