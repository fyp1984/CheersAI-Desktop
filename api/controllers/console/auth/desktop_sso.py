import hashlib
import logging

from flask import request
from flask_restx import Resource, fields

from configs import dify_config
from controllers.console import console_ns
from extensions.ext_database import db
from extensions.ext_redis import redis_client
from libs.datetime_utils import naive_utc_now
from libs.desktop_auth import (
    build_desktop_sso_projection,
    get_sso_subject_owner,
    get_sso_subject_username,
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
from services.sso_account_service import SSOAccountService

logger = logging.getLogger(__name__)
SSO_GROUP_TENANT_CACHE_PREFIX = "desktop:sso:group-tenant:"

desktop_sso_login_model = console_ns.model(
    "DesktopSSOLoginPayload",
    {
        "sub": fields.String(required=True, description="SSO subject"),
        "owner": fields.String(required=False, description="SSO owner/domain"),
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


def _get_sso_group_names(payload: dict) -> list[str]:
    groups = payload.get("groups")
    if not isinstance(groups, list):
        return []

    normalized_groups: list[str] = []
    for group in groups:
        if not isinstance(group, str):
            continue
        normalized_group = group.strip()
        if normalized_group and normalized_group not in normalized_groups:
            normalized_groups.append(normalized_group)

    return normalized_groups


def _get_sso_group_name(payload: dict) -> str | None:
    group_names = _get_sso_group_names(payload)
    return group_names[0] if group_names else None


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


def _get_current_tenant_join(account: Account) -> TenantAccountJoin | None:
    return (
        db.session.query(TenantAccountJoin)
        .join(Tenant, TenantAccountJoin.tenant_id == Tenant.id)
        .filter(
            TenantAccountJoin.account_id == account.id,
            TenantAccountJoin.current.is_(True),
            Tenant.status == TenantStatus.NORMAL,
        )
        .order_by(TenantAccountJoin.updated_at.desc(), TenantAccountJoin.created_at.desc())
        .first()
    )


def _get_fallback_tenant(account: Account) -> Tenant | None:
    tenant_join = _get_preferred_tenant_join(account)
    return db.session.query(Tenant).filter_by(id=tenant_join.tenant_id, status=TenantStatus.NORMAL).first() if tenant_join else None


def _resolve_group_tenant(group_name: str) -> Tenant:
    cache_key = _get_sso_group_tenant_cache_key(group_name)
    cached_tenant_id = redis_client.get(cache_key)
    if isinstance(cached_tenant_id, bytes):
        cached_tenant_id = cached_tenant_id.decode("utf-8")

    tenant = None
    if isinstance(cached_tenant_id, str) and cached_tenant_id:
        tenant = db.session.query(Tenant).filter_by(id=cached_tenant_id, status=TenantStatus.NORMAL).first()
        if tenant and tenant.name != group_name:
            logger.warning(
                "Desktop SSO group cache mismatch for group '%s': cached tenant '%s' (%s), resetting mapping",
                group_name,
                tenant.name,
                tenant.id,
            )
            tenant = None

    if not tenant:
        tenant = db.session.query(Tenant).filter_by(name=group_name, status=TenantStatus.NORMAL).first()

    if not tenant:
        tenant = TenantService.create_tenant(name=group_name, is_setup=True)
        logger.info("Created tenant %s for Desktop SSO group '%s'", tenant.id, group_name)

    redis_client.set(cache_key, tenant.id)
    return tenant


def _resolve_shared_tenant(account: Account, payload: dict) -> Tenant | None:
    group_name = _get_sso_group_name(payload)
    if not group_name:
        return _get_fallback_tenant(account)

    return _resolve_group_tenant(group_name)


def _ensure_tenant_join(account: Account, tenant: Tenant, system_role: str) -> TenantAccountJoin:
    tenant_join = TenantService.create_tenant_member(tenant, account, role=system_role)
    if tenant_join.role != system_role:
        tenant_join.role = system_role
        db.session.commit()
    return tenant_join


def _ensure_desktop_sso_tenant_join(account: Account, system_role: str, payload: dict) -> TenantAccountJoin:
    current_tenant_join = _get_current_tenant_join(account)
    group_names = _get_sso_group_names(payload)
    resolved_group_joins: list[TenantAccountJoin] = []

    # Always rebuild Redis group->tenant mappings from the current SSO payload.
    for group_name in group_names:
        tenant = _resolve_group_tenant(group_name)
        resolved_group_joins.append(_ensure_tenant_join(account, tenant, system_role))

    tenant_join = resolved_group_joins[0] if resolved_group_joins else None
    tenant = db.session.query(Tenant).filter_by(id=tenant_join.tenant_id, status=TenantStatus.NORMAL).first() if tenant_join else None
    if not tenant:
        TenantService.create_owner_tenant_if_not_exist(account, is_setup=True)
        tenant_join = _get_preferred_tenant_join(account)
        if not tenant_join:
            raise Exception("Failed to create tenant membership")
        if tenant_join.role != system_role:
            tenant_join.role = system_role
            db.session.commit()
        if not current_tenant_join or current_tenant_join.tenant_id != tenant_join.tenant_id:
            TenantService.switch_tenant(account, tenant_join.tenant_id)
        return tenant_join

    if not tenant_join:
        tenant_join = _ensure_tenant_join(account, tenant, system_role)
    if not current_tenant_join or current_tenant_join.tenant_id != tenant.id:
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
            sso_owner = get_sso_subject_owner(data) or (dify_config.SSO_PROVISION_OWNER or "CheersAI")
            sso_username = (
                get_sso_subject_username(data)
                or (data.get("preferred_username") or "")
                or name
            ).strip()
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

            custom_config = account.custom_config_dict
            custom_config.update({
                "desktop_sso_subject": subject_id,
                "desktop_sso_owner": sso_owner,
                "desktop_sso_username": sso_username,
                "desktop_sso_preferred_username": (data.get("preferred_username") or "").strip(),
                "desktop_sso_email": normalized_email,
                "desktop_sso_groups": _get_sso_group_names(data),
                "desktop_sso_password_set": bool(custom_config.get("desktop_sso_password_set")),
            })

            sso_tags: list[str] = []
            sso_account_service = SSOAccountService()
            if sso_account_service.is_enabled():
                try:
                    sso_tags = sso_account_service.get_user_tags(account)
                except Exception as tag_error:
                    logger.warning("Failed to sync SSO tags for %s: %s", normalized_email, tag_error)
            custom_config["desktop_sso_tags"] = sso_tags
            account.custom_config_dict = custom_config
            db.session.commit()

            if tenant_join:
                projection = build_desktop_sso_projection(
                    data,
                    workspace_role=tenant_join.role,
                    mapped_role=resolved_sso_role,
                    sso_tags=sso_tags,
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
                    logger.info("SSO login audit logged, log_id: %s", log_id)
                else:
                    logger.error("SSO login write_log returned None!")
            except Exception as e:
                logger.error("Failed to record SSO login audit log: %s", e, exc_info=True)

            logger.info("Desktop SSO Login success for: %s with role: %s", normalized_email, system_role)
            
            # Auto-provision FileBay for the user if not already configured
            try:
                # Refresh account to avoid stale data
                db.session.refresh(account)
                
                custom_config = account.custom_config_dict
                from libs.filebay_user_config import has_complete_filebay_config, sync_account_filebay_config

                if not has_complete_filebay_config(custom_config):
                    logger.info("[SSO Auto Provision] Triggering FileBay auto-provision for %s", normalized_email)
                    from services.filebay_config_service import resolve_filebay_config
                    
                    # Use resolve_filebay_config which handles auto-provision
                    filebay_config = resolve_filebay_config(
                        normalized_email,
                        auto_provision=True,
                        mask_token=False
                    )
                    
                    # Preserve existing Desktop SSO metadata when enriching FileBay settings.
                    resolved_config = {
                        'gitea_url': filebay_config.gitea_url,
                        'gitea_owner': filebay_config.gitea_owner,
                        'gitea_repo': filebay_config.gitea_repo,
                        'gitea_token': filebay_config.gitea_token,
                    }
                    custom_config.update(resolved_config)
                    sync_account_filebay_config(account, custom_config)
                    
                    logger.info("[SSO Auto Provision] FileBay provisioned for %s", normalized_email)
                else:
                    logger.info("[SSO Auto Provision] User %s already has FileBay config", normalized_email)
            except Exception as provision_error:
                # Don't fail login if auto-provision fails
                logger.error("[SSO Auto Provision] Failed for %s: %s", normalized_email, provision_error, exc_info=True)
            
            return response
        except Exception as e:
            logger.error("Desktop SSO login failed: %s", str(e), exc_info=True)
            return {"result": "fail", "message": str(e)}, 500
