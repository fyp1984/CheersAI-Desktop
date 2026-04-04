import logging
import requests
from flask import request
from flask_restx import Resource, fields
from controllers.console import console_ns
from libs.helper import extract_remote_ip
from services.account_service import AccountService, TenantService
from models import Account, AccountStatus
from extensions.ext_database import db
from libs.datetime_utils import naive_utc_now
from configs import dify_config

logger = logging.getLogger(__name__)

sso_token_exchange_model = console_ns.model('SSOTokenExchange', {
    'code': fields.String(required=True, description='Authorization code from SSO'),
    'state': fields.String(required=True, description='State parameter for CSRF protection'),
    'redirectUri': fields.String(required=True, description='Redirect URI used in authorization')
})

@console_ns.route('/auth/sso/token')
class SSOTokenExchangeApi(Resource):
    @console_ns.expect(sso_token_exchange_model)
    def post(self):
        """Exchange SSO authorization code for tokens and login user."""
        try:
            logger.info("SSO token exchange request received")
            data = request.get_json()
            
            code = data.get('code')
            state = data.get('state')
            redirect_uri = data.get('redirectUri')
            
            if not code or not state or not redirect_uri:
                logger.error("Missing required parameters")
                return {'result': 'fail', 'message': 'Missing required parameters'}, 400
            
            logger.info(f"Exchanging code with SSO server, state: {state}")
            
            # Get SSO configuration from environment
            sso_api_url = dify_config.SSO_API_URL
            client_id = dify_config.DESKTOP_SSO_CLIENT_ID
            client_secret = dify_config.DESKTOP_SSO_CLIENT_SECRET
            
            if not sso_api_url or not client_id or not client_secret:
                logger.error("SSO configuration missing")
                return {'result': 'fail', 'message': 'SSO not configured'}, 500
            
            # Exchange code for access token with SSO server
            token_url = f"{sso_api_url}/oauth2/token"
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'client_id': client_id,
                'client_secret': client_secret,
            }
            
            logger.info(f"Calling SSO token endpoint: {token_url}")
            token_response = requests.post(token_url, data=token_data, timeout=10)
            
            if token_response.status_code != 200:
                logger.error(f"SSO token exchange failed: {token_response.status_code} - {token_response.text}")
                return {'result': 'fail', 'message': 'Failed to exchange token with SSO'}, 400
            
            token_result = token_response.json()
            access_token = token_result.get('access_token')
            
            if not access_token:
                logger.error("No access token in SSO response")
                return {'result': 'fail', 'message': 'Invalid SSO response'}, 400
            
            # Get user info from SSO server
            userinfo_url = f"{sso_api_url}/oauth2/userinfo"
            headers = {'Authorization': f'Bearer {access_token}'}
            
            logger.info(f"Fetching user info from: {userinfo_url}")
            userinfo_response = requests.get(userinfo_url, headers=headers, timeout=10)
            
            if userinfo_response.status_code != 200:
                logger.error(f"Failed to get user info: {userinfo_response.status_code}")
                return {'result': 'fail', 'message': 'Failed to get user info from SSO'}, 400
            
            user_info = userinfo_response.json()
            email = user_info.get('email')
            name = user_info.get('name', 'Dify User')
            
            if not email:
                logger.error("No email in user info")
                return {'result': 'fail', 'message': 'Email not provided by SSO'}, 400
            
            normalized_email = email.lower()
            logger.info(f"SSO user authenticated: {normalized_email}")
            
            # Get or create account
            account = AccountService.get_user_through_email(normalized_email)
            
            if not account:
                logger.info(f"Creating new account for SSO user: {normalized_email}")
                account = AccountService.create_account(
                    email=normalized_email,
                    name=name,
                    interface_language='en-US',
                    password=None,
                    is_setup=True,
                )
                TenantService.create_owner_tenant_if_not_exist(account, is_setup=True)
                account.status = AccountStatus.ACTIVE
                account.initialized_at = naive_utc_now()
                db.session.commit()
            else:
                logger.info(f"Found existing account: {normalized_email}")
                if account.status == AccountStatus.BANNED:
                    return {'result': 'fail', 'message': 'Account is banned'}, 403
                
                if account.status == AccountStatus.PENDING:
                    account.status = AccountStatus.ACTIVE
                    account.initialized_at = naive_utc_now()
                    db.session.commit()
            
            # Generate Dify tokens
            logger.info(f"Generating Dify tokens for: {normalized_email}")
            token_pair = AccountService.login(
                account=account,
                ip_address=extract_remote_ip(request),
            )
            
            import flask
            response = flask.make_response({
                'result': 'success',
                'access_token': token_pair.access_token,
                'refresh_token': token_pair.refresh_token
            })
            
            # Set cookies
            logger.info(f"Setting authentication cookies for: {normalized_email}")
            
            response.set_cookie(
                'access_token',
                value=token_pair.access_token,
                httponly=False,
                domain=None,
                secure=False,
                samesite='Lax',
                max_age=int(60 * 60 * 24),
                path="/",
            )
            
            response.set_cookie(
                'refresh_token',
                value=token_pair.refresh_token,
                httponly=False,
                domain=None,
                secure=False,
                samesite='Lax',
                max_age=int(60 * 60 * 24 * 30),
                path="/",
            )
            
            response.set_cookie(
                'csrf_token',
                value=token_pair.csrf_token,
                httponly=False,
                domain=None,
                secure=False,
                samesite='Lax',
                max_age=int(60 * 60 * 24),
                path="/",
            )
            
            logger.info(f"SSO login successful for: {normalized_email}")
            return response
            
        except requests.RequestException as e:
            logger.error(f"SSO API request failed: {str(e)}", exc_info=True)
            return {'result': 'fail', 'message': 'Failed to communicate with SSO server'}, 500
        except Exception as e:
            logger.error(f"SSO token exchange failed: {str(e)}", exc_info=True)
            return {'result': 'fail', 'message': str(e)}, 500
