"""Gitea file retrieval API endpoints."""
from io import BytesIO

from flask import send_file
from flask_restx import Resource, fields

from controllers.console import console_ns
from controllers.console.wraps import setup_required
from extensions.ext_database import db
from libs.login import login_required
from services.gitea_storage_service import GiteaStorageService

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
        from flask_login import current_user
        from models.account import Account
        import os
        import requests
        from configs import dify_config
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            user_email = current_user.email if hasattr(current_user, 'email') else None
            user_config = {}
            is_enterprise = False
            
            # Try enterprise API first
            if user_email:
                try:
                    # Use local API endpoint instead of external tunnel
                    enterprise_api_url = 'http://localhost:5001/inner/api/enterprise/gitea/config'
                    
                    logger.info(f'[Gitea File Download] Calling enterprise API for {user_email}')
                    
                    response = requests.get(
                        enterprise_api_url,
                        params={'email': user_email},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('gitea_url') and data.get('gitea_token'):
                            user_config = {
                                'gitea_url': data.get('gitea_url'),
                                'gitea_owner': data.get('gitea_owner'),
                                'gitea_repo': data.get('gitea_repo'),
                                'gitea_path': data.get('gitea_path', ''),
                                'gitea_token': data.get('gitea_token'),
                            }
                            is_enterprise = True
                            logger.info('[Gitea File Download] Using enterprise config')
                except Exception as e:
                    logger.warning(f'[Gitea File Download] Enterprise API failed: {str(e)}')
            
            # Fall back to user's database config if no enterprise config
            if not is_enterprise:
                logger.info('[Gitea File Download] Falling back to user database config')
                account = db.session.query(Account).filter_by(id=current_user.id).first()
                if account:
                    user_config = account.custom_config_dict
            
            # Temporarily set env vars for GiteaStorageService
            original_env = {}
            try:
                original_env['GITEA_URL'] = os.getenv('GITEA_URL', '')
                original_env['GITEA_TOKEN'] = os.getenv('GITEA_TOKEN', '')
                original_env['GITEA_OWNER'] = os.getenv('GITEA_OWNER', '')
                original_env['GITEA_REPO'] = os.getenv('GITEA_REPO', '')
                original_env['GITEA_PATH'] = os.getenv('GITEA_PATH', '')
                
                # Use config (enterprise or user) or fall back to env vars
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
                # Restore original env vars
                for key, value in original_env.items():
                    if value:
                        os.environ[key] = value
                    elif key in os.environ:
                        del os.environ[key]
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
        from flask_login import current_user
        from models.account import Account
        import os
        import requests
        from configs import dify_config
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            user_email = current_user.email if hasattr(current_user, 'email') else None
            user_config = {}
            is_enterprise = False
            
            # Try enterprise API first
            if user_email:
                try:
                    # Use local API endpoint instead of external tunnel
                    enterprise_api_url = 'http://localhost:5001/inner/api/enterprise/gitea/config'
                    
                    response = requests.get(
                        enterprise_api_url,
                        params={'email': user_email},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('gitea_url') and data.get('gitea_token'):
                            user_config = {
                                'gitea_url': data.get('gitea_url'),
                                'gitea_owner': data.get('gitea_owner'),
                                'gitea_repo': data.get('gitea_repo'),
                                'gitea_path': data.get('gitea_path', ''),
                                'gitea_token': data.get('gitea_token'),
                            }
                            is_enterprise = True
                except Exception as e:
                    logger.warning(f'[Gitea Metadata] Enterprise API failed: {str(e)}')
            
            # Fall back to user's database config if no enterprise config
            if not is_enterprise:
                account = db.session.query(Account).filter_by(id=current_user.id).first()
                if account:
                    user_config = account.custom_config_dict
            
            # Temporarily set env vars for GiteaStorageService
            original_env = {}
            try:
                original_env['GITEA_URL'] = os.getenv('GITEA_URL', '')
                original_env['GITEA_TOKEN'] = os.getenv('GITEA_TOKEN', '')
                original_env['GITEA_OWNER'] = os.getenv('GITEA_OWNER', '')
                original_env['GITEA_REPO'] = os.getenv('GITEA_REPO', '')
                original_env['GITEA_PATH'] = os.getenv('GITEA_PATH', '')
                
                # Use config (enterprise or user) or fall back to env vars
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
                
                gitea_service = GiteaStorageService()
                metadata = gitea_service.get_file_metadata(file_path)
                return metadata
            finally:
                # Restore original env vars
                for key, value in original_env.items():
                    if value:
                        os.environ[key] = value
                    elif key in os.environ:
                        del os.environ[key]
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
        from flask import request
        from flask_login import current_user
        from models.account import Account
        import os
        import requests
        from configs import dify_config
        import logging
        
        logger = logging.getLogger(__name__)
        directory_path = request.args.get('path', '')
        
        try:
            user_email = current_user.email if hasattr(current_user, 'email') else None
            user_config = {}
            is_enterprise = False
            
            # Try enterprise API first
            if user_email:
                try:
                    # Use local API endpoint instead of external tunnel
                    enterprise_api_url = 'http://localhost:5001/inner/api/enterprise/gitea/config'
                    
                    logger.info(f'[Gitea Files] Calling enterprise API: {enterprise_api_url}?email={user_email}')
                    
                    response = requests.get(
                        enterprise_api_url,
                        params={'email': user_email},
                        timeout=10
                    )
                    
                    logger.info(f'[Gitea Files] Enterprise API response: {response.status_code}')
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f'[Gitea Files] Enterprise config data: {data}')
                        
                        # Check if we got valid config data
                        if data.get('gitea_url') and data.get('gitea_token'):
                            user_config = {
                                'gitea_url': data.get('gitea_url'),
                                'gitea_owner': data.get('gitea_owner'),
                                'gitea_repo': data.get('gitea_repo'),
                                'gitea_path': data.get('gitea_path', ''),
                                'gitea_token': data.get('gitea_token'),
                            }
                            is_enterprise = True
                            logger.info('[Gitea Files] Using enterprise config')
                        else:
                            logger.warning('[Gitea Files] Enterprise API returned incomplete config')
                except Exception as e:
                    logger.warning(f'[Gitea Files] Enterprise API failed: {str(e)}')
            
            # Fall back to user's database config if no enterprise config
            if not is_enterprise:
                logger.info('[Gitea Files] Falling back to user database config')
                account = db.session.query(Account).filter_by(id=current_user.id).first()
                if account:
                    user_config = account.custom_config_dict
                    logger.info(f'[Gitea Files] User config: {user_config}')
            
            # Temporarily set env vars for GiteaStorageService
            original_env = {}
            try:
                original_env['GITEA_URL'] = os.getenv('GITEA_URL', '')
                original_env['GITEA_TOKEN'] = os.getenv('GITEA_TOKEN', '')
                original_env['GITEA_OWNER'] = os.getenv('GITEA_OWNER', '')
                original_env['GITEA_REPO'] = os.getenv('GITEA_REPO', '')
                original_env['GITEA_PATH'] = os.getenv('GITEA_PATH', '')
                
                # Use config (enterprise or user) or fall back to env vars
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
                
                logger.info(f'[Gitea Files] Using GITEA_URL: {os.getenv("GITEA_URL")}')
                logger.info(f'[Gitea Files] Using GITEA_OWNER: {os.getenv("GITEA_OWNER")}')
                logger.info(f'[Gitea Files] Using GITEA_REPO: {os.getenv("GITEA_REPO")}')
                
                gitea_service = GiteaStorageService()
                files = gitea_service.list_files(directory_path)
                return {'files': files}
            finally:
                # Restore original env vars
                for key, value in original_env.items():
                    if value:
                        os.environ[key] = value
                    elif key in os.environ:
                        del os.environ[key]
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
        from flask_login import current_user
        from models.account import Account
        import os
        import requests
        from configs import dify_config
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            user_email = current_user.email if hasattr(current_user, 'email') else None
            user_config = {}
            is_enterprise = False
            
            # Try enterprise API first
            if user_email:
                try:
                    # Use local API endpoint instead of external tunnel
                    enterprise_api_url = 'http://localhost:5001/inner/api/enterprise/gitea/config'
                    
                    response = requests.get(
                        enterprise_api_url,
                        params={'email': user_email},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('gitea_url') and data.get('gitea_token'):
                            user_config = {
                                'gitea_url': data.get('gitea_url'),
                                'gitea_owner': data.get('gitea_owner'),
                                'gitea_repo': data.get('gitea_repo'),
                                'gitea_path': data.get('gitea_path', ''),
                                'gitea_token': data.get('gitea_token'),
                            }
                            is_enterprise = True
                except Exception as e:
                    logger.warning(f'[Gitea URL] Enterprise API failed: {str(e)}')
            
            # Fall back to user's database config if no enterprise config
            if not is_enterprise:
                account = db.session.query(Account).filter_by(id=current_user.id).first()
                if account:
                    user_config = account.custom_config_dict
            
            # Temporarily set env vars for GiteaStorageService
            original_env = {}
            try:
                original_env['GITEA_URL'] = os.getenv('GITEA_URL', '')
                original_env['GITEA_TOKEN'] = os.getenv('GITEA_TOKEN', '')
                original_env['GITEA_OWNER'] = os.getenv('GITEA_OWNER', '')
                original_env['GITEA_REPO'] = os.getenv('GITEA_REPO', '')
                original_env['GITEA_PATH'] = os.getenv('GITEA_PATH', '')
                
                # Use config (enterprise or user) or fall back to env vars
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
                # Restore original env vars
                for key, value in original_env.items():
                    if value:
                        os.environ[key] = value
                    elif key in os.environ:
                        del os.environ[key]
        except Exception as e:
            logger.error(f'[Gitea URL] Failed: {str(e)}', exc_info=True)
            return {'error': f'Failed to get file URL: {str(e)}'}, 500

