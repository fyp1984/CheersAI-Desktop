"""Inner API for Gitea configuration."""
import json
import logging
import os

from flask import request
from flask_restx import Resource, fields

from controllers.console.wraps import setup_required
from controllers.inner_api import inner_api_ns
from extensions.ext_database import db
from models.account import Account

logger = logging.getLogger(__name__)

gitea_config_model = inner_api_ns.model('InnerGiteaConfig', {
    'gitea_url': fields.String(description='Gitea server URL'),
    'gitea_owner': fields.String(description='Repository owner'),
    'gitea_repo': fields.String(description='Repository name'),
    'gitea_token': fields.String(description='API token'),
})


@inner_api_ns.route('/enterprise/gitea/config')
class EnterpriseGiteaConfigApi(Resource):
    """Gitea config for backend-to-backend use."""

    method_decorators = [setup_required]

    @inner_api_ns.marshal_with(gitea_config_model)
    def get(self):
        """
        Get Gitea configuration for a specific user by email.
        
        Query Parameters:
            email: User email address
            
        Returns:
            User-specific Gitea configuration or default from env vars
        """
        user_email = request.args.get('email')
        
        if user_email:
            logger.info(f'[Enterprise Gitea Config] Getting config for user: {user_email}')
            
            try:
                # Query user from database
                account = db.session.query(Account).filter_by(email=user_email).first()
                
                if account and account.custom_config:
                    try:
                        custom_config = json.loads(account.custom_config)
                        filebay_config = custom_config.get('filebay', {})
                        
                        if filebay_config:
                            logger.info(f'[Enterprise Gitea Config] Found FileBay config in custom_config for {user_email}')
                            
                            gitea_url = filebay_config.get('gitea_url', '')
                            gitea_token = filebay_config.get('gitea_token', '')
                            gitea_owner = filebay_config.get('gitea_owner', 'cheersai')
                            gitea_repo = filebay_config.get('gitea_repo', 'file-storage')
                            
                            # Return unmasked token for backend-to-backend communication
                            return {
                                'gitea_url': gitea_url,
                                'gitea_owner': gitea_owner,
                                'gitea_repo': gitea_repo,
                                'gitea_token': gitea_token,
                            }
                        else:
                            logger.info(f'[Enterprise Gitea Config] No FileBay config found in custom_config for {user_email}')
                    except json.JSONDecodeError as e:
                        logger.warning(f'[Enterprise Gitea Config] Failed to parse custom_config for {user_email}: {e}')
                else:
                    logger.info(f'[Enterprise Gitea Config] No account or custom_config found for {user_email}')
            except Exception as e:
                logger.error(f'[Enterprise Gitea Config] Error querying user config: {e}')
        
        # Fallback to environment variables
        logger.info('[Enterprise Gitea Config] Using default config from environment variables')
        gitea_url = os.getenv('FILEBAY_BASE_URL') or os.getenv('GITEA_URL', '')
        gitea_token = os.getenv('GITEA_TOKEN', '')
        gitea_owner = os.getenv('GITEA_OWNER', 'cheersai')
        gitea_repo = os.getenv('GITEA_REPO', 'file-storage')

        # Return unmasked token for backend-to-backend communication
        return {
            'gitea_url': gitea_url,
            'gitea_owner': gitea_owner,
            'gitea_repo': gitea_repo,
            'gitea_token': gitea_token,
        }
