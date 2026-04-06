import logging

from flask import request
from flask_restx import Resource, fields

from controllers.console import console_ns
from extensions.ext_database import db
from libs.datetime_utils import naive_utc_now
from libs.desktop_auth import has_desktop_access, resolve_workspace_role
from libs.helper import extract_remote_ip
from libs.token import (
    set_access_token_to_cookie,
    set_csrf_token_to_cookie,
    set_refresh_token_to_cookie,
)
from models import AccountStatus
from services.account_service import AccountService, TenantService

logger = logging.getLogger(__name__)

desktop_sso_login_model = console_ns.model('DesktopSSOLoginPayload', {
    'sub': fields.String(required=True, description='SSO subject'),
    'preferred_username': fields.String(required=False, description='SSO username'),
    'email': fields.String(required=True, description='User email from SSO'),
    'name': fields.String(required=False, description='User name from SSO'),
    'role': fields.String(required=False, description='Legacy SSO role field'),
    'type': fields.String(required=False, description='Legacy SSO type field'),
    'roles': fields.List(fields.String, required=False, description='SSO roles'),
    'permissions': fields.List(fields.String, required=False, description='SSO permissions'),
    'groups': fields.List(fields.String, required=False, description='SSO groups'),
    'iss': fields.String(required=False, description='SSO issuer'),
    'aud': fields.String(required=False, description='SSO client id'),
})


@console_ns.route('/auth/desktop-sso/login')
class DesktopSSOLoginApi(Resource):
    @console_ns.expect(desktop_sso_login_model)
    def post(self):
        """Authenticate user from Desktop SSO email."""
        try:
            logger.info("Desktop SSO login request received")
            data = request.get_json() or {}
            logger.info("Request data: %s", data)

            subject_id = data.get('sub')
            email = data.get('email')
            name = data.get('name') or data.get('preferred_username') or 'Dify User'

            if not subject_id:
                logger.error("SSO subject is missing from request")
                return {'result': 'fail', 'message': 'SSO subject is required'}, 400

            if not email:
                logger.error("Email is missing from request")
                return {'result': 'fail', 'message': 'Email is required'}, 400

            if not has_desktop_access(data):
                logger.warning("Desktop access denied for subject %s", subject_id)
                return {'result': 'fail', 'message': 'Desktop access denied'}, 403

            normalized_email = email.lower()
            resolved_sso_role, system_role = resolve_workspace_role(data)
            logger.info(
                "Resolved Desktop SSO subject %s with identifier '%s' to workspace role '%s'",
                subject_id,
                resolved_sso_role,
                system_role,
            )

            account = AccountService.get_user_through_email(normalized_email)

            if not account:
                logger.info("Creating new account for SSO user: %s with role: %s", normalized_email, system_role)

                account = AccountService.create_account(
                    email=normalized_email,
                    name=name,
                    interface_language='en-US',
                    password=None,
                    is_setup=True,
                )

                TenantService.create_owner_tenant_if_not_exist(account, is_setup=True)

                from models.account import TenantAccountJoin
                tenant_join = db.session.query(TenantAccountJoin).filter_by(
                    account_id=account.id
                ).first()
                if tenant_join:
                    tenant_join.role = system_role
                    db.session.commit()
                    logger.info("Set workspace role to '%s' for new user", system_role)

                account.status = AccountStatus.ACTIVE
                account.initialized_at = naive_utc_now()
                db.session.commit()
            else:
                logger.info("Found existing account for: %s", normalized_email)
                if account.status == AccountStatus.BANNED:
                    return {'result': 'fail', 'message': 'Account is banned'}, 403

                if account.status == AccountStatus.PENDING:
                    account.status = AccountStatus.ACTIVE
                    account.initialized_at = naive_utc_now()
                    db.session.commit()

                from models.account import TenantAccountJoin
                tenant_join = db.session.query(TenantAccountJoin).filter_by(
                    account_id=account.id
                ).first()

                if tenant_join:
                    old_role = tenant_join.role
                    logger.info("Attempting to update role from '%s' to '%s'", old_role, system_role)

                    if old_role == 'owner':
                        owner_count = db.session.query(TenantAccountJoin).filter_by(
                            tenant_id=tenant_join.tenant_id,
                            role='owner'
                        ).count()
                        if owner_count > 1:
                            tenant_join.role = system_role
                            db.session.commit()
                            logger.info("Updated role from 'owner' to '%s' (multiple owners exist)", system_role)
                        else:
                            logger.info("Keeping 'owner' role (only owner in workspace)")
                    elif old_role != system_role:
                        tenant_join.role = system_role
                        db.session.commit()
                        logger.info("Updated role from '%s' to '%s'", old_role, system_role)

            logger.info("Generating tokens for: %s", normalized_email)
            token_pair = AccountService.login(
                account=account,
                ip_address=extract_remote_ip(request),
            )
            logger.info("Setting cookies for: %s", normalized_email)

            from flask import make_response
            response = make_response({'result': 'success'})

            set_access_token_to_cookie(request, response, token_pair.access_token)
            set_refresh_token_to_cookie(request, response, token_pair.refresh_token)
            set_csrf_token_to_cookie(request, response, token_pair.csrf_token)

            logger.info("Desktop SSO Login success for: %s with role: %s", normalized_email, system_role)
            return response
        except Exception as e:
            logger.error("Desktop SSO login failed: %s", str(e), exc_info=True)
            return {'result': 'fail', 'message': str(e)}, 500
