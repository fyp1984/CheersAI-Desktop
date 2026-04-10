from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from core.model_runtime.entities.llm_entities import LLMUsage
from core.model_runtime.entities.text_embedding_entities import EmbeddingUsage
from core.model_runtime.entities.model_entities import ModelType
from extensions.ext_database import db
from models.model_usage import ModelUsageRecord

logger = logging.getLogger(__name__)


class ModelUsageRecordService:
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
        except Exception:
            db.session.rollback()
            logger.exception("Failed to persist model usage record for %s/%s", provider, model_instance.model)

    @staticmethod
    def _is_cloud_model(provider: str) -> bool:
        provider_name = provider.lower()
        local_provider_keywords = ("ollama", "xinference", "openllm", "localai", "lmstudio", "vllm")
        return not any(keyword in provider_name for keyword in local_provider_keywords)
