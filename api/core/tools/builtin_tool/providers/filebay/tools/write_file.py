"""Write file to FileBay repository"""

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


class WriteFileTool(BuiltinTool):
    """Tool for writing files to FileBay repository"""
    
    def _invoke(
        self,
        user_id: str,
        tool_parameters: dict[str, Any],
        conversation_id: str | None = None,
        app_id: str | None = None,
        message_id: str | None = None,
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Write a file to FileBay repository
        
        Args:
            user_id: The user ID
            tool_parameters: Tool parameters containing:
                - file_path: Path where the file will be saved
                - content: Content to write to the file
                - commit_message: Commit message (optional)
        """
        # Get parameters
        file_path = tool_parameters.get('file_path', '').strip()
        content = tool_parameters.get('content', '')
        commit_message = tool_parameters.get('commit_message', 'Update file via Dify').strip()
        
        if not file_path:
            yield self.create_text_message("Error: file_path is required")
            return
        
        if not content:
            yield self.create_text_message("Error: content is required")
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
            
            # Encode content to base64
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = content
            content_base64 = base64.b64encode(content_bytes).decode('utf-8')
            
            # Check if file exists to get SHA (required for updates)
            api_path = f"/api/v1/repos/{filebay_owner}/{filebay_repo}/contents/{file_path}"
            status_code, response = client.get(api_path)
            
            file_sha = None
            if status_code == 200:
                file_sha = response.get('sha')
            
            # Prepare request body
            body = {
                "message": commit_message,
                "content": content_base64,
                "branch": filebay_branch
            }
            
            if file_sha:
                body["sha"] = file_sha
            
            # Create or update file
            status_code, response = client.put(api_path, body)
            
            if status_code in [200, 201]:
                result = {
                    "file_path": file_path,
                    "action": "updated" if file_sha else "created",
                    "commit_message": commit_message,
                    "branch": filebay_branch,
                    "size": len(content_bytes),
                    "sha": response.get('content', {}).get('sha', '')
                }
                yield self.create_json_message(result)
            else:
                error_msg = response.get('message', 'Unknown error')
                yield self.create_text_message(f"Error writing file (HTTP {status_code}): {error_msg}")
                
        except Exception as e:
            yield self.create_text_message(f"Error: {str(e)}")
