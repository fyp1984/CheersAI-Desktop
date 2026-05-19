from flask_login import current_user

from configs import dify_config
from extensions.ext_database import db
from libs.desktop_auth import (
    get_account_allowed_workspace_tenant_ids,
    get_account_workspace_capabilities,
    load_desktop_sso_projection,
)
from models.account import Tenant, TenantAccountJoin, TenantAccountRole
from services.account_service import TenantService
from services.feature_service import FeatureService


class WorkspaceService:
    @classmethod
    def get_visible_tenants(cls, account, tenants: list[Tenant]) -> list[Tenant]:
        allowed_tenant_ids = get_account_allowed_workspace_tenant_ids(account)
        if allowed_tenant_ids is None:
            return tenants

        allowed_tenant_id_set = set(allowed_tenant_ids)
        visible_tenants = [tenant for tenant in tenants if tenant.id in allowed_tenant_id_set]
        visible_tenants.sort(key=lambda tenant: allowed_tenant_ids.index(tenant.id) if tenant.id in allowed_tenant_id_set else len(allowed_tenant_ids))
        return visible_tenants

    @classmethod
    def ensure_current_workspace_access(cls, account) -> Tenant | None:
        current_tenant = getattr(account, "current_tenant", None)
        allowed_tenant_ids = get_account_allowed_workspace_tenant_ids(account)
        if allowed_tenant_ids is None:
            return current_tenant

        if current_tenant and current_tenant.id in allowed_tenant_ids:
            return current_tenant

        joined_tenants = cls.get_visible_tenants(account, TenantService.get_join_tenants(account))
        if not joined_tenants:
            return None

        TenantService.switch_tenant(account, joined_tenants[0].id)
        return joined_tenants[0]

    @classmethod
    def get_tenant_info(cls, tenant: Tenant):
        if not tenant:
            return None
        tenant_info: dict[str, object] = {
            "id": tenant.id,
            "name": tenant.name,
            "plan": tenant.plan,
            "status": tenant.status,
            "created_at": tenant.created_at,
            "trial_end_reason": None,
            "role": "normal",
        }

        # Get role of user
        tenant_account_join = (
            db.session.query(TenantAccountJoin)
            .where(TenantAccountJoin.tenant_id == tenant.id, TenantAccountJoin.account_id == current_user.id)
            .first()
        )
        assert tenant_account_join is not None, "TenantAccountJoin not found"
        tenant_info["role"] = tenant_account_join.role
        tenant_info["capabilities"] = get_account_workspace_capabilities(current_user, tenant.id)

        sso_projection = load_desktop_sso_projection(current_user.id, tenant.id)
        if sso_projection:
            projection_capabilities = sso_projection.get("capabilities")
            if isinstance(projection_capabilities, list):
                merged_capabilities = set(tenant_info.get("capabilities") or [])
                merged_capabilities.update(capability for capability in projection_capabilities if isinstance(capability, str))
                tenant_info["capabilities"] = sorted(merged_capabilities)
            tenant_info["sso_mapped_role"] = sso_projection.get("mapped_role")
            tenant_info["sso_sync_hash"] = sso_projection.get("sync_hash")

        feature = FeatureService.get_features(tenant.id)
        can_replace_logo = feature.can_replace_logo

        if can_replace_logo and TenantService.has_roles(tenant, [TenantAccountRole.OWNER, TenantAccountRole.ADMIN]):
            base_url = dify_config.FILES_URL
            replace_webapp_logo = (
                f"{base_url}/files/workspaces/{tenant.id}/webapp-logo"
                if tenant.custom_config_dict.get("replace_webapp_logo")
                else None
            )
            remove_webapp_brand = tenant.custom_config_dict.get("remove_webapp_brand", False)

            tenant_info["custom_config"] = {
                "remove_webapp_brand": remove_webapp_brand,
                "replace_webapp_logo": replace_webapp_logo,
            }
        if dify_config.EDITION == "CLOUD":
            tenant_info["next_credit_reset_date"] = feature.next_credit_reset_date

            from services.credit_pool_service import CreditPoolService

            paid_pool = CreditPoolService.get_pool(tenant_id=tenant.id, pool_type="paid")
            if paid_pool:
                tenant_info["trial_credits"] = paid_pool.quota_limit
                tenant_info["trial_credits_used"] = paid_pool.quota_used
            else:
                trial_pool = CreditPoolService.get_pool(tenant_id=tenant.id, pool_type="trial")
                if trial_pool:
                    tenant_info["trial_credits"] = trial_pool.quota_limit
                    tenant_info["trial_credits_used"] = trial_pool.quota_used

        return tenant_info
