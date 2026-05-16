"""List files in FileBay repository"""
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
    
    def get(self, path: str) -> tuple[int, bytes]:
        """Send GET request"""
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
            
            request_line = f"GET {path} HTTP/1.1\r\n"
            header_lines = "\r\n".join(f"{k}: {v}" for k, v in headers.items())
            request = f"{request_line}{header_lines}\r\n\r\n"
            
            ssl_sock.sendall(request.encode('utf-8'))
            
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


class ListFilesTool(Tool):
    """Tool for listing files in FileBay repository"""
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        List files in a FileBay repository directory
        
        Args:
            tool_parameters: Dictionary containing:
                - directory_path: Path to the directory (optional, defaults to root)
        
        Yields:
            ToolInvokeMessage: Message containing the list of files
        """
        directory_path = tool_parameters.get('directory_path', '').strip().lstrip('/')
        
        # Get credentials
        filebay_url = self.runtime.credentials.get('filebay_url', '').rstrip('/')
        filebay_token = self.runtime.credentials.get('filebay_token', '')
        filebay_owner = self.runtime.credentials.get('filebay_owner', '')
        filebay_repo = self.runtime.credentials.get('filebay_repo', '')
        
        if not all([filebay_url, filebay_token, filebay_owner, filebay_repo]):
            yield self.create_text_message("Error: Missing required credentials")
            return
        
        try:
            # Create client
            client = NoSNIHTTPSClient(filebay_url, filebay_token)
            
            # Build API path
            api_path = f"/api/v1/repos/{filebay_owner}/{filebay_repo}/contents"
            if directory_path:
                api_path += f"/{directory_path}"
            
            # Get directory contents
            status_code, response = client.get(api_path)
            
            if status_code == 404:
                yield self.create_text_message(f"Error: Directory not found: {directory_path or '/'}")
                return
            elif status_code != 200:
                yield self.create_text_message(f"Error: Failed to list files (HTTP {status_code})")
                return
            
            # Parse response
            try:
                items = json.loads(response.decode('utf-8'))
            except:
                yield self.create_text_message("Error: Failed to parse response")
                return
            
            if not isinstance(items, list):
                yield self.create_text_message("Error: Unexpected response format")
                return
            
            # Format file list
            files = []
            directories = []
            
            for item in items:
                item_info = {
                    "name": item.get("name", ""),
                    "path": item.get("path", ""),
                    "type": item.get("type", ""),
                    "size": item.get("size", 0)
                }
                
                if item.get("type") == "dir":
                    directories.append(item_info)
                else:
                    files.append(item_info)
            
            result = {
                "directory": directory_path or "/",
                "total_items": len(items),
                "directories": directories,
                "files": files
            }
            
            yield self.create_json_message(result)
            
        except Exception as e:
            yield self.create_text_message(f"Error listing files: {str(e)}")
