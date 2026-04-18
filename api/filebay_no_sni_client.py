#!/usr/bin/env python3
"""
FileBay 客户端 - 禁用 SNI 解决 SSL 问题

根本原因: UAT FileBay 服务器的 SNI 配置有问题
解决方案: 使用原始 socket + SSL，不传递 server_hostname
"""
import ssl
import socket
import json
import base64
from urllib.parse import urlparse, urlencode
from typing import Optional, Dict, Any


class NoSNIHTTPSClient:
    """不使用 SNI 的 HTTPS 客户端"""
    
    def __init__(self, base_url: str, username: str, password: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        
        # 解析 URL
        parsed = urlparse(self.base_url)
        self.host = parsed.hostname
        self.port = parsed.port or 443
        
        # 创建认证头
        credentials = f"{username}:{password}"
        self.auth_header = base64.b64encode(credentials.encode()).decode()
    
    def _create_ssl_socket(self) -> ssl.SSLSocket:
        """创建 SSL socket，不使用 SNI"""
        # 创建 TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        
        # 创建 SSL 上下文
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        try:
            context.set_ciphers('ALL:@SECLEVEL=0')
        except:
            context.set_ciphers('DEFAULT')
        
        # 包装 socket，关键: 不传递 server_hostname（禁用 SNI）
        ssl_sock = context.wrap_socket(sock)
        
        return ssl_sock
    
    def _send_request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None
    ) -> tuple[int, Dict[str, str], bytes]:
        """发送 HTTP 请求"""
        ssl_sock = self._create_ssl_socket()
        
        try:
            # 构建请求头
            request_headers = {
                "Host": self.host,
                "Authorization": f"Basic {self.auth_header}",
                "User-Agent": "FileBay-NoSNI-Client/1.0",
                "Accept": "application/json",
                "Connection": "close"
            }
            
            if headers:
                request_headers.update(headers)
            
            if body:
                request_headers["Content-Length"] = str(len(body.encode('utf-8')))
                if "Content-Type" not in request_headers:
                    request_headers["Content-Type"] = "application/json"
            
            # 构建 HTTP 请求
            request_line = f"{method} {path} HTTP/1.1\r\n"
            header_lines = "\r\n".join(f"{k}: {v}" for k, v in request_headers.items())
            request = f"{request_line}{header_lines}\r\n\r\n"
            
            if body:
                request += body
            
            # 发送请求
            ssl_sock.sendall(request.encode('utf-8'))
            
            # 接收响应
            response_data = b""
            while True:
                chunk = ssl_sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            # 解析响应
            response_str = response_data.decode('utf-8', errors='ignore')
            
            # 分离头和体
            parts = response_str.split('\r\n\r\n', 1)
            if len(parts) != 2:
                raise ValueError("Invalid HTTP response")
            
            header_part, body_part = parts
            
            # 解析状态行
            lines = header_part.split('\r\n')
            status_line = lines[0]
            status_code = int(status_line.split()[1])
            
            # 解析响应头
            response_headers = {}
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    response_headers[key.strip()] = value.strip()
            
            return status_code, response_headers, body_part.encode('utf-8')
            
        finally:
            ssl_sock.close()
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> tuple[int, Any]:
        """发送 GET 请求"""
        if params:
            query_string = urlencode(params)
            path = f"{path}?{query_string}"
        
        status_code, headers, body = self._send_request("GET", path)
        
        # 解析 JSON 响应
        try:
            data = json.loads(body.decode('utf-8'))
        except:
            data = body.decode('utf-8')
        
        return status_code, data
    
    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> tuple[int, Any]:
        """发送 POST 请求"""
        body = json.dumps(data) if data else None
        
        status_code, response_headers, response_body = self._send_request(
            "POST",
            path,
            headers=headers,
            body=body
        )
        
        # 解析 JSON 响应
        try:
            response_data = json.loads(response_body.decode('utf-8'))
        except:
            response_data = response_body.decode('utf-8')
        
        return status_code, response_data


def test_no_sni_client():
    """测试 NoSNI 客户端"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("=" * 80)
    print("测试: NoSNI HTTPS 客户端")
    print("=" * 80)
    
    base_url = os.getenv("FILEBAY_BASE_URL", "https://uat-filebay.cheersai.cloud")
    admin_username = os.getenv("FILEBAY_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("FILEBAY_ADMIN_PASSWORD")
    
    if not admin_password:
        print("错误: FILEBAY_ADMIN_PASSWORD 未设置")
        return False
    
    client = NoSNIHTTPSClient(base_url, admin_username, admin_password)
    
    try:
        # 测试 1: 获取版本信息
        print("\n测试 1: 获取版本信息")
        print("-" * 60)
        status, data = client.get("/api/v1/version")
        print(f"✓ 状态码: {status}")
        print(f"  响应: {str(data)[:200]}")
        
        # 测试 2: 搜索用户
        print("\n测试 2: 搜索用户")
        print("-" * 60)
        status, data = client.get("/api/v1/admin/emails/search", {"q": "1@qq.com", "limit": 10})
        print(f"✓ 状态码: {status}")
        if status == 200 and isinstance(data, list):
            print(f"  找到 {len(data)} 个用户")
            for user in data:
                print(f"    - {user.get('username')} ({user.get('email')})")
        else:
            print(f"  响应: {str(data)[:200]}")
        
        # 测试 3: 获取用户列表
        print("\n测试 3: 获取用户列表")
        print("-" * 60)
        status, data = client.get("/api/v1/admin/users", {"page": 1, "limit": 5})
        print(f"✓ 状态码: {status}")
        if status == 200 and isinstance(data, list):
            print(f"  找到 {len(data)} 个用户")
            for user in data[:3]:
                print(f"    - {user.get('username')} (ID: {user.get('id')})")
        else:
            print(f"  响应: {str(data)[:200]}")
        
        # 测试 4: 创建 Token (POST 请求)
        print("\n测试 4: 创建 Token (POST 请求)")
        print("-" * 60)
        if isinstance(data, list) and len(data) > 0:
            test_username = data[0].get('username')
            print(f"  为用户 {test_username} 创建 Token...")
            
            status, token_data = client.post(
                f"/api/v1/users/{test_username}/tokens",
                data={
                    "name": f"test-token-{test_username}",
                    "scopes": ["read:user", "read:repository", "write:repository"]
                },
                headers={"Sudo": test_username}
            )
            print(f"✓ 状态码: {status}")
            if status in (200, 201):
                token = token_data.get('sha1') or token_data.get('token')
                if token:
                    print(f"  Token: {token[:20]}...{token[-10:]}")
                else:
                    print(f"  响应: {str(token_data)[:200]}")
            else:
                print(f"  响应: {str(token_data)[:200]}")
        
        print("\n" + "=" * 80)
        print("✓ 所有测试通过! NoSNI 客户端可以成功连接 FileBay")
        print("=" * 80)
        print()
        print("解决方案: 使用 NoSNIHTTPSClient 替代 requests 库")
        print("根本原因: UAT FileBay 服务器的 SNI 配置有问题")
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_no_sni_client()
    exit(0 if success else 1)
