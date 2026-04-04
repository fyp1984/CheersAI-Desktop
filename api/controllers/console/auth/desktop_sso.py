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
    'name': fields.String(required=False, description='User name from SSO'),
    'role': fields.String(required=False, description='User role from SSO (admin/technician/user)')
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
            sso_role = data.get('role') if data else None

            if not email:
                logger.error("Email is missing from request")
                return {'result': 'fail', 'message': 'Email is required'}, 400

            normalized_email = email.lower()
            logger.info(f"Processing SSO login for: {normalized_email}, role: {sso_role}")
            logger.info(f"DEBUG: Email contains 'tech': {'tech' in normalized_email}, contains 'technician': {'technician' in normalized_email}")
            
            # Map SSO role to system role
            SSO_ROLE_MAPPING = {
                'admin': 'admin',
                'owner': 'owner',
                'technician': 'editor',
                'editor': 'editor',
                'user': 'normal',
                'normal': 'normal',
            }
            
            # 测试模式：根据邮箱或用户名自动分配角色（方便测试）
            # 生产环境请删除此段代码或设置环境变量控制
            if not sso_role or sso_role == 'user':
                normalized_name = name.lower() if name else ''
                if 'admin' in normalized_email or 'admin' in normalized_name:
                    sso_role = 'admin'
                    logger.info(f"Test mode: Auto-assigned admin role based on email/name")
                elif 'tech' in normalized_email or 'tech' in normalized_name:
                    sso_role = 'technician'
                    logger.info(f"Test mode: Auto-assigned technician role based on email/name")
                else:
                    sso_role = 'user'
                    logger.info(f"Test mode: Using default user role")
            
            system_role = SSO_ROLE_MAPPING.get(sso_role.lower() if sso_role else None, 'normal')
            logger.info(f"Mapped SSO role '{sso_role}' to system role '{system_role}'")
            
            # 1. Get or create account
            account = AccountService.get_user_through_email(normalized_email)
            
            if not account:
                # Handle auto-registration - bypass normal registration checks for SSO
                logger.info(f"Creating new account for SSO user: {normalized_email} with role: {system_role}")
                
                # Create account directly using is_setup=True to bypass registration checks
                account = AccountService.create_account(
                    email=normalized_email,
                    name=name,
                    interface_language='en-US',
                    password=None,
                    is_setup=True,  # Bypass registration restrictions for SSO
                )
                
                # Ensure workspace exists
                TenantService.create_owner_tenant_if_not_exist(account, is_setup=True)
                
                # Update the role in TenantAccountJoin based on SSO role
                from models.account import TenantAccountJoin
                tenant_join = db.session.query(TenantAccountJoin).filter_by(
                    account_id=account.id
                ).first()
                if tenant_join:
                    tenant_join.role = system_role
                    db.session.commit()
                    logger.info(f"Set workspace role to '{system_role}' for new user")
                
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
                
                # Load tenant information for existing user
                from models.account import TenantAccountJoin
                tenant_join = db.session.query(TenantAccountJoin).filter_by(
                    account_id=account.id
                ).first()
                
                logger.info(f"DEBUG: Found tenant_join for existing user: {tenant_join is not None}")
                if tenant_join:
                    logger.info(f"DEBUG: Tenant ID: {tenant_join.tenant_id}, Current role: {tenant_join.role}")
                
                # Update role for existing user
                if tenant_join:
                    old_role = tenant_join.role
                    logger.info(f"DEBUG: Attempting to update role from '{old_role}' to '{system_role}'")
                    
                    # 测试模式：允许降级唯一owner（生产环境请删除此段代码）
                    TEST_MODE_ALLOW_OWNER_DOWNGRADE = True
                    
                    # Don't downgrade owner unless there are multiple owners (or in test mode)
                    if old_role == 'owner' and not TEST_MODE_ALLOW_OWNER_DOWNGRADE:
                        owner_count = db.session.query(TenantAccountJoin).filter_by(
                            tenant_id=tenant_join.tenant_id,
                            role='owner'
                        ).count()
                        if owner_count > 1:
                            tenant_join.role = system_role
                            db.session.commit()
                            logger.info(f"Updated role from 'owner' to '{system_role}' (multiple owners exist)")
                        else:
                            logger.info(f"Keeping 'owner' role (only owner in workspace)")
                    elif old_role != system_role:
                        tenant_join.role = system_role
                        db.session.commit()
                        logger.info(f"Updated role from '{old_role}' to '{system_role}'")

            # 2. Login and issue Dify tokens
            logger.info(f"Generating tokens for: {normalized_email}")
            token_pair = AccountService.login(
                account=account,
                ip_address=extract_remote_ip(request),
            )
            
            logger.info(f"DEBUG: Token pair generated - access_token length: {len(token_pair.access_token)}, refresh_token length: {len(token_pair.refresh_token)}, csrf_token length: {len(token_pair.csrf_token)}")

            # 3. Set cookies using standard Dify cookie functions
            logger.info(f"Setting cookies for: {normalized_email}")
            
            from flask import make_response
            response = make_response({'result': 'success'})
            
            # Use standard Dify cookie functions to ensure proper cookie format
            set_access_token_to_cookie(request, response, token_pair.access_token)
            set_refresh_token_to_cookie(request, response, token_pair.refresh_token)
            set_csrf_token_to_cookie(request, response, token_pair.csrf_token)
            
            logger.info(f"DEBUG: Cookies set in response headers")

            logger.info(f"Desktop SSO Login success for: {normalized_email} with role: {system_role}")
            return response
        except Exception as e:
            logger.error(f"Desktop SSO login failed: {str(e)}", exc_info=True)
            return {'result': 'fail', 'message': str(e)}, 500
