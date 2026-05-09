"""
Token Quota Management Models
用于管理云端模型 Token 配额的数据库模型
"""

import enum
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from extensions.ext_database import db
from models.types import StringUUID


class QuotaIntervalType(enum.StrEnum):
    """配额时间间隔类型"""
    HOURLY = "hourly"  # 每小时
    DAILY = "daily"  # 每天
    WEEKLY = "weekly"  # 每周
    MONTHLY = "monthly"  # 每月
    CUSTOM = "custom"  # 自定义（秒数）


class QuotaStatus(enum.StrEnum):
    """配额状态"""
    ACTIVE = "active"  # 激活
    PAUSED = "paused"  # 暂停
    EXCEEDED = "exceeded"  # 已超额


class TokenQuotaConfig(db.Model):
    """
    Token 配额配置表
    定义租户或用户的 Token 使用配额规则
    """
    __tablename__ = "token_quota_configs"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="token_quota_config_pkey"),
        sa.Index("token_quota_config_tenant_idx", "tenant_id"),
        sa.Index("token_quota_config_user_idx", "user_id"),
        sa.UniqueConstraint("tenant_id", "user_id", "name", name="token_quota_config_unique"),
    )

    # 基础字段
    id: Mapped[str] = mapped_column(StringUUID, server_default=db.text("uuid_generate_v4()"))
    tenant_id: Mapped[str] = mapped_column(StringUUID, nullable=False, comment="租户ID")
    user_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, comment="用户ID（为空表示租户级配置）")
    
    # 配额配置
    name: Mapped[str] = mapped_column(db.String(255), nullable=False, comment="配置名称")
    description: Mapped[str | None] = mapped_column(db.Text, nullable=True, comment="配置描述")
    
    # 时间间隔配置
    interval_type: Mapped[str] = mapped_column(
        db.String(20), 
        nullable=False, 
        server_default="daily",
        comment="时间间隔类型"
    )
    interval_value: Mapped[int | None] = mapped_column(
        db.Integer, 
        nullable=True,
        comment="自定义间隔值（秒数，仅当 interval_type=custom 时使用）"
    )
    
    # Token 配额
    token_limit: Mapped[int] = mapped_column(
        db.Integer, 
        nullable=False,
        comment="Token 配额上限"
    )
    
    # 模型配置
    cloud_models: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="云端模型列表 [{provider: str, model: str}]"
    )
    local_models: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="本地模型列表（超额后使用） [{provider: str, model: str}]"
    )
    
    # 状态和优先级
    status: Mapped[str] = mapped_column(
        db.String(20),
        nullable=False,
        server_default="active",
        comment="配额状态"
    )
    priority: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        server_default="0",
        comment="优先级（数字越大优先级越高）"
    )
    
    # 额外配置
    extra_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="额外配置（如告警阈值、通知设置等）"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP(0)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP(0)"),
        onupdate=db.text("CURRENT_TIMESTAMP(0)")
    )
    created_by: Mapped[str] = mapped_column(StringUUID, nullable=False, comment="创建人ID")
    updated_by: Mapped[str] = mapped_column(StringUUID, nullable=False, comment="更新人ID")


class TokenQuotaUsage(db.Model):
    """
    Token 配额使用记录表
    记录每个时间窗口内的 Token 使用情况
    """
    __tablename__ = "token_quota_usages"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="token_quota_usage_pkey"),
        sa.Index("token_quota_usage_config_idx", "quota_config_id"),
        sa.Index("token_quota_usage_period_idx", "period_start", "period_end"),
        sa.Index("token_quota_usage_tenant_period_idx", "tenant_id", "period_start"),
    )

    # 基础字段
    id: Mapped[str] = mapped_column(StringUUID, server_default=db.text("uuid_generate_v4()"))
    quota_config_id: Mapped[str] = mapped_column(
        StringUUID,
        nullable=False,
        comment="关联的配额配置ID"
    )
    tenant_id: Mapped[str] = mapped_column(StringUUID, nullable=False, comment="租户ID")
    user_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, comment="用户ID")
    
    # 时间窗口
    period_start: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        comment="时间窗口开始时间"
    )
    period_end: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        comment="时间窗口结束时间"
    )
    
    # Token 使用统计
    total_tokens: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        server_default="0",
        comment="总 Token 数"
    )
    input_tokens: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        server_default="0",
        comment="输入 Token 数"
    )
    output_tokens: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        server_default="0",
        comment="输出 Token 数"
    )
    
    # 请求统计
    request_count: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        server_default="0",
        comment="请求次数"
    )
    
    # 模型使用详情
    model_usage_details: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="各模型使用详情 {model_key: {tokens: int, requests: int}}"
    )
    
    # 状态
    is_exceeded: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        server_default="false",
        comment="是否已超额"
    )
    exceeded_at: Mapped[datetime | None] = mapped_column(
        db.DateTime,
        nullable=True,
        comment="超额时间"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP(0)")
    )
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP(0)"),
        onupdate=db.text("CURRENT_TIMESTAMP(0)")
    )


class TokenQuotaLog(db.Model):
    """
    Token 配额日志表
    记录每次 Token 使用和配额检查的详细日志
    """
    __tablename__ = "token_quota_logs"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="token_quota_log_pkey"),
        sa.Index("token_quota_log_usage_idx", "usage_id"),
        sa.Index("token_quota_log_created_idx", "created_at"),
    )

    # 基础字段
    id: Mapped[str] = mapped_column(StringUUID, server_default=db.text("uuid_generate_v4()"))
    usage_id: Mapped[str] = mapped_column(
        StringUUID,
        nullable=False,
        comment="关联的使用记录ID"
    )
    tenant_id: Mapped[str] = mapped_column(StringUUID, nullable=False, comment="租户ID")
    user_id: Mapped[str | None] = mapped_column(StringUUID, nullable=True, comment="用户ID")
    
    # 请求信息
    request_id: Mapped[str | None] = mapped_column(
        db.String(255),
        nullable=True,
        comment="请求ID（用于追踪）"
    )
    model_provider: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        comment="模型提供商"
    )
    model_name: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        comment="模型名称"
    )
    
    # Token 使用
    tokens_used: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        comment="本次使用的 Token 数"
    )
    tokens_before: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        comment="使用前的累计 Token 数"
    )
    tokens_after: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        comment="使用后的累计 Token 数"
    )
    
    # 配额检查结果
    quota_limit: Mapped[int] = mapped_column(
        db.Integer,
        nullable=False,
        comment="配额上限"
    )
    is_within_quota: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        comment="是否在配额内"
    )
    switched_to_local: Mapped[bool] = mapped_column(
        db.Boolean,
        nullable=False,
        server_default="false",
        comment="是否切换到本地模型"
    )
    
    # 额外信息
    extra_info: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="额外信息"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP(0)")
    )
