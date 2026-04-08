from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import TypeBase
from .types import LongText, StringUUID


class BetaApplicationNotification(TypeBase):
    """Notification delivery records for beta applications."""

    __tablename__ = "beta_application_notifications"
    __table_args__ = (
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[str] = mapped_column(StringUUID, primary_key=True)
    application_id: Mapped[str] = mapped_column(StringUUID, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # email / wechat
    event: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    receiver: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending", default="pending", index=True
    )  # pending / sent / failed
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(155), nullable=True, default=None)
    error_message: Mapped[Optional[str]] = mapped_column(LongText, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), default=func.now()
    )
