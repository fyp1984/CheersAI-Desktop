import enum
import json
from dataclasses import field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

import sqlalchemy as sa
from flask_login import UserMixin
from sqlalchemy import DateTime, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, validates
from typing_extensions import deprecated

from .base import TypeBase
from .engine import db
from .types import LongText, StringUUID


class TenantAccountRole(enum.StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    NORMAL = "normal"
    DATASET_OPERATOR = "dataset_operator"

    @staticmethod
    def is_valid_role(role: str) -> bool:
        if not role:
            return False
        return role in {
            TenantAccountRole.OWNER,
            TenantAccountRole.ADMIN,
            TenantAccountRole.EDITOR,
            TenantAccountRole.NORMAL,
            TenantAccountRole.DATASET_OPERATOR,
        }

    @staticmethod
    def is_privileged_role(role: Optional["TenantAccountRole"]) -> bool:
        if not role:
            return False
        return role in {TenantAccountRole.OWNER, TenantAccountRole.ADMIN}

    @staticmethod
    def is_admin_role(role: Optional["TenantAccountRole"]) -> bool:
        if not role:
            return False
        return role == TenantAccountRole.ADMIN

    @staticmethod
    def is_non_owner_role(role: Optional["TenantAccountRole"]) -> bool:
        if not role:
            return False
        return role in {
            TenantAccountRole.ADMIN,
            TenantAccountRole.EDITOR,
            TenantAccountRole.NORMAL,
            TenantAccountRole.DATASET_OPERATOR,
        }

    @staticmethod
    def is_editing_role(role: Optional["TenantAccountRole"]) -> bool:
        if not role:
            return False
        return role in {TenantAccountRole.OWNER, TenantAccountRole.ADMIN, TenantAccountRole.EDITOR}

    @staticmethod
    def is_dataset_edit_role(role: Optional["TenantAccountRole"]) -> bool:
        if not role:
            return False
        return role in {
            TenantAccountRole.OWNER,
            TenantAccountRole.ADMIN,
            TenantAccountRole.EDITOR,
            TenantAccountRole.DATASET_OPERATOR,
        }


class AccountStatus(enum.StrEnum):
    PENDING = "pending"
    UNINITIALIZED = "uninitialized"
    ACTIVE = "active"
    BANNED = "banned"
    CLOSED = "closed"


class Account(UserMixin, TypeBase):
    __tablename__ = "accounts"
    __table_args__ = (sa.PrimaryKeyConstraint("id", name="account_pkey"), sa.Index("account_email_idx", "email"))

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    password: Mapped[str | None] = mapped_column(String(255), default=None)
    password_salt: Mapped[str | None] = mapped_column(String(255), default=None)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    interface_language: Mapped[str | None] = mapped_column(String(255), default=None)
    interface_theme: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    timezone: Mapped[str | None] = mapped_column(String(255), default=None)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    last_login_ip: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False
    )
    status: Mapped[str] = mapped_column(String(16), server_default=sa.text("'active'"), default="active")
    initialized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    custom_config: Mapped[str | None] = mapped_column(LongText, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False, onupdate=func.current_timestamp()
    )

    role: TenantAccountRole | None = field(default=None, init=False)
    _current_tenant: "Tenant | None" = field(default=None, init=False)

    @validates("status")
    def _normalize_status(self, _key: str, value: str | AccountStatus) -> str:
        if isinstance(value, AccountStatus):
            return value.value
        return value

    @property
    def is_password_set(self):
        config = self.custom_config_dict
        return self.password is not None or bool(
            config.get("desktop_sso_password_set") or config.get("desktop_sso_subject")
        )

    @property
    def current_tenant(self):
        return self._current_tenant

    @current_tenant.setter
    def current_tenant(self, tenant: "Tenant"):
        with Session(db.engine, expire_on_commit=False) as session:
            tenant_join_query = select(TenantAccountJoin).where(
                TenantAccountJoin.tenant_id == tenant.id, TenantAccountJoin.account_id == self.id
            )
            tenant_join = session.scalar(tenant_join_query)
            tenant_query = select(Tenant).where(Tenant.id == tenant.id)
            # TODO: A workaround to reload the tenant with `expire_on_commit=False`, allowing
            # access to it after the session has been closed.
            # This prevents `DetachedInstanceError` when accessing the tenant outside
            # the session's lifecycle.
            # (The `tenant` argument is typically loaded by `db.session` without the
            # `expire_on_commit=False` flag, meaning its lifetime is tied to the web
            # request's lifecycle.)
            tenant_reloaded = session.scalars(tenant_query).one()

        if tenant_join:
            self.role = TenantAccountRole(tenant_join.role)
            self._current_tenant = tenant_reloaded
            return
        self._current_tenant = None

    @property
    def current_tenant_id(self) -> str | None:
        return self._current_tenant.id if self._current_tenant else None

    def set_tenant_id(self, tenant_id: str):
        query = (
            select(Tenant, TenantAccountJoin)
            .where(Tenant.id == tenant_id)
            .where(TenantAccountJoin.tenant_id == Tenant.id)
            .where(TenantAccountJoin.account_id == self.id)
        )
        with Session(db.engine, expire_on_commit=False) as session:
            tenant_account_join = session.execute(query).first()
            if not tenant_account_join:
                return
            tenant, join = tenant_account_join
            self.role = TenantAccountRole(join.role)
            self._current_tenant = tenant

    @property
    def current_role(self):
        return self.role

    def get_status(self) -> AccountStatus:
        status_str = self.status
        return AccountStatus(status_str)

    @classmethod
    def get_by_openid(cls, provider: str, open_id: str):
        account_integrate = (
            db.session.query(AccountIntegrate)
            .where(AccountIntegrate.provider == provider, AccountIntegrate.open_id == open_id)
            .one_or_none()
        )
        if account_integrate:
            return db.session.query(Account).where(Account.id == account_integrate.account_id).one_or_none()
        return None

    # check current_user.current_tenant.current_role in ['admin', 'owner']
    @property
    def is_admin_or_owner(self):
        if TenantAccountRole.is_privileged_role(self.role):
            return True

        from libs.desktop_auth import has_any_workspace_capability

        return has_any_workspace_capability(self, ["desktop_team_manage"], self.current_tenant_id)

    @property
    def is_admin(self):
        return TenantAccountRole.is_admin_role(self.role)

    @property
    @deprecated("Use has_edit_permission instead.")
    def is_editor(self):
        """Determines if the account has edit permissions in their current tenant (workspace).

        This property checks if the current role has editing privileges, which includes:
        - `OWNER`
        - `ADMIN`
        - `EDITOR`

        Note: This checks for any role with editing permission, not just the 'EDITOR' role specifically.
        """
        return self.has_edit_permission

    @property
    def has_edit_permission(self):
        """Determines if the account has editing permissions in their current tenant (workspace).

        This property checks if the current role has editing privileges, which includes:
        - `OWNER`
        - `ADMIN`
        - `EDITOR`
        """
        return TenantAccountRole.is_editing_role(self.role)

    @property
    def is_dataset_editor(self):
        return TenantAccountRole.is_dataset_edit_role(self.role)

    @property
    def is_dataset_operator(self):
        return self.role == TenantAccountRole.DATASET_OPERATOR

    @property
    def custom_config_dict(self) -> dict[str, Any]:
        return json.loads(self.custom_config) if self.custom_config else {}

    @custom_config_dict.setter
    def custom_config_dict(self, value: dict[str, Any]) -> None:
        self.custom_config = json.dumps(value)


class TenantStatus(enum.StrEnum):
    NORMAL = "normal"
    ARCHIVE = "archive"


class Tenant(TypeBase):
    __tablename__ = "tenants"
    __table_args__ = (sa.PrimaryKeyConstraint("id", name="tenant_pkey"),)

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    name: Mapped[str] = mapped_column(String(255))
    encrypt_public_key: Mapped[str | None] = mapped_column(LongText, default=None)
    plan: Mapped[str] = mapped_column(String(255), server_default=sa.text("'basic'"), default="basic")
    status: Mapped[str] = mapped_column(String(255), server_default=sa.text("'normal'"), default="normal")
    custom_config: Mapped[str | None] = mapped_column(LongText, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), init=False, onupdate=func.current_timestamp()
    )

    def get_accounts(self) -> list[Account]:
        return list(
            db.session.scalars(
                select(Account).where(
                    Account.id == TenantAccountJoin.account_id, TenantAccountJoin.tenant_id == self.id
                )
            ).all()
        )

    @property
    def custom_config_dict(self) -> dict[str, Any]:
        return json.loads(self.custom_config) if self.custom_config else {}

    @custom_config_dict.setter
    def custom_config_dict(self, value: dict[str, Any]) -> None:
        self.custom_config = json.dumps(value)


class TenantAccountJoin(TypeBase):
    __tablename__ = "tenant_account_joins"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="tenant_account_join_pkey"),
        sa.Index("tenant_account_join_account_id_idx", "account_id"),
        sa.Index("tenant_account_join_tenant_id_idx", "tenant_id"),
        sa.UniqueConstraint("tenant_id", "account_id", name="unique_tenant_account_join"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    tenant_id: Mapped[str] = mapped_column(StringUUID)
    account_id: Mapped[str] = mapped_column(StringUUID)
    current: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.text("false"), default=False)
    role: Mapped[str] = mapped_column(String(16), server_default="normal", default="normal")
    invited_by: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False, onupdate=func.current_timestamp()
    )


class AccountIntegrate(TypeBase):
    __tablename__ = "account_integrates"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="account_integrate_pkey"),
        sa.UniqueConstraint("account_id", "provider", name="unique_account_provider"),
        sa.UniqueConstraint("provider", "open_id", name="unique_provider_open_id"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    account_id: Mapped[str] = mapped_column(StringUUID)
    provider: Mapped[str] = mapped_column(String(16))
    open_id: Mapped[str] = mapped_column(String(255))
    encrypted_token: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False, onupdate=func.current_timestamp()
    )


class InvitationCode(TypeBase):
    __tablename__ = "invitation_codes"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="invitation_code_pkey"),
        sa.Index("invitation_codes_batch_idx", "batch"),
        sa.Index("invitation_codes_code_idx", "code", "status"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, init=False)
    batch: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), server_default=sa.text("'unused'"), default="unused")
    used_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    used_by_tenant_id: Mapped[str | None] = mapped_column(StringUUID, default=None)
    used_by_account_id: Mapped[str | None] = mapped_column(StringUUID, default=None)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=sa.func.current_timestamp(), nullable=False, init=False
    )


class AccountInviteCode(TypeBase):
    __tablename__ = "account_invite_codes"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="account_invite_code_pkey"),
        sa.UniqueConstraint("code", name="unique_account_invite_code"),
        sa.Index("account_invite_codes_owner_idx", "owner_account_id"),
        sa.Index("account_invite_codes_status_idx", "status"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    owner_account_id: Mapped[str] = mapped_column(StringUUID)
    code: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), server_default=sa.text("'unused'"), default="unused")
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    used_by_account_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False, onupdate=func.current_timestamp()
    )


class AccountPointTransaction(TypeBase):
    __tablename__ = "account_point_transactions"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="account_point_transaction_pkey"),
        sa.Index("account_point_transactions_account_idx", "account_id"),
        sa.Index("account_point_transactions_account_expire_idx", "account_id", "expires_at"),
        sa.Index("account_point_transactions_source_idx", "source", "source_id"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    account_id: Mapped[str] = mapped_column(StringUUID)
    points: Mapped[int] = mapped_column(sa.Integer)
    type: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(255))
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    remaining_points: Mapped[int] = mapped_column(sa.Integer, server_default=sa.text("0"), default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False
    )


class AccountPointRedemption(TypeBase):
    __tablename__ = "account_point_redemptions"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="account_point_redemption_pkey"),
        sa.Index("account_point_redemptions_account_idx", "account_id"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    account_id: Mapped[str] = mapped_column(StringUUID)
    reward_id: Mapped[str] = mapped_column(String(64))
    reward_name: Mapped[str] = mapped_column(String(255))
    points: Mapped[int] = mapped_column(sa.Integer)
    status: Mapped[str] = mapped_column(String(32), server_default=sa.text("'pending_activation'"), default="pending_activation")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False
    )


class UserFeedback(TypeBase):
    __tablename__ = "user_feedbacks"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="user_feedback_pkey"),
        sa.UniqueConstraint("ticket_no", name="unique_user_feedback_ticket_no"),
        sa.Index("user_feedbacks_tenant_status_idx", "tenant_id", "status"),
        sa.Index("user_feedbacks_account_idx", "account_id"),
        sa.Index("user_feedbacks_source_idx", "source", "channel"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    ticket_no: Mapped[str] = mapped_column(String(64))
    tenant_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    account_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    user_name: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    source: Mapped[str] = mapped_column(String(64), server_default=sa.text("'customer_service'"), default="customer_service")
    channel: Mapped[str] = mapped_column(String(32), server_default=sa.text("'ai'"), default="ai")
    category: Mapped[str] = mapped_column(String(64), server_default=sa.text("'general'"), default="general")
    title: Mapped[str] = mapped_column(String(255), default="")
    content: Mapped[str] = mapped_column(LongText, default="")
    status: Mapped[str] = mapped_column(String(32), server_default=sa.text("'open'"), default="open")
    priority: Mapped[str] = mapped_column(String(16), server_default=sa.text("'normal'"), default="normal")
    assigned_to: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    resolution: Mapped[str | None] = mapped_column(LongText, nullable=True, default=None)
    page_url: Mapped[str | None] = mapped_column(String(2048), nullable=True, default=None)
    app_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    conversation_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    message_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    contact_allowed: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.text("true"), default=True)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", sa.JSON, default_factory=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False, onupdate=func.current_timestamp()
    )


class UserFeedbackMessage(TypeBase):
    __tablename__ = "user_feedback_messages"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="user_feedback_message_pkey"),
        sa.Index("user_feedback_messages_feedback_idx", "feedback_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    feedback_id: Mapped[str] = mapped_column(StringUUID)
    content: Mapped[str] = mapped_column(LongText, default="")
    sender_type: Mapped[str] = mapped_column(String(32), server_default=sa.text("'system'"), default="system")
    sender_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    is_internal: Mapped[bool] = mapped_column(sa.Boolean, server_default=sa.text("false"), default=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", sa.JSON, default_factory=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, init=False
    )


class TenantPluginPermission(TypeBase):
    class InstallPermission(enum.StrEnum):
        EVERYONE = "everyone"
        ADMINS = "admins"
        NOBODY = "noone"

    class DebugPermission(enum.StrEnum):
        EVERYONE = "everyone"
        ADMINS = "admins"
        NOBODY = "noone"

    __tablename__ = "account_plugin_permissions"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="account_plugin_permission_pkey"),
        sa.UniqueConstraint("tenant_id", name="unique_tenant_plugin"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    tenant_id: Mapped[str] = mapped_column(StringUUID, nullable=False)
    install_permission: Mapped[InstallPermission] = mapped_column(
        String(16), nullable=False, server_default="everyone", default=InstallPermission.EVERYONE
    )
    debug_permission: Mapped[DebugPermission] = mapped_column(
        String(16), nullable=False, server_default="noone", default=DebugPermission.NOBODY
    )


class TenantPluginAutoUpgradeStrategy(TypeBase):
    class StrategySetting(enum.StrEnum):
        DISABLED = "disabled"
        FIX_ONLY = "fix_only"
        LATEST = "latest"

    class UpgradeMode(enum.StrEnum):
        ALL = "all"
        PARTIAL = "partial"
        EXCLUDE = "exclude"

    __tablename__ = "tenant_plugin_auto_upgrade_strategies"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="tenant_plugin_auto_upgrade_strategy_pkey"),
        sa.UniqueConstraint("tenant_id", name="unique_tenant_plugin_auto_upgrade_strategy"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID, insert_default=lambda: str(uuid4()), default_factory=lambda: str(uuid4()), init=False
    )
    tenant_id: Mapped[str] = mapped_column(StringUUID, nullable=False)
    strategy_setting: Mapped[StrategySetting] = mapped_column(
        String(16), nullable=False, server_default="fix_only", default=StrategySetting.FIX_ONLY
    )
    upgrade_mode: Mapped[UpgradeMode] = mapped_column(
        String(16), nullable=False, server_default="exclude", default=UpgradeMode.EXCLUDE
    )
    exclude_plugins: Mapped[list[str]] = mapped_column(sa.JSON, nullable=False, default_factory=list)
    include_plugins: Mapped[list[str]] = mapped_column(sa.JSON, nullable=False, default_factory=list)
    upgrade_time_of_day: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), init=False, onupdate=func.current_timestamp()
    )
