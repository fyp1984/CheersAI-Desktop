"""Inner API for Gitea configuration."""
import os

from flask_restx import Resource, fields

from controllers.console.wraps import setup_required
from controllers.inner_api import inner_api_ns

gitea_config_model = inner_api_ns.model('InnerGiteaConfig', {
    'gitea_url': fields.String(description='Gitea server URL'),
    'gitea_owner': fields.String(description='Repository owner'),
    'gitea_repo': fields.String(description='Repository name'),
    'gitea_token': fields.String(description='API token (masked)'),
})


@inner_api_ns.route('/enterprise/gitea/config')
class EnterpriseGiteaConfigApi(Resource):
    """Gitea config for backend-to-backend use."""

    method_decorators = [setup_required]

    @inner_api_ns.marshal_with(gitea_config_model)
    def get(self):
        gitea_url = os.getenv('FILEBAY_BASE_URL') or os.getenv('GITEA_URL', '')
        gitea_token = os.getenv('GITEA_TOKEN', '')
        gitea_owner = os.getenv('GITEA_OWNER', 'cheersai')
        gitea_repo = os.getenv('GITEA_REPO', 'file-storage')

        masked_token = ''
        if gitea_token:
            masked_token = gitea_token[:4] + '*' * (len(gitea_token) - 8) + gitea_token[-4:] if len(gitea_token) > 8 else '****'

        return {
            'gitea_url': gitea_url,
            'gitea_owner': gitea_owner,
            'gitea_repo': gitea_repo,
            'gitea_token': masked_token,
        }
