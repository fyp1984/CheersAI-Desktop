"""FileBay file retrieval API endpoints."""
import base64
import http.client
import json
import logging
import ssl
import urllib.parse
from io import BytesIO

from flask import request, send_file
from flask_login import current_user
from flask_restx import Resource, fields

from controllers.console import console_ns
from controllers.console.wraps import setup_required
from libs.filebay_user_config import resolve_user_filebay_config
from libs.login import login_required

logger = logging.getLogger(__name__)

# Define API models
filebay_file_list_model = console_ns.model('FileBayFileList', {
    'directory': fields.String(description='Current directory path'),
    'branch': fields.String(description='Branch name'),
    'directories': fields.List(fields.Raw, description='List of directories'),
    'files': fields.List(fields.Raw, description='List of files'),
    'total_directories': fields.Integer(description='Total number of directories'),
    'total_files': fields.Integer(description='Total number of files'),
})

filebay_file_content_model = console_ns.model('FileBayFileContent', {
    'file_path': fields.String(description='File path'),
    'content': fields.String(description='File content'),
    'size': fields.Integer(description='File size in bytes'),
    'sha': fields.String(description='File SHA hash'),
    'branch': fields.String(description='Branch name'),
})


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
    
    def _make_request(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict | list]:
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
                "User-Agent": "Dify-FileBay-API/1.0",
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
            logger.error(f"[FileBay API] Request failed: {str(e)}", exc_info=True)
            return 0, {"error": str(e)}
    
    def get(self, path: str) -> tuple[int, dict | list]:
        """GET request"""
        return self._make_request("GET", path)


def _get_user_filebay_config() -> dict[str, str]:
    """Get FileBay configuration for current user"""
    user_email = current_user.email if hasattr(current_user, 'email') else None
    if not user_email:
        return {}

    user_config = resolve_user_filebay_config(
        user_email,
        mask_token=False,
        log_prefix='[FileBay API]',
    )
    return user_config or {}


@console_ns.route('/filebay/list-files')
class FileBayListFilesApi(Resource):
    """FileBay file list API."""

    @setup_required
    @login_required
    @console_ns.marshal_with(filebay_file_list_model)
    def get(self):
        """
        List files in FileBay repository.
        
        Query parameters:
            path: Directory path (optional, default: root)
            
        Returns:
            List of files and directories
        """
        directory_path = request.args.get('path', '').strip().strip('/')
        
        logger.info('[FileBay API] ===== LIST FILES REQUEST =====')
        logger.info(f'[FileBay API] Path: {directory_path or "/"}')
        logger.info(f'[FileBay API] User: {current_user.email if hasattr(current_user, "email") else "Unknown"}')
        
        try:
            logger.info(f'[FileBay API] List files request - path: {directory_path or "/"}')
            
            # Get user FileBay config
            user_config = _get_user_filebay_config()
            
            filebay_url = user_config.get('gitea_url', '').rstrip('/')
            filebay_token = user_config.get('gitea_token', '')
            filebay_owner = user_config.get('gitea_owner', '')
            filebay_repo = user_config.get('gitea_repo', '')
            filebay_branch = user_config.get('gitea_branch', 'main')
            
            logger.info('[FileBay API] Config - url: %s, owner: %s, repo: %s, branch: %s', filebay_url, filebay_owner, filebay_repo, filebay_branch)
            
            if not all([filebay_url, filebay_token, filebay_owner, filebay_repo]):
                logger.error('[FileBay API] Missing required FileBay credentials')
                return {'error': 'Missing required FileBay credentials'}, 400
            
            logger.info(f'[FileBay API] Listing files in path: {directory_path or "/"}')
            
            # Create client
            client = NoSNIHTTPSClient(filebay_url, filebay_token)
            
            # Build API path
            if directory_path:
                api_path = f"/api/v1/repos/{filebay_owner}/{filebay_repo}/contents/{directory_path}"
            else:
                api_path = f"/api/v1/repos/{filebay_owner}/{filebay_repo}/contents"
            
            params = f"?ref={filebay_branch}"
            
            status_code, response = client.get(api_path + params)
            
            if status_code == 200:
                # Response should be a list of files/directories
                if isinstance(response, list):
                    files = []
                    directories = []
                    
                    for item in response:
                        item_info = {
                            "name": item.get('name', ''),
                            "path": item.get('path', ''),
                            "type": item.get('type', ''),
                            "size": item.get('size', 0),
                            "sha": item.get('sha', '')
                        }
                        
                        if item.get('type') == 'dir':
                            directories.append(item_info)
                        else:
                            files.append(item_info)
                    
                    result = {
                        "directory": directory_path or "/",
                        "branch": filebay_branch,
                        "directories": directories,
                        "files": files,
                        "total_directories": len(directories),
                        "total_files": len(files)
                    }
                    logger.info(f'[FileBay API] Found {len(directories)} directories and {len(files)} files')
                    return result
                else:
                    # Single file response
                    result = {
                        "directory": directory_path or "/",
                        "branch": filebay_branch,
                        "directories": [],
                        "files": [{
                            "name": response.get('name', ''),
                            "path": response.get('path', ''),
                            "type": response.get('type', ''),
                            "size": response.get('size', 0),
                            "sha": response.get('sha', '')
                        }],
                        "total_directories": 0,
                        "total_files": 1
                    }
                    return result
            elif status_code == 404:
                logger.error(f'[FileBay API] Directory not found: {directory_path or "/"}')
                return {'error': f'Directory not found: {directory_path or "/"}'}, 404
            else:
                error_msg = response.get('message', 'Unknown error') if isinstance(response, dict) else 'Unknown error'
                logger.error('[FileBay API] Error listing files (HTTP %s): %s', status_code, error_msg)
                return {'error': f'Error listing files: {error_msg}'}, 500
                
        except Exception as e:
            logger.error(f'[FileBay API] Failed to list files: {str(e)}', exc_info=True)
            return {'error': f'Failed to list files: {str(e)}'}, 500


@console_ns.route('/filebay/read-file')
class FileBayReadFileApi(Resource):
    """FileBay file read API."""

    @setup_required
    @login_required
    @console_ns.marshal_with(filebay_file_content_model)
    def post(self):
        """
        Read file content from FileBay repository.
        
        Request body:
            file_path: Path to the file
            
        Returns:
            File content and metadata
        """
        data = request.get_json()
        file_path = data.get('file_path', '').strip().lstrip('/')
        
        if not file_path:
            return {'error': 'file_path is required'}, 400
        
        try:
            # Get user FileBay config
            user_config = _get_user_filebay_config()
            
            filebay_url = user_config.get('gitea_url', '').rstrip('/')
            filebay_token = user_config.get('gitea_token', '')
            filebay_owner = user_config.get('gitea_owner', '')
            filebay_repo = user_config.get('gitea_repo', '')
            filebay_branch = user_config.get('gitea_branch', 'main')
            
            if not all([filebay_url, filebay_token, filebay_owner, filebay_repo]):
                logger.error('[FileBay API] Missing required FileBay credentials')
                return {'error': 'Missing required FileBay credentials'}, 400
            
            logger.info('[FileBay API] Reading file: %s', file_path)
            
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
                        
                        result = {
                            "file_path": file_path,
                            "content": content,
                            "size": response.get('size', 0),
                            "sha": response.get('sha', ''),
                            "branch": filebay_branch
                        }
                        logger.info(f'[FileBay API] Successfully read file: {file_path} ({result["size"]} bytes)')
                        return result
                    except Exception as e:
                        logger.error(f'[FileBay API] Error decoding file content: {str(e)}')
                        return {'error': f'Error decoding file content: {str(e)}'}, 500
                else:
                    logger.error('[FileBay API] File content is empty')
                    return {'error': 'File content is empty'}, 500
            elif status_code == 404:
                logger.error('[FileBay API] File not found: %s', file_path)
                return {'error': f'File not found: {file_path}'}, 404
            else:
                error_msg = response.get('message', 'Unknown error') if isinstance(response, dict) else 'Unknown error'
                logger.error('[FileBay API] Error reading file (HTTP %s): %s', status_code, error_msg)
                return {'error': f'Error reading file: {error_msg}'}, 500
                
        except Exception as e:
            logger.error(f'[FileBay API] Failed to read file: {str(e)}', exc_info=True)
            return {'error': f'Failed to read file: {str(e)}'}, 500


@console_ns.route('/filebay/download-file')
class FileBayDownloadFileApi(Resource):
    """FileBay file download API."""

    @setup_required
    @login_required
    def get(self):
        """
        Download file from FileBay repository.
        
        Query parameters:
            path: Path to the file
            
        Returns:
            File content as download
        """
        file_path = request.args.get('path', '').strip().lstrip('/')
        
        if not file_path:
            return {'error': 'path parameter is required'}, 400
        
        try:
            # Get user FileBay config
            user_config = _get_user_filebay_config()
            
            filebay_url = user_config.get('gitea_url', '').rstrip('/')
            filebay_token = user_config.get('gitea_token', '')
            filebay_owner = user_config.get('gitea_owner', '')
            filebay_repo = user_config.get('gitea_repo', '')
            filebay_branch = user_config.get('gitea_branch', 'main')
            
            if not all([filebay_url, filebay_token, filebay_owner, filebay_repo]):
                logger.error('[FileBay API] Missing required FileBay credentials')
                return {'error': 'Missing required FileBay credentials'}, 400
            
            logger.info('[FileBay API] Downloading file: %s', file_path)
            
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
                        content = base64.b64decode(content_base64)
                        filename = response.get('name', file_path.split('/')[-1])
                        
                        # Return file as download
                        return send_file(
                            BytesIO(content),
                            as_attachment=True,
                            download_name=filename,
                            mimetype='application/octet-stream'
                        )
                    except Exception as e:
                        logger.error(f'[FileBay API] Error decoding file content: {str(e)}')
                        return {'error': f'Error decoding file content: {str(e)}'}, 500
                else:
                    logger.error('[FileBay API] File content is empty')
                    return {'error': 'File content is empty'}, 500
            elif status_code == 404:
                logger.error('[FileBay API] File not found: %s', file_path)
                return {'error': f'File not found: {file_path}'}, 404
            else:
                error_msg = response.get('message', 'Unknown error') if isinstance(response, dict) else 'Unknown error'
                logger.error('[FileBay API] Error downloading file (HTTP %s): %s', status_code, error_msg)
                return {'error': f'Error downloading file: {error_msg}'}, 500
                
        except Exception as e:
            logger.error(f'[FileBay API] Failed to download file: {str(e)}', exc_info=True)
            return {'error': f'Failed to download file: {str(e)}'}, 500


@console_ns.route('/filebay/upload-file')
class FileBayUploadFileApi(Resource):
    """FileBay file upload API - downloads from FileBay and uploads to Dify storage."""

    @setup_required
    @login_required
    def post(self):
        """
        Upload file from FileBay repository to Dify storage.
        
        Request body:
            file_path: Path to the file in FileBay
            
        Returns:
            Uploaded file information
        """
        import services
        from core.file import helpers as file_helpers
        from extensions.ext_database import db
        from services.file_service import FileService
        
        data = request.get_json()
        file_path = data.get('file_path', '').strip().lstrip('/')
        
        if not file_path:
            return {'error': 'file_path is required'}, 400
        
        try:
            # Get user FileBay config
            user_config = _get_user_filebay_config()
            
            filebay_url = user_config.get('gitea_url', '').rstrip('/')
            filebay_token = user_config.get('gitea_token', '')
            filebay_owner = user_config.get('gitea_owner', '')
            filebay_repo = user_config.get('gitea_repo', '')
            filebay_branch = user_config.get('gitea_branch', 'main')
            
            if not all([filebay_url, filebay_token, filebay_owner, filebay_repo]):
                logger.error('[FileBay API] Missing required FileBay credentials')
                return {'error': 'Missing required FileBay credentials'}, 400
            
            logger.info('[FileBay API] Uploading file: %s', file_path)
            
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
                        content = base64.b64decode(content_base64)
                        filename = response.get('name', file_path.split('/')[-1])
                        file_size = response.get('size', 0)
                        
                        # Guess file info
                        extension = filename.split('.')[-1] if '.' in filename else ''
                        mimetype = 'application/octet-stream'
                        
                        # Try to guess mimetype from extension
                        import mimetypes
                        guessed_type = mimetypes.guess_type(filename)[0]
                        if guessed_type:
                            mimetype = guessed_type
                        
                        # Check file size limit
                        if not FileService.is_file_size_within_limit(extension=extension, file_size=file_size):
                            return {'error': 'File size exceeds limit'}, 413
                        
                        # Upload file to Dify storage
                        try:
                            upload_file = FileService(db.engine).upload_file(
                                filename=filename,
                                content=content,
                                mimetype=mimetype,
                                user=current_user,
                                source_url=f"{filebay_url}/{filebay_owner}/{filebay_repo}/src/branch/{filebay_branch}/{file_path}",
                            )
                        except services.errors.file.FileTooLargeError as file_too_large_error:
                            return {'error': str(file_too_large_error)}, 413
                        except services.errors.file.UnsupportedFileTypeError:
                            return {'error': 'Unsupported file type'}, 400
                        
                        result = {
                            'id': upload_file.id,
                            'name': upload_file.name,
                            'size': upload_file.size,
                            'extension': upload_file.extension,
                            'mime_type': upload_file.mime_type,
                            'url': file_helpers.get_signed_file_url(upload_file_id=upload_file.id),
                            'created_by': upload_file.created_by,
                            'created_at': int(upload_file.created_at.timestamp()),
                        }
                        logger.info(f'[FileBay API] Successfully uploaded file: {filename} (ID: {upload_file.id})')
                        return result
                    except Exception as e:
                        logger.error(f'[FileBay API] Error processing file: {str(e)}', exc_info=True)
                        return {'error': f'Error processing file: {str(e)}'}, 500
                else:
                    logger.error('[FileBay API] File content is empty')
                    return {'error': 'File content is empty'}, 500
            elif status_code == 404:
                logger.error('[FileBay API] File not found: %s', file_path)
                return {'error': f'File not found: {file_path}'}, 404
            else:
                error_msg = response.get('message', 'Unknown error') if isinstance(response, dict) else 'Unknown error'
                logger.error('[FileBay API] Error downloading file (HTTP %s): %s', status_code, error_msg)
                return {'error': f'Error downloading file: {error_msg}'}, 500
                
        except Exception as e:
            logger.error(f'[FileBay API] Failed to upload file: {str(e)}', exc_info=True)
            return {'error': f'Failed to upload file: {str(e)}'}, 500
