"""Write file to FileBay repository"""
import base64
import json
import socket
import ssl
from collections.abc import Generator
from typing import Any
from urllib.parse import urlparse

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class NoSNIHTTPSClient:
    """HTTPS client without SNI for FileBay compatibility"""
    
    def __init__(self, base_url: str, token: str = "", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        
        parsed = urlparse(self.base_url)
        self.host = parsed.hostname
        self.port = parsed.port or 443
    
    def _create_ssl_socket(self) -> ssl.SSLSocket:
        """Create SSL socket without SNI"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        try:
            context.set_ciphers('ALL:@SECLEVEL=0')
        except:
            context.set_ciphers('DEFAULT')
        
        ssl_sock = context.wrap_socket(sock)
        return ssl_sock
    
    def _send_request(self, method: str, path: str, body: bytes = None) -> tuple[int, bytes]:
        """Send HTTP request"""
        ssl_sock = self._create_ssl_socket()
        
        try:
            headers = {
                "Host": self.host,
                "User-Agent": "Dify-FileBay-Plugin/1.0",
                "Accept": "application/json",
                "Connection": "close"
            }
            
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            
            if body:
                headers["Content-Type"] = "application/json"
                headers["Content-Length"] = str(len(body))
            
            request_line = f"{method} {path} HTTP/1.1\r\n"
            header_lines = "\r\n".join(f"{k}: {v}" for k, v in headers.items())
            request = f"{request_line}{header_lines}\r\n\r\n"
            
            ssl_sock.sendall(request.encode('utf-8'))
            if body:
                ssl_sock.sendall(body)
            
            response_data = b""
            while True:
                chunk = ssl_sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            header_end = response_data.find(b'\r\n\r\n')
            if header_end == -1:
                raise ValueError("Invalid HTTP response")
            
            header_part = response_data[:header_end].decode('utf-8', errors='ignore')
            body_part = response_data[header_end + 4:]
            
            lines = header_part.split('\r\n')
            status_code = int(lines[0].split()[1])
            
            return status_code, body_part
            
        finally:
            ssl_sock.close()
    
    def get(self, path: str) -> tuple[int, bytes]:
        """Send GET request"""
        return self._send_request("GET", path)
    
    def post(self, path: str, data: dict) -> tuple[int, bytes]:
        """Send POST request"""
        body = json.dumps(data).encode('utf-8')
        return self._send_request("POST", path, body)
    
    def put(self, path: str, data: dict) -> tuple[int, bytes]:
        """Send PUT request"""
        body = json.dumps(data).encode('utf-8')
        return self._send_request("PUT", path, body)


class WriteFileTool(Tool):
    """Tool for writing files to FileBay repository"""
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        Write a file to FileBay repository
        
        Args:
            tool_parameters: Dictionary containing:
                - file_path: Path where the file will be saved
                - content: Content to write
                - commit_message: Commit message (optional)
                - encoding: Content encoding (utf-8, gbk, or binary)
        
        Yields:
            ToolInvokeMessage: Message containing the operation result
        """
        file_path = tool_parameters.get('file_path', '').strip().lstrip('/')
        content = tool_parameters.get('content', '')
        commit_message = tool_parameters.get('commit_message', 'Update file via Dify agent')
        encoding = tool_parameters.get('encoding', 'utf-8')
        
        if not file_path:
            yield self.create_text_message("Error: file_path is required")
            return
        
        if not content:
            yield self.create_text_message("Error: content is required")
            return
        
        # Get credentials
        filebay_url = self.runtime.credentials.get('filebay_url', '').rstrip('/')
        filebay_token = self.runtime.credentials.get('filebay_token', '')
        filebay_owner = self.runtime.credentials.get('filebay_owner', '')
        filebay_repo = self.runtime.credentials.get('filebay_repo', '')
        filebay_branch = self.runtime.credentials.get('filebay_branch', 'main')
        
        if not all([filebay_url, filebay_token, filebay_owner, filebay_repo]):
            yield self.create_text_message("Error: Missing required credentials")
            return
        
        try:
            # Create client
            client = NoSNIHTTPSClient(filebay_url, filebay_token)
            
            # Encode content to base64
            if encoding == 'binary':
                # Content is already base64 encoded
                content_base64 = content
            else:
                # Encode text content
                content_bytes = content.encode(encoding)
                content_base64 = base64.b64encode(content_bytes).decode('utf-8')
            
            # Check if file exists to get SHA (required for updates)
            api_path = f"/api/v1/repos/{filebay_owner}/{filebay_repo}/contents/{file_path}"
            status_code, response = client.get(api_path)
            
            file_sha = None
            if status_code == 200:
                # File exists, get its SHA
                try:
                    file_info = json.loads(response.decode('utf-8'))
                    file_sha = file_info.get('sha')
                except:
                    pass
            
            # Prepare payload
            payload = {
                "message": commit_message,
                "content": content_base64,
                "branch": filebay_branch
            }
            
            if file_sha:
                # Update existing file
                payload["sha"] = file_sha
            
            # Create or update file
            if file_sha:
                status_code, response = client.put(api_path, payload)
            else:
                status_code, response = client.post(api_path, payload)
            
            if status_code in (200, 201):
                result = {
                    "success": True,
                    "file_path": file_path,
                    "action": "updated" if file_sha else "created",
                    "commit_message": commit_message,
                    "branch": filebay_branch
                }
                yield self.create_json_message(result)
            else:
                try:
                    error_data = json.loads(response.decode('utf-8'))
                    error_msg = error_data.get('message', f'HTTP {status_code}')
                except:
                    error_msg = f'HTTP {status_code}'
                
                yield self.create_text_message(f"Error: Failed to write file: {error_msg}")
            
        except Exception as e:
            yield self.create_text_message(f"Error writing file: {str(e)}")
