"""Gitea storage service for file retrieval."""
import json
import os
import socket
import ssl
import time
from typing import Optional
from urllib.parse import urlparse


class GiteaHTTPSClient:
    """Small HTTPS client with SNI and NoSNI fallback.

    Some FileBay deployments have broken SNI. Try NoSNI first, then fall back
    to a standard TLS handshake for newer deployments.
    """
    
    def __init__(self, base_url: str, token: str = "", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        
        parsed = urlparse(self.base_url)
        self.host = parsed.hostname
        self.port = parsed.port or 443
        self.scheme = parsed.scheme
        self.host_header = self.host if self.port == 443 else f"{self.host}:{self.port}"
    
    def _create_ssl_socket(self, use_sni: bool) -> ssl.SSLSocket:
        """Create an SSL socket, optionally passing server_hostname for SNI."""
        # 创建 TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        
        # 创建 SSL 上下文
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        try:
            context.minimum_version = ssl.TLSVersion.TLSv1
        except AttributeError:
            pass
        
        try:
            context.set_ciphers('ALL:@SECLEVEL=0')
        except:
            context.set_ciphers('DEFAULT')
        
        try:
            if use_sni:
                ssl_sock = context.wrap_socket(sock, server_hostname=self.host)
            else:
                ssl_sock = context.wrap_socket(sock)
        except Exception:
            sock.close()
            raise
        
        return ssl_sock
    
    def _send_request(
        self,
        method: str,
        path: str,
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None
    ) -> tuple[int, dict[str, str], bytes]:
        """发送 HTTP 请求"""
        last_error: Exception | None = None

        for attempt in range(3):
            for use_sni in (False, True):
                try:
                    return self._send_request_once(method, path, headers, body, use_sni)
                except (ssl.SSLError, socket.timeout, OSError) as exc:
                    last_error = exc
                    continue

            if attempt < 2:
                time.sleep(0.25 * (attempt + 1))

        if last_error:
            raise last_error
        raise RuntimeError("Failed to send request")

    def _send_request_once(
        self,
        method: str,
        path: str,
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
        use_sni: bool = True,
    ) -> tuple[int, dict[str, str], bytes]:
        ssl_sock = self._create_ssl_socket(use_sni)
        
        try:
            # 构建请求头
            request_headers = {
                "Host": self.host_header,
                "User-Agent": "Gitea-Storage-Client/1.0",
                "Accept": "application/json",
                "Connection": "close"
            }
            
            if self.token:
                request_headers["Authorization"] = f"token {self.token}"
            
            if headers:
                request_headers.update(headers)
            
            if body:
                request_headers["Content-Length"] = str(len(body))
            
            # 构建 HTTP 请求
            request_line = f"{method} {path} HTTP/1.1\r\n"
            header_lines = "\r\n".join(f"{k}: {v}" for k, v in request_headers.items())
            request = f"{request_line}{header_lines}\r\n\r\n"
            
            # 发送请求
            ssl_sock.sendall(request.encode('utf-8'))
            if body:
                ssl_sock.sendall(body)
            
            # 接收响应
            response_data = b""
            while True:
                chunk = ssl_sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            # 查找头部结束位置
            header_end = response_data.find(b'\r\n\r\n')
            if header_end == -1:
                raise ValueError("Invalid HTTP response: no header end found")
            
            # 分离头和体
            header_part = response_data[:header_end].decode('utf-8', errors='ignore')
            body_part = response_data[header_end + 4:]  # 跳过 \r\n\r\n
            
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
            
            # 处理 chunked transfer encoding
            if response_headers.get('Transfer-Encoding', '').lower() == 'chunked':
                body_part = self._decode_chunked(body_part)
            
            return status_code, response_headers, body_part
            
        finally:
            ssl_sock.close()
    
    def _decode_chunked(self, data: bytes) -> bytes:
        """解码 chunked transfer encoding"""
        result = b""
        pos = 0
        
        while pos < len(data):
            # 查找块大小行的结束
            line_end = data.find(b'\r\n', pos)
            if line_end == -1:
                break
            
            # 解析块大小
            chunk_size_str = data[pos:line_end].decode('utf-8', errors='ignore').strip()
            if not chunk_size_str:
                break
            
            try:
                chunk_size = int(chunk_size_str, 16)
            except ValueError:
                break
            
            if chunk_size == 0:
                # 最后一个块
                break
            
            # 读取块数据
            chunk_start = line_end + 2  # 跳过 \r\n
            chunk_end = chunk_start + chunk_size
            result += data[chunk_start:chunk_end]
            
            # 移动到下一个块（跳过块数据后的 \r\n）
            pos = chunk_end + 2
        
        return result
    
    def get(self, path: str) -> tuple[int, bytes]:
        """发送 GET 请求"""
        status_code, headers, body = self._send_request("GET", path)
        return status_code, body


class GiteaStorageService:
    """Service for retrieving files from Gitea."""

    def __init__(self):
        """Initialize Gitea storage service."""
        self.gitea_url = os.getenv("GITEA_URL", "http://localhost:3000").rstrip("/")
        self.gitea_proxy_url = os.getenv("GITEA_PROXY_URL", "").rstrip("/")
        self.gitea_token = os.getenv("GITEA_TOKEN", "")
        self.gitea_owner = os.getenv("GITEA_OWNER", "cheersai")
        self.gitea_repo = os.getenv("GITEA_REPO", "file-storage")
        self.request_base_url = self.gitea_proxy_url or self.gitea_url

        # Token is optional for public repositories
        self.use_auth = bool(self.gitea_token)
        
        self.client = GiteaHTTPSClient(self.request_base_url, self.gitea_token)

    def get_file(self, file_path: str) -> bytes:
        """
        Get file content from Gitea repository.
        
        Args:
            file_path: Path to the file in the repository
            
        Returns:
            bytes: File content
        """
        # Use raw file URL for direct download
        path = f"/{self.gitea_owner}/{self.gitea_repo}/raw/branch/main/{file_path}"
        
        status_code, content = self.client.get(path)
        
        if status_code == 200:
            return content
        elif status_code == 404:
            raise FileNotFoundError(f"File not found in Gitea: {file_path}")
        else:
            raise Exception(f"Failed to get file from Gitea: {status_code}")

    def get_file_metadata(self, file_path: str) -> dict:
        """
        Get file metadata from Gitea repository.
        
        Args:
            file_path: Path to the file in the repository
            
        Returns:
            dict: File metadata including name, size, sha, etc.
        """
        path = f"/api/v1/repos/{self.gitea_owner}/{self.gitea_repo}/contents/{file_path}"
        
        status_code, content = self.client.get(path)
        
        if status_code == 200:
            data = json.loads(content.decode('utf-8'))
            return {
                "name": data.get("name"),
                "path": data.get("path"),
                "sha": data.get("sha"),
                "size": data.get("size"),
                "url": data.get("download_url"),
                "type": data.get("type"),
            }
        elif status_code == 404:
            raise FileNotFoundError(f"File not found in Gitea: {file_path}")
        else:
            raise Exception(f"Failed to get file metadata: {status_code}")

    def list_files(self, directory_path: str = "") -> list:
        """
        List files in a directory in Gitea repository.
        
        Args:
            directory_path: Path to the directory in the repository
            
        Returns:
            list: List of file metadata dictionaries
        """
        path = f"/api/v1/repos/{self.gitea_owner}/{self.gitea_repo}/contents/{directory_path}"
        
        status_code, content = self.client.get(path)
        
        if status_code == 200:
            data = json.loads(content.decode('utf-8'))
            if isinstance(data, list):
                return [
                    {
                        "name": item.get("name"),
                        "path": item.get("path"),
                        "type": item.get("type"),
                        "size": item.get("size"),
                        "sha": item.get("sha"),
                        "url": item.get("download_url"),
                    }
                    for item in data
                ]
            return []
        elif status_code == 404:
            raise FileNotFoundError(f"Directory not found in Gitea: {directory_path}")
        else:
            raise Exception(f"Failed to list files: {status_code}")

    def get_file_url(self, file_path: str) -> str:
        """
        Get the download URL for a file.
        
        Args:
            file_path: Path to the file in the repository
            
        Returns:
            str: Download URL
        """
        return f"{self.gitea_url}/{self.gitea_owner}/{self.gitea_repo}/raw/branch/main/{file_path}"

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in Gitea repository.
        
        Args:
            file_path: Path to the file in the repository
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.get_file_metadata(file_path)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
