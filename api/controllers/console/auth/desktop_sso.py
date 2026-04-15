import hashlib
import logging

from flask import request
from flask_restx import Resource, fields

from controllers.console import console_ns
from extensions.ext_database import db
from extensions.ext_redis import redis_client
from libs.datetime_utils import naive_utc_now
from libs.desktop_auth import (
    build_desktop_sso_projection,
    has_desktop_access,
    resolve_workspace_role,
    save_desktop_sso_projection,
)
from libs.helper import extract_remote_ip
from libs.token import (
    set_access_token_to_cookie,
    set_csrf_token_to_cookie,
    set_refresh_token_to_cookie,
)
from models import AccountStatus
from models.account import Account, Tenant, TenantAccountJoin, TenantStatus
from services.account_service import AccountService, TenantService

logger = logging.getLogger(__name__)
SSO_GROUP_TENANT_CACHE_PREFIX = "desktop:sso:group-tenant:"

desktop_sso_login_model = console_ns.model(
    "DesktopSSOLoginPayload",
    {
        "sub": fields.String(required=True, description="SSO subject"),
        "preferred_username": fields.String(required=False, description="SSO username"),
        "email": fields.String(required=True, description="User email from SSO"),
        "name": fields.String(required=False, description="User name from SSO"),
        "role": fields.String(required=False, description="Legacy SSO role field"),
        "type": fields.String(required=False, description="Legacy SSO type field"),
        "roles": fields.List(fields.String, required=False, description="SSO roles"),
        "permissions": fields.List(fields.String, required=False, description="SSO permissions"),
        "groups": fields.List(fields.String, required=False, description="SSO groups"),
        "iss": fields.String(required=False, description="SSO issuer"),
        "aud": fields.String(required=False, description="SSO client id"),
    },
)


def _get_sso_group_name(payload: dict) -> str | None:
    groups = payload.get("groups")
    if not isinstance(groups, list):
        return None

    for group in groups:
        if not isinstance(group, str):
            continue
        normalized_group = group.strip()
        if normalized_group:
            return normalized_group

    return None


def _get_sso_group_tenant_cache_key(group_name: str) -> str:
    group_hash = hashlib.sha256(group_name.strip().lower().encode("utf-8")).hexdigest()
    return f"{SSO_GROUP_TENANT_CACHE_PREFIX}{group_hash}"


def _get_preferred_tenant_join(account: Account) -> TenantAccountJoin | None:
    return (
        db.session.query(TenantAccountJoin)
        .join(Tenant, TenantAccountJoin.tenant_id == Tenant.id)
        .filter(TenantAccountJoin.account_id == account.id, Tenant.status == TenantStatus.NORMAL)
        .order_by(TenantAccountJoin.current.desc(), TenantAccountJoin.id.asc())
        .first()
    )


def _resolve_shared_tenant(account: Account, payload: dict) -> Tenant | None:
    group_name = _get_sso_group_name(payload)
    if not group_name:
        tenant_join = _get_preferred_tenant_join(account)
        return (
            db.session.query(Tenant).filter_by(id=tenant_join.tenant_id, status=TenantStatus.NORMAL).first()
            if tenant_join
            else None
        )

    cache_key = _get_sso_group_tenant_cache_key(group_name)
    cached_tenant_id = redis_client.get(cache_key)
    if isinstance(cached_tenant_id, bytes):
        cached_tenant_id = cached_tenant_id.decode("utf-8")

    tenant = None
    if isinstance(cached_tenant_id, str) and cached_tenant_id:
        tenant = db.session.query(Tenant).filter_by(id=cached_tenant_id, status=TenantStatus.NORMAL).first()

    if not tenant:
        tenant_join = _get_preferred_tenant_join(account)
        tenant = (
            db.session.query(Tenant).filter_by(id=tenant_join.tenant_id, status=TenantStatus.NORMAL).first()
            if tenant_join
            else None
        )

    if not tenant:
        tenant = TenantService.create_tenant(name=group_name, is_setup=True)

    redis_client.set(cache_key, tenant.id)
    return tenant


def _ensure_desktop_sso_tenant_join(account: Account, system_role: str, payload: dict) -> TenantAccountJoin:
    tenant = _resolve_shared_tenant(account, payload)
    if not tenant:
        TenantService.create_owner_tenant_if_not_exist(account, is_setup=True)
        tenant_join = _get_preferred_tenant_join(account)
        if not tenant_join:
            raise Exception("Failed to create tenant membership")
        if tenant_join.role != system_role:
            tenant_join.role = system_role
            db.session.commit()
        TenantService.switch_tenant(account, tenant_join.tenant_id)
        return tenant_join

    tenant_join = TenantService.create_tenant_member(tenant, account, role=system_role)
    TenantService.switch_tenant(account, tenant.id)
    return tenant_join


@console_ns.route("/auth/desktop-sso/login")
class DesktopSSOLoginApi(Resource):
    @console_ns.expect(desktop_sso_login_model)
    def post(self):
        """Authenticate user from Desktop SSO email."""
        try:
            logger.info("Desktop SSO login request received")
            data = request.get_json() or {}
            logger.info("Request data: %s", data)

            subject_id = data.get("sub")
            email = data.get("email")
            name = data.get("name") or data.get("preferred_username") or "Dify User"

            if not subject_id:
                logger.error("SSO subject is missing from request")
                return {"result": "fail", "message": "SSO subject is required"}, 400

            if not email:
                logger.error("Email is missing from request")
                return {"result": "fail", "message": "Email is required"}, 400

            if not has_desktop_access(data):
                logger.warning("Desktop access denied for subject %s", subject_id)
                return {"result": "fail", "message": "Desktop access denied"}, 403

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
                    interface_language="en-US",
                    password=None,
                    is_setup=True,
                )

                TenantService.create_owner_tenant_if_not_exist(account, is_setup=True)

                from models.account import TenantAccountJoin

                tenant_join = (
                    db.session.query(TenantAccountJoin)
                    .filter_by(account_id=account.id, current=True)
                    .order_by(TenantAccountJoin.updated_at.desc(), TenantAccountJoin.created_at.desc())
                    .first()
                ) or (
                    db.session.query(TenantAccountJoin)
                    .filter_by(account_id=account.id)
                    .order_by(
                        TenantAccountJoin.current.desc(),
                        TenantAccountJoin.updated_at.desc(),
                        TenantAccountJoin.created_at.desc(),
                    )
                    .first()
                )
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
                    return {"result": "fail", "message": "Account is banned"}, 403

                if account.status == AccountStatus.PENDING:
                    account.status = AccountStatus.ACTIVE
                    account.initialized_at = naive_utc_now()
                    db.session.commit()

                from models.account import TenantAccountJoin

                tenant_join = (
                    db.session.query(TenantAccountJoin)
                    .filter_by(account_id=account.id, current=True)
                    .order_by(TenantAccountJoin.updated_at.desc(), TenantAccountJoin.created_at.desc())
                    .first()
                ) or (
                    db.session.query(TenantAccountJoin)
                    .filter_by(account_id=account.id)
                    .order_by(
                        TenantAccountJoin.current.desc(),
                        TenantAccountJoin.updated_at.desc(),
                        TenantAccountJoin.created_at.desc(),
                    )
                    .first()
                )

                if tenant_join:
                    old_role = tenant_join.role
                    logger.info("Attempting to update role from '%s' to '%s'", old_role, system_role)

                    if old_role == "owner":
                        owner_count = (
                            db.session.query(TenantAccountJoin)
                            .filter_by(tenant_id=tenant_join.tenant_id, role="owner")
                            .count()
                        )
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
            tenant_join = _ensure_desktop_sso_tenant_join(account, system_role, data)
            logger.info("Using tenant %s with workspace role '%s'", tenant_join.tenant_id, tenant_join.role)

            if tenant_join:
                projection = build_desktop_sso_projection(
                    data,
                    workspace_role=tenant_join.role,
                    mapped_role=resolved_sso_role,
                )
                save_desktop_sso_projection(account.id, tenant_join.tenant_id, projection)

            logger.info("Generating tokens for: %s", normalized_email)
            token_pair = AccountService.login(
                account=account,
                ip_address=extract_remote_ip(request),
            )
            logger.info("Setting cookies for: %s", normalized_email)

            from flask import make_response

            response = make_response({"result": "success"})

            set_access_token_to_cookie(request, response, token_pair.access_token)
            set_refresh_token_to_cookie(request, response, token_pair.refresh_token)
            set_csrf_token_to_cookie(request, response, token_pair.csrf_token)

            # 记录 Desktop SSO 登录审计日志
            try:
                from services.audit_service import write_log

                log_id = write_log(
                    tenant_id=str(tenant_join.tenant_id),
                    account_id=str(account.id),
                    account_name=account.name,
                    action="login",
                    operation_type="chat",
                    content={"login_method": "desktop_sso"},
                    created_ip=extract_remote_ip(request),
                )
                if log_id:
                    logger.info(f"SSO login audit logged, log_id: {log_id}")
                else:
                    logger.error("SSO login write_log returned None!")
            except Exception as e:
                logger.error(f"Failed to record SSO login audit log: {e}", exc_info=True)

            logger.info("Desktop SSO Login success for: %s with role: %s", normalized_email, system_role)
            return response
        except Exception as e:
            logger.error("Desktop SSO login failed: %s", str(e), exc_info=True)
            return {"result": "fail", "message": str(e)}, 500
