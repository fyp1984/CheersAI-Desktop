import logging
from flask import request
from flask_restx import Resource, fields
from controllers.console import console_ns
from libs.helper import extract_remote_ip
from libs.token import (
    set_access_token_to_cookie,
    set_csrf_token_to_cookie,
    set_refresh_token_to_cookie,
)
from services.account_service import AccountService, RegisterService, TenantService
from models import Account, AccountStatus
from extensions.ext_database import db
from libs.datetime_utils import naive_utc_now
from controllers.console.wraps import setup_required

logger = logging.getLogger(__name__)

class DesktopSSOLoginPayload(fields.Raw):
    def format(self, value):
        return value

desktop_sso_login_model = console_ns.model('DesktopSSOLoginPayload', {
    'email': fields.String(required=True, description='User email from SSO'),
    'name': fields.String(required=False, description='User name from SSO')
})

@console_ns.route('/auth/desktop-sso/login')
class DesktopSSOLoginApi(Resource):
    @console_ns.expect(desktop_sso_login_model)
    def post(self):
        """Authenticate user from Desktop SSO email."""
        try:
            logger.info("Desktop SSO login request received")
            data = request.get_json()
            logger.info(f"Request data: {data}")
            
            email = data.get('email') if data else None
            name = data.get('name') if data else 'Dify User'

            if not email:
                logger.error("Email is missing from request")
                return {'result': 'fail', 'message': 'Email is required'}, 400

            normalized_email = email.lower()
            logger.info(f"Processing SSO login for: {normalized_email}")
            
            # 1. Get or create account
            account = AccountService.get_user_through_email(normalized_email)
            
            if not account:
                # Handle auto-registration - bypass normal registration checks for SSO
                logger.info(f"Creating new account for SSO user: {normalized_email}")
                
                # Create account directly using is_setup=True to bypass registration checks
                account = AccountService.create_account(
                    email=normalized_email,
                    name=name,
                    interface_language='en-US',
                    password=None,
                    is_setup=True,  # Bypass registration restrictions for SSO
                )
                
                # Ensure workspace exists - also bypass restrictions
                TenantService.create_owner_tenant_if_not_exist(account, is_setup=True)
                
                # Set to active
                account.status = AccountStatus.ACTIVE
                account.initialized_at = naive_utc_now()
                db.session.commit()
            else:
                logger.info(f"Found existing account for: {normalized_email}")
                if account.status == AccountStatus.BANNED:
                    return {'result': 'fail', 'message': 'Account is banned'}, 403
                
                if account.status == AccountStatus.PENDING:
                    account.status = AccountStatus.ACTIVE
                    account.initialized_at = naive_utc_now()
                    db.session.commit()

            # 2. Login and issue Dify tokens
            logger.info(f"Generating tokens for: {normalized_email}")
            token_pair = AccountService.login(
                account=account,
                ip_address=extract_remote_ip(request),
            )

            import flask
            response = flask.make_response({'result': 'success'})

            # 3. Set cookies with relaxed settings for local development
            logger.info(f"Setting cookies for: {normalized_email}")
            
            # For local development, use None for SameSite to allow cross-origin
            response.set_cookie(
                'access_token',
                value=token_pair.access_token,
                httponly=False,  # Allow JavaScript access for debugging
                domain=None,  # Let browser decide
                secure=False,  # Allow HTTP
                samesite='None' if request.is_secure else 'Lax',  # None for HTTPS, Lax for HTTP
                max_age=int(60 * 60 * 24),  # 24 hours
                path="/",
            )
            
            response.set_cookie(
                'refresh_token',
                value=token_pair.refresh_token,
                httponly=False,
                domain=None,
                secure=False,
                samesite='None' if request.is_secure else 'Lax',
                max_age=int(60 * 60 * 24 * 30),  # 30 days
                path="/",
            )
            
            response.set_cookie(
                'csrf_token',
                value=token_pair.csrf_token,
                httponly=False,
                domain=None,
                secure=False,
                samesite='None' if request.is_secure else 'Lax',
                max_age=int(60 * 60 * 24),
                path="/",
            )

            logger.info(f"Desktop SSO Login success for: {normalized_email}")
            return response
        except Exception as e:
            logger.error(f"Desktop SSO login failed: {str(e)}", exc_info=True)
            return {'result': 'fail', 'message': str(e)}, 500
