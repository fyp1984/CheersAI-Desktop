"""Read file from FileBay repository"""
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
            
            response_headers = {}
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    response_headers[key.strip()] = value.strip()
            
            if response_headers.get('Transfer-Encoding', '').lower() == 'chunked':
                body_part = self._decode_chunked(body_part)
            
            return status_code, body_part
            
        finally:
            ssl_sock.close()
    
    def _decode_chunked(self, data: bytes) -> bytes:
        """Decode chunked transfer encoding"""
        result = b""
        pos = 0
        
        while pos < len(data):
            line_end = data.find(b'\r\n', pos)
            if line_end == -1:
                break
            
            chunk_size_str = data[pos:line_end].decode('utf-8', errors='ignore').strip()
            if not chunk_size_str:
                break
            
            try:
                chunk_size = int(chunk_size_str, 16)
            except ValueError:
                break
            
            if chunk_size == 0:
                break
            
            chunk_start = line_end + 2
            chunk_end = chunk_start + chunk_size
            result += data[chunk_start:chunk_end]
            pos = chunk_end + 2
        
        return result


class ReadFileTool(Tool):
    """Tool for reading files from FileBay repository"""
    
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        Read a file from FileBay repository
        
        Args:
            tool_parameters: Dictionary containing:
                - file_path: Path to the file in the repository
                - encoding: File encoding (utf-8, gbk, or binary)
        
        Yields:
            ToolInvokeMessage: Message containing the file content
        """
        file_path = tool_parameters.get('file_path', '').strip().lstrip('/')
        encoding = tool_parameters.get('encoding', 'utf-8')
        
        if not file_path:
            yield self.create_text_message("Error: file_path is required")
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
            
            # Get file content using raw endpoint
            path = f"/{filebay_owner}/{filebay_repo}/raw/branch/{filebay_branch}/{file_path}"
            status_code, content = client.get(path)
            
            if status_code == 404:
                yield self.create_text_message(f"Error: File not found: {file_path}")
                return
            elif status_code != 200:
                yield self.create_text_message(f"Error: Failed to read file (HTTP {status_code})")
                return
            
            # Decode content based on encoding
            if encoding == 'binary':
                # Return base64 encoded content for binary files
                content_str = base64.b64encode(content).decode('utf-8')
                result = {
                    "file_path": file_path,
                    "encoding": "base64",
                    "content": content_str,
                    "size": len(content)
                }
            else:
                # Decode as text
                try:
                    content_str = content.decode(encoding)
                    result = {
                        "file_path": file_path,
                        "encoding": encoding,
                        "content": content_str,
                        "size": len(content)
                    }
                except UnicodeDecodeError:
                    yield self.create_text_message(
                        f"Error: Failed to decode file with {encoding} encoding. Try 'binary' encoding."
                    )
                    return
            
            yield self.create_json_message(result)
            
        except Exception as e:
            yield self.create_text_message(f"Error reading file: {str(e)}")
