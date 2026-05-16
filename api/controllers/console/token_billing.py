import csv
import io

from flask import Response
from pydantic import BaseModel, Field

from controllers.console.wraps import account_initialization_required, setup_required
from controllers.fastopenapi import console_router
from libs.desktop_auth import (
    DESKTOP_TOKEN_BILLING_EXPORT_CAPABILITY,
    DESKTOP_TOKEN_BILLING_GLOBAL_VIEW_CAPABILITY,
    has_any_workspace_capability,
)
from libs.login import current_account_with_tenant, login_required
from services.model_usage_record_service import ModelUsageRecordService

TEAM_TOKEN_BILLING_CAPABILITIES = (
    "desktop_settings_team",
    "desktop_model_manage",
    "desktop_model_provider_manage",
)


class TokenBillingUsageQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Number of recent records to return")
    scope: str = Field(default="workspace", description="workspace, self or system")


class TokenBillingSummary(BaseModel):
    total_tokens: int = Field(description="Total tokens consumed")
    total_cost: str = Field(description="Total model cost")
    currency: str = Field(description="Billing currency")
    records_last_7d: int = Field(description="Record count in the last 7 days")
    tokens_last_7d: int = Field(description="Token count in the last 7 days")
    cost_last_7d: str = Field(description="Model cost in the last 7 days")
    records_last_30d: int = Field(description="Record count in the last 30 days")
    tokens_last_30d: int = Field(description="Token count in the last 30 days")
    cost_last_30d: str = Field(description="Model cost in the last 30 days")


class TokenBillingRecord(BaseModel):
    id: str = Field(description="Usage record id")
    tenant_id: str = Field(description="Workspace id")
    tenant_name: str | None = Field(default=None, description="Workspace name")
    organization_name: str | None = Field(default=None, description="Organization name")
    provider: str = Field(description="Model provider")
    provider_type: str = Field(description="Provider type")
    model_name: str = Field(description="Model name")
    model_type: str = Field(description="Model type")
    user_id: str | None = Field(default=None, description="Invoking user id")
    is_cloud: bool = Field(description="Whether the model is cloud hosted")
    invocation_source: str | None = Field(default=None, description="Invocation source")
    input_tokens: int = Field(description="Input tokens")
    output_tokens: int = Field(description="Output tokens")
    total_tokens: int = Field(description="Total tokens")
    input_price: str = Field(description="Input token price")
    output_price: str = Field(description="Output token price")
    total_price: str = Field(description="Total price")
    currency: str = Field(description="Billing currency")
    latency: float = Field(description="Latency in seconds")
    business_type: str | None = Field(default=None, description="Business object type")
    business_id: str | None = Field(default=None, description="Business object id")
    created_at: str | None = Field(default=None, description="Record creation time")


class TokenBillingLeaderboardItem(BaseModel):
    user_id: str | None = Field(default=None, description="User id")
    name: str | None = Field(default=None, description="User display name")
    email: str | None = Field(default=None, description="User email")
    total_tokens: int = Field(description="Total tokens")
    total_cost: str = Field(description="Total cost")
    record_count: int = Field(description="Record count")


class TokenBillingOrganizationItem(BaseModel):
    organization_name: str | None = Field(default=None, description="Organization name")
    workspace_count: int = Field(description="Workspace count")
    total_tokens: int = Field(description="Total tokens")
    total_cost: str = Field(description="Total cost")
    record_count: int = Field(description="Record count")


class TokenBillingUsageResponse(BaseModel):
    table_ready: bool = Field(description="Whether the model usage table exists")
    summary: TokenBillingSummary = Field(description="Usage summary")
    records: list[TokenBillingRecord] = Field(description="Recent usage records")
    leaderboard: list[TokenBillingLeaderboardItem] = Field(description="Per-user usage summary")
    organizations: list[TokenBillingOrganizationItem] = Field(description="Per-organization usage summary")


@console_router.get(
    "/token-billing/usage",
    response_model=TokenBillingUsageResponse,
    tags=["console"],
)
@setup_required
@login_required
@account_initialization_required
def get_token_billing_usage(query: TokenBillingUsageQuery) -> TokenBillingUsageResponse:
    current_user, current_tenant_id = current_account_with_tenant()
    can_view_workspace = has_any_workspace_capability(current_user, TEAM_TOKEN_BILLING_CAPABILITIES, current_tenant_id)
    can_view_system = has_any_workspace_capability(
        current_user,
        [DESKTOP_TOKEN_BILLING_GLOBAL_VIEW_CAPABILITY],
        current_tenant_id,
    )
    requested_scope = query.scope if query.scope in {"self", "workspace", "system"} else "workspace"

    if requested_scope == "system" and can_view_system:
        usage_overview = ModelUsageRecordService.get_usage_overview(
            None,
            limit=query.limit,
            user_id=None,
        )
        return TokenBillingUsageResponse.model_validate(usage_overview)

    user_scope = requested_scope == "self" or not can_view_workspace
    usage_overview = ModelUsageRecordService.get_usage_overview(
        current_tenant_id,
        limit=query.limit,
        user_id=current_user.id if user_scope else None,
    )
    return TokenBillingUsageResponse.model_validate(usage_overview)


class TokenBillingExportQuery(BaseModel):
    limit: int = Field(default=1000, ge=1, le=5000, description="Number of records to export")
    scope: str = Field(default="workspace", description="workspace, self or system")


@console_router.get(
    "/token-billing/export",
    tags=["console"],
)
@setup_required
@login_required
@account_initialization_required
def export_token_billing_usage(query: TokenBillingExportQuery) -> Response:
    current_user, current_tenant_id = current_account_with_tenant()
    can_view_workspace = has_any_workspace_capability(current_user, TEAM_TOKEN_BILLING_CAPABILITIES, current_tenant_id)
    can_view_system = has_any_workspace_capability(
        current_user,
        [DESKTOP_TOKEN_BILLING_GLOBAL_VIEW_CAPABILITY],
        current_tenant_id,
    ) and has_any_workspace_capability(
        current_user,
        [DESKTOP_TOKEN_BILLING_EXPORT_CAPABILITY],
        current_tenant_id,
    )
    requested_scope = query.scope if query.scope in {"self", "workspace", "system"} else "workspace"

    if requested_scope == "system" and can_view_system:
        usage_overview = ModelUsageRecordService.get_usage_overview(None, limit=query.limit, user_id=None)
    else:
        user_scope = requested_scope == "self" or not can_view_workspace
        usage_overview = ModelUsageRecordService.get_usage_overview(
            current_tenant_id,
            limit=query.limit,
            user_id=current_user.id if user_scope else None,
        )
        requested_scope = "self" if user_scope else "workspace"

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "scope",
        "organization_name",
        "workspace_id",
        "workspace_name",
        "user_id",
        "model_provider",
        "model_name",
        "model_type",
        "business_type",
        "business_id",
        "source",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "total_price",
        "currency",
        "created_at",
    ])
    for record in usage_overview.get("records", []):
        writer.writerow([
            requested_scope,
            record.get("organization_name", ""),
            record.get("tenant_id", ""),
            record.get("tenant_name", ""),
            record.get("user_id", ""),
            record.get("provider", ""),
            record.get("model_name", ""),
            record.get("model_type", ""),
            record.get("business_type", ""),
            record.get("business_id", ""),
            record.get("invocation_source", ""),
            record.get("input_tokens", 0),
            record.get("output_tokens", 0),
            record.get("total_tokens", 0),
            record.get("total_price", "0"),
            record.get("currency", "USD"),
            record.get("created_at", ""),
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="token-billing-{requested_scope}.csv"',
        },
    )
