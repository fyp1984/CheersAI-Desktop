from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import TypeBase
from .types import LongText, StringUUID


class BetaApplicationProvisionTask(TypeBase):
    """Async provisioning task tracking records for beta applications."""

    __tablename__ = "beta_application_provision_tasks"
    __table_args__ = (
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[str] = mapped_column(StringUUID, primary_key=True)
    application_id: Mapped[str] = mapped_column(StringUUID, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # approve / retry / provision
    mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=None)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="queued", default="queued", index=True
    )  # queued / running / success / failed
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(155), nullable=True, default=None, index=True)
    requested_by: Mapped[Optional[str]] = mapped_column(StringUUID, nullable=True, default=None, index=True)
    requested_tenant_id: Mapped[Optional[str]] = mapped_column(StringUUID, nullable=True, default=None, index=True)
    requested_ip: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=None)
    error_message: Mapped[Optional[str]] = mapped_column(LongText, nullable=True, default=None)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), default=func.now()
    )
