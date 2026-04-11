from pydantic import BaseModel, Field

from controllers.console.wraps import account_initialization_required, setup_required
from controllers.fastopenapi import console_router
from libs.login import current_account_with_tenant, login_required
from services.model_usage_record_service import ModelUsageRecordService


class TokenBillingUsageQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=100, description="Number of recent records to return")
    scope: str = Field(default="workspace", description="workspace or self")


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
    created_at: str | None = Field(default=None, description="Record creation time")


class TokenBillingLeaderboardItem(BaseModel):
    user_id: str | None = Field(default=None, description="User id")
    name: str | None = Field(default=None, description="User display name")
    email: str | None = Field(default=None, description="User email")
    total_tokens: int = Field(description="Total tokens")
    total_cost: str = Field(description="Total cost")
    record_count: int = Field(description="Record count")


class TokenBillingUsageResponse(BaseModel):
    table_ready: bool = Field(description="Whether the model usage table exists")
    summary: TokenBillingSummary = Field(description="Usage summary")
    records: list[TokenBillingRecord] = Field(description="Recent usage records")
    leaderboard: list[TokenBillingLeaderboardItem] = Field(description="Per-user usage summary")


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
    can_view_workspace = bool(current_user and getattr(current_user, "has_edit_permission", False))
    user_scope = query.scope == "self" or not can_view_workspace
    usage_overview = ModelUsageRecordService.get_usage_overview(
        current_tenant_id,
        limit=query.limit,
        user_id=current_user.id if user_scope else None,
    )
    return TokenBillingUsageResponse.model_validate(usage_overview)
