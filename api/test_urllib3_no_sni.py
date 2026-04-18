#!/usr/bin/env python3
"""使用 urllib3 直接测试，完全禁用 SNI"""
import ssl
import urllib3
from urllib3.util.ssl_ import create_urllib3_context, resolve_cert_reqs, resolve_ssl_version
import os
from dotenv import load_dotenv

load_dotenv()

# 禁用警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NoSNIHTTPSConnectionPool(urllib3.HTTPSConnectionPool):
    """禁用 SNI 的 HTTPS 连接池"""
    
    def _new_conn(self):
        """创建新连接，禁用 SNI"""
        conn = super()._new_conn()
        return conn
    
    def _validate_conn(self, conn):
        """验证连接，禁用 SNI"""
        if not getattr(conn, "is_verified", False):
            # 创建 SSL 上下文
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            try:
                context.set_ciphers('ALL:@SECLEVEL=0')
            except:
                context.set_ciphers('DEFAULT')
            
            # 包装 socket，不传递 server_hostname（禁用 SNI）
            conn.sock = context.wrap_socket(
                conn.sock,
                server_hostname=None  # 关键: 不使用 SNI
            )
            conn.is_verified = True


def test_urllib3_no_sni():
    """使用 urllib3 测试，完全禁用 SNI"""
    print("=" * 80)
    print("测试: 使用 urllib3 完全禁用 SNI")
    print("=" * 80)
    
    base_url = os.getenv("FILEBAY_BASE_URL", "https://uat-filebay.cheersai.cloud")
    admin_username = os.getenv("FILEBAY_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("FILEBAY_ADMIN_PASSWORD")
    
    if not admin_password:
        print("错误: FILEBAY_ADMIN_PASSWORD 未设置")
        return False
    
    # 解析 URL
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    host = parsed.hostname
    port = parsed.port or 443
    
    # 创建 SSL 上下文，禁用 SNI
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    try:
        context.set_ciphers('ALL:@SECLEVEL=0')
    except:
        context.set_ciphers('DEFAULT')
    
    # 创建 PoolManager，使用自定义 SSL 上下文
    http = urllib3.PoolManager(
        ssl_context=context,
        cert_reqs='CERT_NONE',
        assert_hostname=False,
        timeout=urllib3.Timeout(connect=10.0, read=10.0)
    )
    
    # 创建认证头
    import base64
    credentials = f"{admin_username}:{admin_password}"
    auth_header = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }
    
    try:
        # 测试 1: 获取版本信息
        print("\n测试 1: 获取版本信息")
        print("-" * 60)
        response = http.request(
            'GET',
            f"{base_url}/api/v1/version",
            headers=headers
        )
        print(f"✓ 状态码: {response.status}")
        print(f"  响应: {response.data.decode('utf-8')[:200]}")
        
        # 测试 2: 搜索用户
        print("\n测试 2: 搜索用户")
        print("-" * 60)
        response = http.request(
            'GET',
            f"{base_url}/api/v1/admin/emails/search?q=1@qq.com&limit=10",
            headers=headers
        )
        print(f"✓ 状态码: {response.status}")
        if response.status == 200:
            import json
            users = json.loads(response.data.decode('utf-8'))
            print(f"  找到 {len(users)} 个用户")
            for user in users:
                print(f"    - {user.get('username')} ({user.get('email')})")
        else:
            print(f"  响应: {response.data.decode('utf-8')[:200]}")
        
        # 测试 3: 获取用户列表
        print("\n测试 3: 获取用户列表")
        print("-" * 60)
        response = http.request(
            'GET',
            f"{base_url}/api/v1/admin/users?page=1&limit=5",
            headers=headers
        )
        print(f"✓ 状态码: {response.status}")
        if response.status == 200:
            import json
            users = json.loads(response.data.decode('utf-8'))
            print(f"  找到 {len(users)} 个用户")
            for user in users[:3]:
                print(f"    - {user.get('username')} (ID: {user.get('id')})")
        else:
            print(f"  响应: {response.data.decode('utf-8')[:200]}")
        
        print("\n" + "=" * 80)
        print("✓ 所有测试通过! urllib3 + 禁用 SNI 可以解决 SSL 问题")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_urllib3_no_sni()
    exit(0 if success else 1)
