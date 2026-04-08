from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import TypeBase
from .types import LongText, StringUUID


class BetaApplicationStep(TypeBase):
    """Per-step execution status for beta application provisioning."""

    __tablename__ = "beta_application_steps"
    __table_args__ = (
        UniqueConstraint("application_id", "step_key", name="beta_application_step_application_step_key_uq"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[str] = mapped_column(StringUUID, primary_key=True)
    application_id: Mapped[str] = mapped_column(StringUUID, nullable=False, index=True)
    step_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        default="pending",
        index=True,
    )  # pending, running, success, failed, reserved
    message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    request_payload: Mapped[Optional[str]] = mapped_column(LongText, nullable=True, default=None)
    response_payload: Mapped[Optional[str]] = mapped_column(LongText, nullable=True, default=None)
    error_message: Mapped[Optional[str]] = mapped_column(LongText, nullable=True, default=None)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), default=func.now()
    )
