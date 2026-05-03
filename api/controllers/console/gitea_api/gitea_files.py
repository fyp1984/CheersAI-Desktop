"""Gitea file retrieval API endpoints."""
import logging
import os
from io import BytesIO

from flask import request, send_file
from flask_login import current_user
from flask_restx import Resource, fields

from controllers.console import console_ns
from controllers.console.wraps import setup_required
from libs.filebay_user_config import resolve_user_filebay_config
from libs.login import login_required
from services.gitea_storage_service import GiteaStorageService

logger = logging.getLogger(__name__)

# Define API models
gitea_file_list_model = console_ns.model('GiteaFileList', {
    'files': fields.List(fields.Raw, description='List of files'),
})

gitea_file_metadata_model = console_ns.model('GiteaFileMetadata', {
    'name': fields.String(description='File name'),
    'path': fields.String(description='File path'),
    'size': fields.Integer(description='File size in bytes'),
    'sha': fields.String(description='File SHA hash'),
    'url': fields.String(description='Download URL'),
    'type': fields.String(description='File type'),
})


def _get_request_user_config(log_prefix: str) -> dict[str, str]:
    user_email = current_user.email if hasattr(current_user, 'email') else None
    if not user_email:
        return {}

    user_config = resolve_user_filebay_config(
        user_email,
        mask_token=False,
        log_prefix=log_prefix,
    )
    return user_config or {}


def _apply_user_config_to_env(user_config: dict[str, str]) -> dict[str, str]:
    original_env = {
        'GITEA_URL': os.getenv('GITEA_URL', ''),
        'GITEA_TOKEN': os.getenv('GITEA_TOKEN', ''),
        'GITEA_OWNER': os.getenv('GITEA_OWNER', ''),
        'GITEA_REPO': os.getenv('GITEA_REPO', ''),
        'GITEA_PATH': os.getenv('GITEA_PATH', ''),
    }

    if user_config.get('gitea_url'):
        os.environ['GITEA_URL'] = user_config['gitea_url']
    if user_config.get('gitea_token'):
        os.environ['GITEA_TOKEN'] = user_config['gitea_token']
    if user_config.get('gitea_owner'):
        os.environ['GITEA_OWNER'] = user_config['gitea_owner']
    if user_config.get('gitea_repo'):
        os.environ['GITEA_REPO'] = user_config['gitea_repo']
    if user_config.get('gitea_path') is not None:
        os.environ['GITEA_PATH'] = user_config['gitea_path']

    return original_env


def _restore_env(original_env: dict[str, str]) -> None:
    for key, value in original_env.items():
        if value:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]


@console_ns.route('/gitea/files/<path:file_path>')
class GiteaFileApi(Resource):
    """Gitea file retrieval API."""

    @setup_required
    @login_required
    def get(self, file_path):
        """
        Download file from Gitea repository.
        
        Args:
            file_path: Path to the file in Gitea repository
            
        Returns:
            File content
        """
        try:
            user_config = _get_request_user_config('[Gitea File Download]')
            original_env = {}
            try:
                original_env = _apply_user_config_to_env(user_config)
                gitea_service = GiteaStorageService()
                file_content = gitea_service.get_file(file_path)
                
                # Get file metadata for proper filename
                try:
                    metadata = gitea_service.get_file_metadata(file_path)
                    filename = metadata.get('name', file_path.split('/')[-1])
                except Exception:
                    filename = file_path.split('/')[-1]
                
                # Return file as download
                return send_file(
                    BytesIO(file_content),
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/octet-stream'
                )
            finally:
                _restore_env(original_env)
        except FileNotFoundError:
            logger.error(f'[Gitea File Download] File not found: {file_path}')
            return {'error': 'File not found in Gitea repository'}, 404
        except Exception as e:
            logger.error(f'[Gitea File Download] Failed to retrieve file: {str(e)}', exc_info=True)
            return {'error': f'Failed to retrieve file: {str(e)}'}, 500


@console_ns.route('/gitea/files/<path:file_path>/metadata')
class GiteaFileMetadataApi(Resource):
    """Gitea file metadata API."""

    @setup_required
    @login_required
    @console_ns.marshal_with(gitea_file_metadata_model)
    def get(self, file_path):
        """
        Get file metadata from Gitea repository.
        
        Args:
            file_path: Path to the file in Gitea repository
            
        Returns:
            File metadata
        """
        try:
            user_config = _get_request_user_config('[Gitea Metadata]')
            original_env = {}
            try:
                original_env = _apply_user_config_to_env(user_config)
                gitea_service = GiteaStorageService()
                metadata = gitea_service.get_file_metadata(file_path)
                return metadata
            finally:
                _restore_env(original_env)
        except FileNotFoundError:
            return {'error': 'File not found in Gitea repository'}, 404
        except Exception as e:
            logger.error(f'[Gitea Metadata] Failed: {str(e)}', exc_info=True)
            return {'error': f'Failed to retrieve metadata: {str(e)}'}, 500


@console_ns.route('/gitea/files')
class GiteaFileListApi(Resource):
    """Gitea file list API."""

    @setup_required
    @login_required
    @console_ns.marshal_with(gitea_file_list_model)
    def get(self):
        """
        List files in Gitea repository.
        
        Query parameters:
            path: Directory path (optional, default: root)
            
        Returns:
            List of files
        """
        directory_path = request.args.get('path', '')
        
        try:
            user_config = _get_request_user_config('[Gitea Files]')
            original_env = {}
            try:
                original_env = _apply_user_config_to_env(user_config)
                logger.info(f'[Gitea Files] Using GITEA_URL: {os.getenv("GITEA_URL")}')
                logger.info(f'[Gitea Files] Using GITEA_OWNER: {os.getenv("GITEA_OWNER")}')
                logger.info(f'[Gitea Files] Using GITEA_REPO: {os.getenv("GITEA_REPO")}')
                
                gitea_service = GiteaStorageService()
                files = gitea_service.list_files(directory_path)
                return {'files': files}
            finally:
                _restore_env(original_env)
        except FileNotFoundError:
            logger.error('[Gitea Files] Directory not found')
            return {'error': 'Directory not found in Gitea repository'}, 404
        except Exception as e:
            logger.error(f'[Gitea Files] Failed to list files: {str(e)}', exc_info=True)
            return {'error': f'Failed to list files: {str(e)}'}, 500


@console_ns.route('/gitea/files/<path:file_path>/url')
class GiteaFileUrlApi(Resource):
    """Gitea file URL API."""

    @setup_required
    @login_required
    def get(self, file_path):
        """
        Get direct download URL for a file in Gitea repository.
        
        Args:
            file_path: Path to the file in Gitea repository
            
        Returns:
            Download URL
        """
        try:
            user_config = _get_request_user_config('[Gitea URL]')
            original_env = {}
            try:
                original_env = _apply_user_config_to_env(user_config)
                gitea_service = GiteaStorageService()
                
                # Check if file exists
                if not gitea_service.file_exists(file_path):
                    return {'error': 'File not found in Gitea repository'}, 404
                
                url = gitea_service.get_file_url(file_path)
                return {
                    'url': url,
                    'path': file_path
                }
            finally:
                _restore_env(original_env)
        except Exception as e:
            logger.error(f'[Gitea URL] Failed: {str(e)}', exc_info=True)
            return {'error': f'Failed to get file URL: {str(e)}'}, 500
