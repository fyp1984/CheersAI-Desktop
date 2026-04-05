import logging

import requests
from flask import request
from flask_restx import Resource, fields

from configs import dify_config
from controllers.console import console_ns
from extensions.ext_database import db
from libs.datetime_utils import naive_utc_now
from libs.helper import extract_remote_ip
from models import AccountStatus
from models.account import TenantAccountJoin
from services.account_service import AccountService, TenantService

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
            
            logger.info("Exchanging code with SSO server, state: %s", state)
            
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
            
            logger.info("Calling SSO token endpoint: %s", token_url)
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
            
            logger.info("Fetching user info from: %s", userinfo_url)
            userinfo_response = requests.get(userinfo_url, headers=headers, timeout=10)
            
            if userinfo_response.status_code != 200:
                logger.error(f"Failed to get user info: {userinfo_response.status_code}")
                return {'result': 'fail', 'message': 'Failed to get user info from SSO'}, 400
            
            user_info = userinfo_response.json()
            email = user_info.get('email')
            name = user_info.get('name', 'Dify User')
            
            # 提取角色信息
            sso_role_raw = user_info.get('type') or user_info.get('role') or 'user'
            sso_role = sso_role_raw.lower().strip() if sso_role_raw else 'user'
            
            # 映射 Casdoor 角色到系统角色
            if sso_role in ['admin', 'owner']:
                system_role = 'owner'
            elif sso_role in ['technician', 'editor']:
                system_role = 'editor'
            else:
                system_role = 'normal'
            
            logger.info("SSO role mapping: %s -> %s", sso_role_raw, system_role)
            
            if not email:
                logger.error("No email in user info")
                return {'result': 'fail', 'message': 'Email not provided by SSO'}, 400
            
            normalized_email = email.lower()
            logger.info("SSO user authenticated: %s", normalized_email)
            
            # Get or create account
            account = AccountService.get_user_through_email(normalized_email)
            
            if not account:
                logger.info("Creating new account for SSO user: %s", normalized_email)
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
                
                # 为新用户设置工作空间角色
                logger.info("Setting workspace role for new user: %s", system_role)
                tenant_join = db.session.query(TenantAccountJoin).filter_by(account_id=account.id).first()
                if tenant_join:
                    tenant_join.role = system_role
                    db.session.commit()
            else:
                logger.info("Found existing account: %s", normalized_email)
                if account.status == AccountStatus.BANNED:
                    return {'result': 'fail', 'message': 'Account is banned'}, 403
                
                if account.status == AccountStatus.PENDING:
                    account.status = AccountStatus.ACTIVE
                    account.initialized_at = naive_utc_now()
                
                # 更新现有用户的工作空间角色
                logger.info("Updating workspace role for existing user: %s", system_role)
                tenant_join = db.session.query(TenantAccountJoin).filter_by(account_id=account.id).first()
                if tenant_join:
                    # 如果不是唯一的owner，才更新角色
                    if tenant_join.role == 'owner':
                        owner_count = db.session.query(TenantAccountJoin).filter_by(
                            tenant_id=tenant_join.tenant_id, 
                            role='owner'
                        ).count()
                        if owner_count > 1:
                            tenant_join.role = system_role
                    else:
                        tenant_join.role = system_role
                
                db.session.commit()
            
            # Generate Dify tokens
            logger.info("Generating Dify tokens for: %s", normalized_email)
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
            logger.info("Setting authentication cookies for: %s", normalized_email)
            
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
            
            logger.info("SSO login successful for: %s", normalized_email)
            return response
            
        except requests.RequestException as e:
            logger.error(f"SSO API request failed: {str(e)}", exc_info=True)
            return {'result': 'fail', 'message': 'Failed to communicate with SSO server'}, 500
        except Exception as e:
            logger.error(f"SSO token exchange failed: {str(e)}", exc_info=True)
            return {'result': 'fail', 'message': str(e)}, 500
