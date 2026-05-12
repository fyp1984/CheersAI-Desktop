"""Read file from FileBay repository"""

import base64
import http.client
import json
import ssl
import urllib.parse
from collections.abc import Generator
from typing import Any

from core.tools.builtin_tool.tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage


class NoSNIHTTPSClient:
    """HTTPS client without SNI for FileBay compatibility"""
    
    def __init__(self, base_url: str, token: str = "", timeout: int = 30):
        parsed = urllib.parse.urlparse(base_url)
        self.scheme = parsed.scheme
        self.host = parsed.netloc
        self.token = token
        self.timeout = timeout
        
        # Create SSL context without SNI
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def _make_request(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        """Make HTTP request"""
        try:
            if self.scheme == "https":
                conn = http.client.HTTPSConnection(
                    self.host,
                    timeout=self.timeout,
                    context=self.ssl_context
                )
            else:
                conn = http.client.HTTPConnection(self.host, timeout=self.timeout)
            
            headers = {
                "Host": self.host,
                "User-Agent": "Dify-FileBay-Tool/1.0",
                "Accept": "application/json",
                "Connection": "close"
            }
            
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            
            if body is not None:
                body_json = json.dumps(body)
                headers["Content-Type"] = "application/json"
                headers["Content-Length"] = str(len(body_json))
                conn.request(method, path, body=body_json, headers=headers)
            else:
                conn.request(method, path, headers=headers)
            
            response = conn.getresponse()
            status_code = response.status
            response_data = response.read()
            conn.close()
            
            try:
                response_json = json.loads(response_data.decode('utf-8'))
            except Exception:
                response_json = {"raw": response_data.decode('utf-8', errors='ignore')}
            
            return status_code, response_json
            
        except Exception as e:
            return 0, {"error": str(e)}
    
    def get(self, path: str) -> tuple[int, dict]:
        """GET request"""
        return self._make_request("GET", path)
    
    def post(self, path: str, body: dict) -> tuple[int, dict]:
        """POST request"""
        return self._make_request("POST", path, body)
    
    def put(self, path: str, body: dict) -> tuple[int, dict]:
        """PUT request"""
        return self._make_request("PUT", path, body)


class ReadFileTool(BuiltinTool):
    """Tool for reading files from FileBay repository"""
    
    def _invoke(
        self,
        user_id: str,
        tool_parameters: dict[str, Any],
        conversation_id: str | None = None,
        app_id: str | None = None,
        message_id: str | None = None,
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Read a file from FileBay repository
        
        Args:
            user_id: The user ID
            tool_parameters: Tool parameters containing:
                - file_path: Path to the file to read
        """
        # Get parameters
        file_path = tool_parameters.get('file_path', '').strip()
        
        if not file_path:
            yield self.create_text_message("Error: file_path is required")
            return
        
        # Remove leading slash if present
        file_path = file_path.lstrip('/')
        
        # Get credentials
        filebay_url = self.runtime.credentials.get('filebay_url', '').rstrip('/')
        filebay_token = self.runtime.credentials.get('filebay_token', '')
        filebay_owner = self.runtime.credentials.get('filebay_owner', '')
        filebay_repo = self.runtime.credentials.get('filebay_repo', '')
        filebay_branch = self.runtime.credentials.get('filebay_branch', 'main')
        
        if not all([filebay_url, filebay_token, filebay_owner, filebay_repo]):
            yield self.create_text_message("Error: Missing required FileBay credentials")
            return
        
        try:
            # Create client
            client = NoSNIHTTPSClient(filebay_url, filebay_token)
            
            # Get file content
            api_path = f"/api/v1/repos/{filebay_owner}/{filebay_repo}/contents/{file_path}"
            params = f"?ref={filebay_branch}"
            
            status_code, response = client.get(api_path + params)
            
            if status_code == 200:
                # Decode base64 content
                content_base64 = response.get('content', '')
                if content_base64:
                    try:
                        content = base64.b64decode(content_base64).decode('utf-8')
                        
                        # Return file content
                        result = {
                            "file_path": file_path,
                            "content": content,
                            "size": response.get('size', 0),
                            "sha": response.get('sha', ''),
                            "branch": filebay_branch
                        }
                        yield self.create_json_message(result)
                    except Exception as e:
                        yield self.create_text_message(f"Error decoding file content: {str(e)}")
                else:
                    yield self.create_text_message("Error: File content is empty")
            elif status_code == 404:
                yield self.create_text_message(f"Error: File not found: {file_path}")
            else:
                error_msg = response.get('message', 'Unknown error')
                yield self.create_text_message(f"Error reading file (HTTP {status_code}): {error_msg}")
                
        except Exception as e:
            yield self.create_text_message(f"Error: {str(e)}")
