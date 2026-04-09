from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import TypeBase
from .types import StringUUID


class BetaApplication(TypeBase):
    """Beta application model for storing beta access requests."""

    __tablename__ = "beta_applications"
    __table_args__ = (
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[str] = mapped_column(StringUUID, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default=None)
    language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=None)
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default=None)
    use_case: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, default=None)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending", default="pending", index=True
    )  # pending, provisioning, success, failed, rejected
    reviewer_id: Mapped[Optional[str]] = mapped_column(StringUUID, nullable=True, default=None)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    provision_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    provision_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    provision_finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, default=None)
    last_error_step: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, default=None)
    last_error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, default=None)
    sso_subject_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, default=None)
    sso_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default=None)
    filebay_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default=None)
    filebay_repo: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), default=func.now()
    )
