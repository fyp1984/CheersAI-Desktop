from __future__ import annotations

import logging
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from core.model_runtime.entities.llm_entities import LLMUsage
from core.model_runtime.entities.text_embedding_entities import EmbeddingUsage
from core.model_runtime.entities.model_entities import ModelType
from extensions.ext_database import db
from models.account import Account, Tenant, TenantAccountJoin
from models.model_usage import ModelUsageRecord
from services.token_quota_service import TokenQuotaService

logger = logging.getLogger(__name__)


class ModelUsageRecordService:
    @classmethod
    def is_table_ready(cls) -> bool:
        inspector = sa.inspect(db.engine)
        return inspector.has_table(ModelUsageRecord.__tablename__)

    @classmethod
    def get_usage_overview(cls, tenant_id: str | None, limit: int = 20, user_id: str | None = None) -> dict[str, Any]:
        """Return token usage aggregates for one tenant, one user, or the whole system."""

        if not cls.is_table_ready():
            return {
                "table_ready": False,
                "summary": {
                    "total_tokens": 0,
                    "total_cost": "0",
                    "currency": "USD",
                    "records_last_7d": 0,
                    "tokens_last_7d": 0,
                    "cost_last_7d": "0",
                    "records_last_30d": 0,
                    "tokens_last_30d": 0,
                    "cost_last_30d": "0",
                },
                "records": [],
                "leaderboard": [],
                "organizations": [],
            }

        now = datetime.now(UTC)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        filters = []
        if tenant_id:
            filters.append(ModelUsageRecord.tenant_id == tenant_id)
        if user_id:
            filters.append(ModelUsageRecord.user_id == user_id)

        summary_row = db.session.execute(
            sa.select(
                sa.func.coalesce(sa.func.sum(ModelUsageRecord.total_tokens), 0).label("total_tokens"),
                sa.func.coalesce(sa.func.sum(ModelUsageRecord.total_price), 0).label("total_cost"),
                sa.func.coalesce(sa.func.max(ModelUsageRecord.currency), "USD").label("currency"),
                sa.func.coalesce(
                    sa.func.sum(sa.case((ModelUsageRecord.created_at >= last_7d, 1), else_=0)),
                    0,
                ).label("records_last_7d"),
                sa.func.coalesce(
                    sa.func.sum(sa.case((ModelUsageRecord.created_at >= last_7d, ModelUsageRecord.total_tokens), else_=0)),
                    0,
                ).label("tokens_last_7d"),
                sa.func.coalesce(
                    sa.func.sum(sa.case((ModelUsageRecord.created_at >= last_7d, ModelUsageRecord.total_price), else_=0)),
                    0,
                ).label("cost_last_7d"),
                sa.func.coalesce(
                    sa.func.sum(sa.case((ModelUsageRecord.created_at >= last_30d, 1), else_=0)),
                    0,
                ).label("records_last_30d"),
                sa.func.coalesce(
                    sa.func.sum(
                        sa.case((ModelUsageRecord.created_at >= last_30d, ModelUsageRecord.total_tokens), else_=0)
                    ),
                    0,
                ).label("tokens_last_30d"),
                sa.func.coalesce(
                    sa.func.sum(sa.case((ModelUsageRecord.created_at >= last_30d, ModelUsageRecord.total_price), else_=0)),
                    0,
                ).label("cost_last_30d"),
            ).where(*filters)
        ).one()

        recent_records = list(
            db.session.execute(
            sa.select(ModelUsageRecord)
            .where(*filters)
            .order_by(ModelUsageRecord.created_at.desc())
            .limit(limit)
            ).scalars()
        )

        leaderboard = []
        if user_id is None:
            leaderboard_rows = db.session.execute(
                sa.select(
                    ModelUsageRecord.user_id.label("user_id"),
                    sa.func.coalesce(sa.func.sum(ModelUsageRecord.total_tokens), 0).label("total_tokens"),
                    sa.func.coalesce(sa.func.sum(ModelUsageRecord.total_price), 0).label("total_cost"),
                    sa.func.count(ModelUsageRecord.id).label("record_count"),
                )
                .where(*filters, ModelUsageRecord.user_id.is_not(None))
                .group_by(ModelUsageRecord.user_id)
                .order_by(sa.desc("total_tokens"))
                .limit(10)
            ).all()

            user_ids = [row.user_id for row in leaderboard_rows if row.user_id]
            account_rows = {}
            if user_ids:
                account_rows = {
                    row.id: row
                    for row in db.session.execute(
                        sa.select(Account.id, Account.name, Account.email)
                        .where(Account.id.in_(user_ids))
                        .distinct(Account.id)
                    ).all()
                }

            leaderboard = [
                {
                    "user_id": row.user_id,
                    "name": getattr(account_rows.get(row.user_id), "name", None),
                    "email": getattr(account_rows.get(row.user_id), "email", None),
                    "total_tokens": int(row.total_tokens or 0),
                    "total_cost": cls._decimal_to_str(row.total_cost),
                    "record_count": int(row.record_count or 0),
                }
                for row in leaderboard_rows
            ]

        organization_leaderboard = []
        tenant_ids = {record.tenant_id for record in recent_records if record.tenant_id}
        tenant_rows = {}
        tenant_organization_rows = {}
        if tenant_id is None and user_id is None:
            organization_leaderboard = cls._build_organization_leaderboard(filters)
        if tenant_ids:
            tenant_rows = {
                row.id: row.name
                for row in db.session.execute(
                    sa.select(Tenant.id, Tenant.name).where(Tenant.id.in_(tenant_ids))
                ).all()
            }
            tenant_organization_rows = cls._resolve_tenant_organization_names(tenant_ids)

        return {
            "table_ready": True,
            "summary": {
                "total_tokens": int(summary_row.total_tokens or 0),
                "total_cost": cls._decimal_to_str(summary_row.total_cost),
                "currency": summary_row.currency or "USD",
                "records_last_7d": int(summary_row.records_last_7d or 0),
                "tokens_last_7d": int(summary_row.tokens_last_7d or 0),
                "cost_last_7d": cls._decimal_to_str(summary_row.cost_last_7d),
                "records_last_30d": int(summary_row.records_last_30d or 0),
                "tokens_last_30d": int(summary_row.tokens_last_30d or 0),
                "cost_last_30d": cls._decimal_to_str(summary_row.cost_last_30d),
            },
            "records": [
                {
                    "id": record.id,
                    "tenant_id": record.tenant_id,
                    "tenant_name": tenant_rows.get(record.tenant_id),
                    "organization_name": tenant_organization_rows.get(record.tenant_id),
                    "provider": record.provider,
                    "provider_type": record.provider_type,
                    "model_name": record.model_name,
                    "model_type": record.model_type,
                    "user_id": record.user_id,
                    "is_cloud": record.is_cloud,
                    "invocation_source": record.invocation_source,
                    "input_tokens": int(record.input_tokens or 0),
                    "output_tokens": int(record.output_tokens or 0),
                    "total_tokens": int(record.total_tokens or 0),
                    "input_price": cls._decimal_to_str(record.input_price),
                    "output_price": cls._decimal_to_str(record.output_price),
                    "total_price": cls._decimal_to_str(record.total_price),
                    "currency": record.currency,
                    "latency": float(record.latency or 0),
                    "business_type": cls._extract_business_type(record.request_metadata),
                    "business_id": cls._extract_business_id(record.request_metadata),
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                }
                for record in recent_records
            ],
            "leaderboard": leaderboard,
            "organizations": [
                {
                    "organization_name": item.get("organization_name"),
                    "workspace_count": int(item.get("workspace_count", 0) or 0),
                    "total_tokens": int(item.get("total_tokens", 0) or 0),
                    "total_cost": cls._decimal_to_str(item.get("total_cost")),
                    "record_count": int(item.get("record_count", 0) or 0),
                }
                for item in organization_leaderboard
            ],
        }

    @classmethod
    def record_llm_usage(cls, model_instance: Any, usage: LLMUsage, user_id: str | None, metadata: dict | None) -> None:
        if usage.total_tokens <= 0:
            return

        cls._insert_record(
            model_instance=model_instance,
            user_id=user_id,
            model_type=ModelType.LLM.value,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            input_unit_price=usage.prompt_unit_price,
            output_unit_price=usage.completion_unit_price,
            input_price_unit=usage.prompt_price_unit,
            output_price_unit=usage.completion_price_unit,
            input_price=usage.prompt_price,
            output_price=usage.completion_price,
            total_price=usage.total_price,
            currency=usage.currency,
            latency=usage.latency,
            metadata=metadata,
        )

    @classmethod
    def record_embedding_usage(
        cls, model_instance: Any, usage: EmbeddingUsage, user_id: str | None, metadata: dict | None
    ) -> None:
        if usage.total_tokens <= 0:
            return

        cls._insert_record(
            model_instance=model_instance,
            user_id=user_id,
            model_type=ModelType.TEXT_EMBEDDING.value,
            input_tokens=usage.tokens,
            output_tokens=0,
            total_tokens=usage.total_tokens,
            input_unit_price=usage.unit_price,
            output_unit_price=Decimal("0"),
            input_price_unit=usage.price_unit,
            output_price_unit=Decimal("0"),
            input_price=usage.total_price,
            output_price=Decimal("0"),
            total_price=usage.total_price,
            currency=usage.currency,
            latency=usage.latency,
            metadata=metadata,
        )

    @classmethod
    def _insert_record(
        cls,
        *,
        model_instance: Any,
        user_id: str | None,
        model_type: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        input_unit_price: Decimal,
        output_unit_price: Decimal,
        input_price_unit: Decimal,
        output_price_unit: Decimal,
        input_price: Decimal,
        output_price: Decimal,
        total_price: Decimal,
        currency: str,
        latency: float,
        metadata: dict | None,
    ) -> None:
        tenant_id = model_instance.provider_model_bundle.configuration.tenant_id
        provider_configuration = model_instance.provider_model_bundle.configuration
        provider = model_instance.provider

        try:
            record = ModelUsageRecord(
                tenant_id=tenant_id,
                user_id=user_id,
                provider=provider,
                provider_type=provider_configuration.using_provider_type.value,
                model_name=model_instance.model,
                model_type=model_type,
                is_cloud=cls._is_cloud_model(provider),
                invocation_source=(metadata or {}).get("source"),
                request_metadata=metadata or {},
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                input_unit_price=input_unit_price,
                output_unit_price=output_unit_price,
                input_price_unit=input_price_unit,
                output_price_unit=output_price_unit,
                input_price=input_price,
                output_price=output_price,
                total_price=total_price,
                currency=currency or "USD",
                latency=latency or 0,
            )
            db.session.add(record)
            db.session.commit()
            
            # 记录到配额系统
            try:
                TokenQuotaService.record_token_usage(
                    tenant_id=tenant_id,
                    model_provider=provider,
                    model_name=model_instance.model,
                    tokens_used=total_tokens,
                    user_id=user_id,
                    request_id=record.id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    extra_info={
                        "model_type": model_type,
                        "is_cloud": cls._is_cloud_model(provider),
                        "total_price": str(total_price),
                        "currency": currency or "USD",
                    },
                )
            except Exception:
                logger.exception("Failed to record token usage to quota system")
                
        except Exception:
            db.session.rollback()
            logger.exception("Failed to persist model usage record for %s/%s", provider, model_instance.model)

    @staticmethod
    def _is_cloud_model(provider: str) -> bool:
        provider_name = provider.lower()
        local_provider_keywords = ("ollama", "xinference", "openllm", "localai", "lmstudio", "vllm")
        return not any(keyword in provider_name for keyword in local_provider_keywords)

    @staticmethod
    def _decimal_to_str(value: Decimal | None) -> str:
        if value is None:
            return "0"
        return format(value.normalize(), "f") if value != 0 else "0"

    @staticmethod
    def _extract_business_type(metadata: dict | None) -> str | None:
        if not isinstance(metadata, dict):
            return None

        if metadata.get("workflow_id") or metadata.get("workflow_app_id"):
            return "workflow"
        if metadata.get("agent_id"):
            return "agent"
        if metadata.get("app_id"):
            return "app"

        source = metadata.get("source")
        return source if isinstance(source, str) and source in {"app", "agent", "workflow"} else None

    @staticmethod
    def _extract_business_id(metadata: dict | None) -> str | None:
        if not isinstance(metadata, dict):
            return None

        for key in ("workflow_id", "workflow_app_id", "agent_id", "app_id"):
            value = metadata.get(key)
            if isinstance(value, str) and value:
                return value

        return None

    @classmethod
    def _resolve_tenant_organization_names(cls, tenant_ids: set[str]) -> dict[str, str]:
        if not tenant_ids:
            return {}

        rows = db.session.execute(
            sa.select(TenantAccountJoin.tenant_id, Account.custom_config)
            .join(Account, Account.id == TenantAccountJoin.account_id)
            .where(TenantAccountJoin.tenant_id.in_(tenant_ids))
            .order_by(TenantAccountJoin.created_at.asc())
        ).all()

        tenant_organization_names: dict[str, str] = {}
        for row in rows:
            tenant_id = getattr(row, "tenant_id", None)
            if not isinstance(tenant_id, str) or tenant_id in tenant_organization_names:
                continue

            organization_name = cls._extract_organization_name(getattr(row, "custom_config", None))
            if organization_name:
                tenant_organization_names[tenant_id] = organization_name

        return tenant_organization_names

    @staticmethod
    def _extract_organization_name(custom_config: str | None) -> str | None:
        if not isinstance(custom_config, str) or not custom_config.strip():
            return None

        try:
            config = json.loads(custom_config)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

        organization_name = config.get("desktop_sso_owner")
        if isinstance(organization_name, str):
            organization_name = organization_name.strip()
            if organization_name:
                return organization_name

        return None

    @classmethod
    def _build_organization_leaderboard(cls, filters: list[Any]) -> list[dict[str, Any]]:
        tenant_usage_rows = db.session.execute(
            sa.select(
                ModelUsageRecord.tenant_id.label("tenant_id"),
                sa.func.coalesce(sa.func.sum(ModelUsageRecord.total_tokens), 0).label("total_tokens"),
                sa.func.coalesce(sa.func.sum(ModelUsageRecord.total_price), 0).label("total_cost"),
                sa.func.count(ModelUsageRecord.id).label("record_count"),
            )
            .where(*filters, ModelUsageRecord.tenant_id.is_not(None))
            .group_by(ModelUsageRecord.tenant_id)
        ).all()

        tenant_ids = {
            row.tenant_id
            for row in tenant_usage_rows
            if isinstance(getattr(row, "tenant_id", None), str) and row.tenant_id
        }
        tenant_organization_rows = cls._resolve_tenant_organization_names(tenant_ids)

        organization_summary: dict[str | None, dict[str, Any]] = {}
        for row in tenant_usage_rows:
            organization_name = tenant_organization_rows.get(row.tenant_id)
            current = organization_summary.setdefault(
                organization_name,
                {
                    "organization_name": organization_name,
                    "workspace_ids": set(),
                    "total_tokens": 0,
                    "total_cost": Decimal("0"),
                    "record_count": 0,
                },
            )
            current["workspace_ids"].add(row.tenant_id)
            current["total_tokens"] += int(row.total_tokens or 0)
            current["total_cost"] += row.total_cost or Decimal("0")
            current["record_count"] += int(row.record_count or 0)

        return sorted(
            [
                {
                    "organization_name": item["organization_name"],
                    "workspace_count": len(item["workspace_ids"]),
                    "total_tokens": item["total_tokens"],
                    "total_cost": item["total_cost"],
                    "record_count": item["record_count"],
                }
                for item in organization_summary.values()
            ],
            key=lambda item: item["total_tokens"],
            reverse=True,
        )[:10]
