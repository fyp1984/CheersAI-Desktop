from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from libs.uuid_utils import uuidv7

from .base import TypeBase
from .types import AdjustedJSON, StringUUID


class ModelUsageRecord(TypeBase):
    """
    Usage ledger for model invocations.

    Stores normalized per-call token and pricing data so billing/reporting can
    be calculated later without relying on only aggregated quota counters.
    """

    __tablename__ = "model_usage_records"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="model_usage_record_pkey"),
        sa.Index("model_usage_record_tenant_created_idx", "tenant_id", "created_at"),
        sa.Index("model_usage_record_provider_model_idx", "provider", "model_name", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID,
        insert_default=lambda: str(uuidv7()),
        default_factory=lambda: str(uuidv7()),
        init=False,
    )
    tenant_id: Mapped[str] = mapped_column(StringUUID, nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(40), nullable=False)
    model_type: Mapped[str] = mapped_column(String(40), nullable=False)
    input_unit_price: Mapped[Decimal] = mapped_column(sa.Numeric(20, 10), nullable=False, server_default=text("0"))
    output_unit_price: Mapped[Decimal] = mapped_column(sa.Numeric(20, 10), nullable=False, server_default=text("0"))
    input_price_unit: Mapped[Decimal] = mapped_column(sa.Numeric(20, 10), nullable=False, server_default=text("0"))
    output_price_unit: Mapped[Decimal] = mapped_column(sa.Numeric(20, 10), nullable=False, server_default=text("0"))
    input_price: Mapped[Decimal] = mapped_column(sa.Numeric(20, 10), nullable=False, server_default=text("0"))
    output_price: Mapped[Decimal] = mapped_column(sa.Numeric(20, 10), nullable=False, server_default=text("0"))
    total_price: Mapped[Decimal] = mapped_column(sa.Numeric(20, 10), nullable=False, server_default=text("0"))

    input_tokens: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, server_default=text("0"), default=0)
    output_tokens: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, server_default=text("0"), default=0)
    total_tokens: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, server_default=text("0"), default=0)

    currency: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'USD'"), default="USD")
    latency: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default=text("0"), default=0)
    user_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    is_cloud: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.true(), default=True)
    invocation_source: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    request_metadata: Mapped[dict | None] = mapped_column(AdjustedJSON(), nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        init=False,
    )
