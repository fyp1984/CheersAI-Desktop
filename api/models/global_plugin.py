from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from libs.uuid_utils import uuidv7

from .base import TypeBase
from .types import LongText, StringUUID


class SystemPlugin(TypeBase):
    __tablename__ = "system_plugins"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="system_plugin_pkey"),
        sa.UniqueConstraint("plugin_code", name="system_plugin_plugin_code_key"),
        sa.Index("system_plugin_enabled_idx", "enabled"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID,
        primary_key=True,
        insert_default=lambda: str(uuidv7()),
        default_factory=lambda: str(uuidv7()),
        init=False,
    )
    plugin_code: Mapped[str] = mapped_column(String(255), nullable=False)
    plugin_id: Mapped[str] = mapped_column(String(255), nullable=False)
    plugin_unique_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    source_tenant_id: Mapped[str] = mapped_column(StringUUID, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    source_account_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(LongText, nullable=True, default=None)
    enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=text("true"), default=True)
    install_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), init=False
    )


class TeamModelConfig(TypeBase):
    __tablename__ = "team_model_config"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="team_model_config_pkey"),
        sa.UniqueConstraint("team_id", "plugin_code", name="team_model_config_team_plugin_key"),
        sa.Index("team_model_config_team_idx", "team_id"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID,
        primary_key=True,
        insert_default=lambda: str(uuidv7()),
        default_factory=lambda: str(uuidv7()),
        init=False,
    )
    team_id: Mapped[str] = mapped_column(StringUUID, nullable=False)
    plugin_code: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_enc: Mapped[str] = mapped_column(LongText, nullable=False)
    base_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    updated_by: Mapped[str] = mapped_column(StringUUID, nullable=False)
    max_concurrent: Mapped[int | None] = mapped_column(sa.Integer, nullable=True, default=None)
    max_qps: Mapped[int | None] = mapped_column(sa.Integer, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), init=False
    )
