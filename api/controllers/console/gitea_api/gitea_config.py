"""Gitea configuration API endpoints."""
import logging
import os
from urllib.parse import urlparse

from flask import request
from flask_restx import Resource, fields

from controllers.console import console_ns
from controllers.console.wraps import setup_required
from extensions.ext_database import db
from libs.filebay_user_config import (
    is_masked_gitea_token,
    mask_gitea_token,
    merge_account_filebay_config,
    resolve_user_filebay_config,
)
from libs.login import current_user, login_required
from models.account import Account
from services.gitea_storage_service import GiteaStorageService

logger = logging.getLogger(__name__)

# Define API models
gitea_config_model = console_ns.model('GiteaConfig', {
    'gitea_url': fields.String(description='Gitea server URL'),
    'gitea_owner': fields.String(description='Repository owner'),
    'gitea_repo': fields.String(description='Repository name'),
    'gitea_token': fields.String(description='API token (masked)'),
})

gitea_config_update_model = console_ns.model('GiteaConfigUpdate', {
    'gitea_url': fields.String(description='Gitea server URL'),
    'gitea_owner': fields.String(description='Repository owner'),
    'gitea_repo': fields.String(description='Repository name'),
    'gitea_path': fields.String(description='Default path in repository'),
    'gitea_token': fields.String(description='API token'),
})

gitea_test_result_model = console_ns.model('GiteaTestResult', {
    'success': fields.Boolean(description='Test result'),
    'message': fields.String(description='Result message'),
})


@console_ns.route('/gitea/config')
class GiteaConfigApi(Resource):
    """Gitea configuration API."""

    @setup_required
    @login_required
    @console_ns.marshal_with(gitea_config_model)
    def get(self):
        """
        Get current Gitea configuration for the logged-in user.
        
        Returns:
            Current Gitea configuration (token is masked)
        """
        # Get current user's email
        user_email = current_user.email
        logger.info('[Gitea Config] Getting config for user: %s', user_email)

        account = db.session.query(Account).filter_by(id=current_user.id).first()
        config_data = resolve_user_filebay_config(
            user_email,
            account=account,
            mask_token=True,
            log_prefix='[Gitea Config]',
        )
        if config_data:
            return config_data
        
        # Fallback to environment variables
        gitea_url = os.getenv('FILEBAY_BASE_URL') or os.getenv('GITEA_URL', '')
        gitea_token = os.getenv('GITEA_TOKEN', '')
        gitea_owner = os.getenv('GITEA_OWNER', 'cheersai')
        gitea_repo = os.getenv('GITEA_REPO', 'file-storage')
        
        return {
            'gitea_url': gitea_url,
            'gitea_owner': gitea_owner,
            'gitea_repo': gitea_repo,
            'gitea_token': mask_gitea_token(gitea_token),
        }

    @setup_required
    @login_required
    @console_ns.expect(gitea_config_update_model)
    def post(self):
        """
        Update Gitea configuration and save to .env file.
        
        Returns:
            Success message
        """
        data = request.get_json()
        if not isinstance(data, dict):
            return {
                'success': False,
                'message': '请求参数格式错误',
            }, 400

        gitea_url = (data.get('gitea_url') or '').strip()
        gitea_owner = (data.get('gitea_owner') or '').strip()
        gitea_repo = (data.get('gitea_repo') or '').strip()
        gitea_token = (data.get('gitea_token') or '').strip()

        if not gitea_url:
            return {'success': False, 'message': 'FileBay 服务器地址不能为空'}, 400
        if not gitea_owner:
            return {'success': False, 'message': '仓库所有者不能为空'}, 400
        if not gitea_repo:
            return {'success': False, 'message': '仓库名称不能为空'}, 400

        try:
            parsed = urlparse(gitea_url)
            if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
                raise ValueError()
        except Exception:
            return {'success': False, 'message': 'FileBay 服务器地址格式不正确'}, 400

        data['gitea_url'] = gitea_url
        data['gitea_owner'] = gitea_owner
        data['gitea_repo'] = gitea_repo
        data['gitea_token'] = gitea_token

        account = db.session.query(Account).filter_by(id=current_user.id).first()
        if not account:
            return {'success': False, 'message': '当前用户不存在'}, 404

        account.custom_config_dict = merge_account_filebay_config(account.custom_config_dict, data)

        try:
            self._update_env_file(data)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to save configuration: {str(e)}'
            }, 500

        # Update environment variables after durable persistence succeeds
        os.environ['GITEA_URL'] = data['gitea_url']
        os.environ['FILEBAY_BASE_URL'] = data['gitea_url']
        os.environ['GITEA_OWNER'] = data['gitea_owner']
        os.environ['GITEA_REPO'] = data['gitea_repo']
        if 'gitea_path' in data:
            os.environ['GITEA_PATH'] = data['gitea_path']
        if gitea_token and not is_masked_gitea_token(gitea_token):
            os.environ['GITEA_TOKEN'] = gitea_token
        
        return {
            'success': True,
            'message': 'Gitea configuration saved successfully'
        }
    
    def _update_env_file(self, data):
        """Update .env file with new Gitea configuration."""
        from pathlib import Path
        
        # Find .env file
        env_path = Path(__file__).parent.parent.parent.parent / '.env'
        
        # Read existing .env file
        if env_path.exists():
            with open(env_path, encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Update or add Gitea configuration
        gitea_keys = {
            'GITEA_URL': data.get('gitea_url'),
            'FILEBAY_BASE_URL': data.get('gitea_url'),
            'GITEA_OWNER': data.get('gitea_owner'),
            'GITEA_REPO': data.get('gitea_repo'),
            'GITEA_PATH': data.get('gitea_path'),
            'GITEA_TOKEN': data.get('gitea_token') if data.get('gitea_token') and not is_masked_gitea_token(data.get('gitea_token', '')) else None,
        }
        
        # Remove None values
        gitea_keys = {k: v for k, v in gitea_keys.items() if v is not None}
        
        # Update existing lines or mark for addition
        updated_keys = set()
        new_lines = []
        
        for line in lines:
            updated = False
            for key, value in gitea_keys.items():
                if line.startswith(f'{key}='):
                    new_lines.append(f'{key}={value}\n')
                    updated_keys.add(key)
                    updated = True
                    break
            if not updated:
                new_lines.append(line)
        
        # Add new keys that weren't in the file
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines.append('\n')
        
        # Add Gitea section header if adding new keys
        keys_to_add = set(gitea_keys.keys()) - updated_keys
        if keys_to_add:
            # Check if Gitea section exists
            has_gitea_section = any('Gitea Configuration' in line for line in new_lines)
            if not has_gitea_section:
                new_lines.append('\n# Gitea Configuration\n')
            
            for key in keys_to_add:
                new_lines.append(f'{key}={gitea_keys[key]}\n')
        
        # Write back to .env file
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)


@console_ns.route('/gitea/config/test')
class GiteaConfigTestApi(Resource):
    """Gitea configuration test API."""

    @setup_required
    @login_required
    @console_ns.marshal_with(gitea_test_result_model)
    def post(self):
        """
        Test Gitea connection with current or provided configuration.
        
        Returns:
            Test result
        """
        data = request.get_json() or {}
        
        # Use provided config or current env vars
        gitea_url = data.get('gitea_url') or os.getenv('FILEBAY_BASE_URL') or os.getenv('GITEA_URL', '')
        gitea_token = data.get('gitea_token') or os.getenv('GITEA_TOKEN', '')
        gitea_owner = data.get('gitea_owner') or os.getenv('GITEA_OWNER', 'cheersai')
        gitea_repo = data.get('gitea_repo') or os.getenv('GITEA_REPO', 'file-storage')
        gitea_path = data.get('gitea_path', '').strip()
        
        # Temporarily set env vars for testing
        original_env = {}
        try:
            original_env['GITEA_URL'] = os.getenv('GITEA_URL', '')
            original_env['GITEA_TOKEN'] = os.getenv('GITEA_TOKEN', '')
            original_env['GITEA_OWNER'] = os.getenv('GITEA_OWNER', '')
            original_env['GITEA_REPO'] = os.getenv('GITEA_REPO', '')
            
            os.environ['GITEA_URL'] = gitea_url
            os.environ['GITEA_TOKEN'] = gitea_token
            os.environ['GITEA_OWNER'] = gitea_owner
            os.environ['GITEA_REPO'] = gitea_repo
            
            # Test connection
            gitea_service = GiteaStorageService()
            
            # Try to list files in the configured directory (or root if not specified)
            files = gitea_service.list_files(gitea_path)
            
            path_info = f" in '{gitea_path}'" if gitea_path else " in root directory"
            return {
                'success': True,
                'message': f'Successfully connected to FileBay! Found {len(files)} items{path_info}.'
            }
        except FileNotFoundError:
            path_info = f" '{gitea_path}'" if gitea_path else " root directory"
            return {
                'success': True,
                'message': f'Successfully connected to FileBay! Directory{path_info} is empty or not found (will be created on first upload).'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to connect to FileBay: {str(e)}'
            }
        finally:
            # Restore original env vars
            for key, value in original_env.items():
                if value:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]


@console_ns.route('/gitea/config/download')
class GiteaConfigDownloadApi(Resource):
    """Gitea configuration download API for Desktop App."""

    def options(self):
        """Handle CORS preflight request."""
        return {}, 200

    @setup_required
    @login_required
    def get(self):
        """
        Get complete Gitea configuration for download (including unmasked token).
        This endpoint is specifically for Desktop App configuration download.
        
        Returns:
            Complete Gitea configuration with unmasked token
        """
        # Get current user's email
        user_email = current_user.email
        logger.info('[Gitea Config Download] Getting config for user: %s', user_email)

        account = db.session.query(Account).filter_by(id=current_user.id).first()
        config_data = resolve_user_filebay_config(
            user_email,
            account=account,
            mask_token=False,
            log_prefix='[Gitea Config Download]',
        )
        if config_data:
            return config_data
        
        # Fallback to environment variables
        return {
            'gitea_url': os.getenv('FILEBAY_BASE_URL') or os.getenv('GITEA_URL', ''),
            'gitea_owner': os.getenv('GITEA_OWNER', 'cheersai'),
            'gitea_repo': os.getenv('GITEA_REPO', 'file-storage'),
            'gitea_token': os.getenv('GITEA_TOKEN', ''),  # Unmasked token
        }
