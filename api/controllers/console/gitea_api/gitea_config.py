"""Gitea configuration API endpoints."""
import os

from flask import request
from flask_restx import Resource, fields

from controllers.console import console_ns
from controllers.console.wraps import setup_required
from libs.login import login_required
from services.gitea_storage_service import GiteaStorageService

# Define API models
gitea_config_model = console_ns.model('GiteaConfig', {
    'gitea_url': fields.String(description='Gitea server URL'),
    'gitea_owner': fields.String(description='Repository owner'),
    'gitea_repo': fields.String(description='Repository name'),
    'gitea_path': fields.String(description='Default path in repository'),
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
        Get current Gitea configuration.
        
        Returns:
            Current Gitea configuration (token is masked)
        """
        gitea_url = os.getenv('GITEA_URL', 'http://localhost:3000')
        gitea_token = os.getenv('GITEA_TOKEN', '')
        gitea_owner = os.getenv('GITEA_OWNER', 'cheersai')
        gitea_repo = os.getenv('GITEA_REPO', 'file-storage')
        gitea_path = os.getenv('GITEA_PATH', '')
        
        # Mask the token for security
        masked_token = ''
        if gitea_token:
            masked_token = gitea_token[:4] + '*' * (len(gitea_token) - 8) + gitea_token[-4:] if len(gitea_token) > 8 else '****'
        
        return {
            'gitea_url': gitea_url,
            'gitea_owner': gitea_owner,
            'gitea_repo': gitea_repo,
            'gitea_path': gitea_path,
            'gitea_token': masked_token,
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
        
        # Update environment variables
        if 'gitea_url' in data:
            os.environ['GITEA_URL'] = data['gitea_url']
        if 'gitea_owner' in data:
            os.environ['GITEA_OWNER'] = data['gitea_owner']
        if 'gitea_repo' in data:
            os.environ['GITEA_REPO'] = data['gitea_repo']
        if 'gitea_path' in data:
            os.environ['GITEA_PATH'] = data['gitea_path']
        if data.get('gitea_token'):
            # Only update if a new token is provided (not masked)
            if not data['gitea_token'].startswith('****'):
                os.environ['GITEA_TOKEN'] = data['gitea_token']
        
        # Save to .env file
        try:
            self._update_env_file(data)
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to save to .env file: {str(e)}'
            }, 500
        
        return {
            'success': True,
            'message': 'Gitea configuration saved successfully to .env file'
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
            'GITEA_OWNER': data.get('gitea_owner'),
            'GITEA_REPO': data.get('gitea_repo'),
            'GITEA_PATH': data.get('gitea_path'),
            'GITEA_TOKEN': data.get('gitea_token') if data.get('gitea_token') and not data.get('gitea_token').startswith('****') else None,
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
        gitea_url = data.get('gitea_url') or os.getenv('GITEA_URL', 'http://localhost:3000')
        gitea_token = data.get('gitea_token') or os.getenv('GITEA_TOKEN', '')
        gitea_owner = data.get('gitea_owner') or os.getenv('GITEA_OWNER', 'cheersai')
        gitea_repo = data.get('gitea_repo') or os.getenv('GITEA_REPO', 'file-storage')
        
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
            
            # Try to list files in root directory
            files = gitea_service.list_files('')
            
            return {
                'success': True,
                'message': f'Successfully connected to Gitea! Found {len(files)} items in repository.'
            }
        except FileNotFoundError:
            return {
                'success': True,
                'message': 'Successfully connected to Gitea! Repository is empty or directory not found.'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to connect to Gitea: {str(e)}'
            }
        finally:
            # Restore original env vars
            for key, value in original_env.items():
                if value:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]
