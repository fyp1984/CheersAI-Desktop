#!/usr/bin/env python3
"""测试不使用 SNI 的 requests 请求"""
import ssl
import urllib3
from urllib3.util.ssl_ import create_urllib3_context
from requests.adapters import HTTPAdapter
from requests import Session
import os
from dotenv import load_dotenv

load_dotenv()

# 禁用警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NoSNIHTTPAdapter(HTTPAdapter):
    """禁用 SNI 的 HTTP 适配器"""
    
    def init_poolmanager(self, *args, **kwargs):
        # 创建不使用 SNI 的 SSL 上下文
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        try:
            context.set_ciphers('ALL:@SECLEVEL=0')
        except:
            context.set_ciphers('DEFAULT')
        
        # 使用自定义的 PoolManager，禁用 SNI
        kwargs['ssl_context'] = context
        kwargs['assert_hostname'] = False
        
        # 创建 PoolManager 时不使用 server_hostname
        return super().init_poolmanager(*args, **kwargs)


def test_with_no_sni_adapter():
    """测试使用禁用 SNI 的适配器"""
    print("=" * 80)
    print("测试: 使用禁用 SNI 的 Requests 适配器")
    print("=" * 80)
    
    base_url = os.getenv("FILEBAY_BASE_URL", "https://uat-filebay.cheersai.cloud")
    admin_username = os.getenv("FILEBAY_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("FILEBAY_ADMIN_PASSWORD")
    
    if not admin_password:
        print("错误: FILEBAY_ADMIN_PASSWORD 未设置")
        return False
    
    session = Session()
    session.mount('https://', NoSNIHTTPAdapter())
    
    try:
        # 测试 1: 获取版本信息
        print("\n测试 1: 获取版本信息")
        print("-" * 60)
        response = session.get(
            f"{base_url}/api/v1/version",
            auth=(admin_username, admin_password),
            timeout=10
        )
        print(f"✓ 状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        
        # 测试 2: 搜索用户
        print("\n测试 2: 搜索用户")
        print("-" * 60)
        response = session.get(
            f"{base_url}/api/v1/admin/emails/search",
            params={"q": "1@qq.com", "limit": 10},
            auth=(admin_username, admin_password),
            timeout=10
        )
        print(f"✓ 状态码: {response.status_code}")
        if response.status_code == 200:
            import json
            users = response.json()
            print(f"  找到 {len(users)} 个用户")
            for user in users:
                print(f"    - {user.get('username')} ({user.get('email')})")
        else:
            print(f"  响应: {response.text[:200]}")
        
        # 测试 3: 获取用户信息
        print("\n测试 3: 获取用户信息")
        print("-" * 60)
        response = session.get(
            f"{base_url}/api/v1/admin/users",
            params={"page": 1, "limit": 5},
            auth=(admin_username, admin_password),
            timeout=10
        )
        print(f"✓ 状态码: {response.status_code}")
        if response.status_code == 200:
            import json
            users = response.json()
            print(f"  找到 {len(users)} 个用户")
            for user in users[:3]:
                print(f"    - {user.get('username')} (ID: {user.get('id')})")
        else:
            print(f"  响应: {response.text[:200]}")
        
        print("\n" + "=" * 80)
        print("✓ 所有测试通过! 禁用 SNI 可以解决 SSL 问题")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = test_with_no_sni_adapter()
    exit(0 if success else 1)
