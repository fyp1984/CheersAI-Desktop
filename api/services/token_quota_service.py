"""
Token Quota Service
Token 配额管理服务
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import or_

from extensions.ext_database import db
from models.token_quota import (
    QuotaIntervalType,
    QuotaStatus,
    TokenQuotaConfig,
    TokenQuotaLog,
    TokenQuotaUsage,
)

logger = logging.getLogger(__name__)


class TokenQuotaService:
    """Token 配额管理服务"""

    @staticmethod
    def create_quota_config(
        tenant_id: str,
        user_id: str | None,
        name: str,
        interval_type: str,
        token_limit: int,
        cloud_models: list[dict[str, str]],
        local_models: list[dict[str, str]],
        created_by: str,
        description: str | None = None,
        interval_value: int | None = None,
        priority: int = 0,
        extra_config: dict | None = None,
    ) -> TokenQuotaConfig:
        """
        创建配额配置

        Args:
            tenant_id: 租户ID
            user_id: 用户ID（None 表示租户级配置）
            name: 配置名称
            interval_type: 时间间隔类型
            token_limit: Token 配额上限
            cloud_models: 云端模型列表
            local_models: 本地模型列表
            created_by: 创建人ID
            description: 配置描述
            interval_value: 自定义间隔值（秒）
            priority: 优先级
            extra_config: 额外配置

        Returns:
            TokenQuotaConfig: 创建的配额配置
        """
        # 验证间隔类型
        if interval_type not in [e.value for e in QuotaIntervalType]:
            raise ValueError(f"Invalid interval_type: {interval_type}")

        # 如果是自定义间隔，必须提供 interval_value
        if interval_type == QuotaIntervalType.CUSTOM and not interval_value:
            raise ValueError("interval_value is required for custom interval type")

        # 创建配额配置
        quota_config = TokenQuotaConfig(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            description=description,
            interval_type=interval_type,
            interval_value=interval_value,
            token_limit=token_limit,
            cloud_models=cloud_models,
            local_models=local_models,
            status=QuotaStatus.ACTIVE,
            priority=priority,
            extra_config=extra_config or {},
            created_by=created_by,
            updated_by=created_by,
        )

        db.session.add(quota_config)
        db.session.commit()

        logger.info(
            f"Created token quota config: {quota_config.id} for tenant: {tenant_id}, "
            f"user: {user_id}, limit: {token_limit} tokens per {interval_type}"
        )

        return quota_config

    @staticmethod
    def update_quota_config(
        config_id: str,
        updated_by: str,
        **kwargs: Any,
    ) -> TokenQuotaConfig:
        """
        更新配额配置

        Args:
            config_id: 配额配置ID
            updated_by: 更新人ID
            **kwargs: 要更新的字段

        Returns:
            TokenQuotaConfig: 更新后的配额配置
        """
        quota_config = db.session.query(TokenQuotaConfig).filter_by(id=config_id).first()
        if not quota_config:
            raise ValueError(f"Quota config not found: {config_id}")

        # 允许更新的字段
        allowed_fields = {
            "name",
            "description",
            "interval_type",
            "interval_value",
            "token_limit",
            "cloud_models",
            "local_models",
            "status",
            "priority",
            "extra_config",
        }

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(quota_config, key, value)

        quota_config.updated_by = updated_by
        db.session.commit()

        logger.info("Updated token quota config: %s", config_id)

        return quota_config

    @staticmethod
    def get_active_quota_config(
        tenant_id: str,
        user_id: str | None = None,
    ) -> TokenQuotaConfig | None:
        """
        获取激活的配额配置（优先级最高的）

        Args:
            tenant_id: 租户ID
            user_id: 用户ID

        Returns:
            TokenQuotaConfig | None: 配额配置
        """
        query = db.session.query(TokenQuotaConfig).filter(
            TokenQuotaConfig.tenant_id == tenant_id,
            TokenQuotaConfig.status == QuotaStatus.ACTIVE,
        )

        # 优先查找用户级配置，其次是租户级配置
        if user_id:
            query = query.filter(
                or_(
                    TokenQuotaConfig.user_id == user_id,
                    TokenQuotaConfig.user_id.is_(None),
                )
            )
        else:
            query = query.filter(TokenQuotaConfig.user_id.is_(None))

        # 按优先级降序排序
        quota_config = query.order_by(TokenQuotaConfig.priority.desc()).first()

        return quota_config

    @staticmethod
    def get_current_period_usage(
        quota_config: TokenQuotaConfig,
        current_time: datetime | None = None,
    ) -> TokenQuotaUsage:
        """
        获取当前时间窗口的使用记录

        Args:
            quota_config: 配额配置
            current_time: 当前时间（默认为 now）

        Returns:
            TokenQuotaUsage: 使用记录
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # 计算时间窗口
        period_start, period_end = TokenQuotaService._calculate_period(
            quota_config.interval_type,
            quota_config.interval_value,
            current_time,
        )

        # 查找或创建使用记录
        usage = (
            db.session.query(TokenQuotaUsage)
            .filter(
                TokenQuotaUsage.quota_config_id == quota_config.id,
                TokenQuotaUsage.period_start == period_start,
                TokenQuotaUsage.period_end == period_end,
            )
            .first()
        )

        if not usage:
            usage = TokenQuotaUsage(
                quota_config_id=quota_config.id,
                tenant_id=quota_config.tenant_id,
                user_id=quota_config.user_id,
                period_start=period_start,
                period_end=period_end,
                total_tokens=0,
                input_tokens=0,
                output_tokens=0,
                request_count=0,
                model_usage_details={},
                is_exceeded=False,
            )
            db.session.add(usage)
            db.session.commit()

        return usage

    @staticmethod
    def check_quota(
        tenant_id: str,
        user_id: str | None = None,
        tokens_to_use: int = 0,
    ) -> dict[str, Any]:
        """
        检查配额是否充足

        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            tokens_to_use: 预计使用的 Token 数

        Returns:
            dict: {
                "within_quota": bool,  # 是否在配额内
                "remaining_tokens": int,  # 剩余 Token 数
                "should_use_local": bool,  # 是否应该使用本地模型
                "quota_config": TokenQuotaConfig | None,
                "current_usage": TokenQuotaUsage | None,
            }
        """
        # 获取激活的配额配置
        quota_config = TokenQuotaService.get_active_quota_config(tenant_id, user_id)

        if not quota_config:
            # 没有配额限制
            return {
                "within_quota": True,
                "remaining_tokens": float("inf"),
                "should_use_local": False,
                "quota_config": None,
                "current_usage": None,
            }

        # 获取当前时间窗口的使用记录
        current_usage = TokenQuotaService.get_current_period_usage(quota_config)

        # 计算剩余配额
        remaining_tokens = quota_config.token_limit - current_usage.total_tokens
        within_quota = remaining_tokens >= tokens_to_use

        # 判断是否应该使用本地模型
        should_use_local = not within_quota or current_usage.is_exceeded

        return {
            "within_quota": within_quota,
            "remaining_tokens": max(0, remaining_tokens),
            "should_use_local": should_use_local,
            "quota_config": quota_config,
            "current_usage": current_usage,
        }

    @staticmethod
    def record_token_usage(
        tenant_id: str,
        model_provider: str,
        model_name: str,
        tokens_used: int,
        user_id: str | None = None,
        request_id: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        extra_info: dict | None = None,
    ) -> TokenQuotaLog | None:
        """
        记录 Token 使用

        Args:
            tenant_id: 租户ID
            model_provider: 模型提供商
            model_name: 模型名称
            tokens_used: 使用的 Token 数
            user_id: 用户ID
            request_id: 请求ID
            input_tokens: 输入 Token 数
            output_tokens: 输出 Token 数
            extra_info: 额外信息

        Returns:
            TokenQuotaLog | None: 日志记录
        """
        # 获取激活的配额配置
        quota_config = TokenQuotaService.get_active_quota_config(tenant_id, user_id)

        if not quota_config:
            # 没有配额限制，不记录
            return None

        # 获取当前时间窗口的使用记录
        current_usage = TokenQuotaService.get_current_period_usage(quota_config)

        # 记录使用前的 Token 数
        tokens_before = current_usage.total_tokens

        # 更新使用记录
        current_usage.total_tokens += tokens_used
        current_usage.input_tokens += input_tokens
        current_usage.output_tokens += output_tokens
        current_usage.request_count += 1

        # 更新模型使用详情
        model_key = f"{model_provider}/{model_name}"
        if model_key not in current_usage.model_usage_details:
            current_usage.model_usage_details[model_key] = {"tokens": 0, "requests": 0}

        current_usage.model_usage_details[model_key]["tokens"] += tokens_used
        current_usage.model_usage_details[model_key]["requests"] += 1

        # 检查是否超额
        if not current_usage.is_exceeded and current_usage.total_tokens >= quota_config.token_limit:
            current_usage.is_exceeded = True
            current_usage.exceeded_at = datetime.utcnow()
            logger.warning(
                f"Token quota exceeded for tenant: {tenant_id}, user: {user_id}, "
                f"usage: {current_usage.total_tokens}/{quota_config.token_limit}"
            )

        # 标记为脏数据，确保更新
        db.session.add(current_usage)

        # 创建日志记录
        quota_log = TokenQuotaLog(
            usage_id=current_usage.id,
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            model_provider=model_provider,
            model_name=model_name,
            tokens_used=tokens_used,
            tokens_before=tokens_before,
            tokens_after=current_usage.total_tokens,
            quota_limit=quota_config.token_limit,
            is_within_quota=current_usage.total_tokens <= quota_config.token_limit,
            switched_to_local=current_usage.is_exceeded,
            extra_info=extra_info or {},
        )

        db.session.add(quota_log)
        db.session.commit()

        logger.info(
            f"Recorded token usage: {tokens_used} tokens for {model_provider}/{model_name}, "
            f"total: {current_usage.total_tokens}/{quota_config.token_limit}"
        )

        return quota_log

    @staticmethod
    def get_quota_statistics(
        tenant_id: str,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        获取配额统计信息

        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            dict: 统计信息
        """
        query = db.session.query(TokenQuotaUsage).filter(TokenQuotaUsage.tenant_id == tenant_id)

        if user_id:
            query = query.filter(TokenQuotaUsage.user_id == user_id)

        if start_date:
            query = query.filter(TokenQuotaUsage.period_start >= start_date)

        if end_date:
            query = query.filter(TokenQuotaUsage.period_end <= end_date)

        usages = query.all()

        # 统计数据
        total_tokens = sum(usage.total_tokens for usage in usages)
        total_requests = sum(usage.request_count for usage in usages)
        exceeded_periods = sum(1 for usage in usages if usage.is_exceeded)

        # 模型使用统计
        model_stats: dict[str, dict[str, int]] = {}
        for usage in usages:
            for model_key, details in usage.model_usage_details.items():
                if model_key not in model_stats:
                    model_stats[model_key] = {"tokens": 0, "requests": 0}
                model_stats[model_key]["tokens"] += details.get("tokens", 0)
                model_stats[model_key]["requests"] += details.get("requests", 0)

        return {
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "total_periods": len(usages),
            "exceeded_periods": exceeded_periods,
            "model_statistics": model_stats,
        }

    @staticmethod
    def _calculate_period(
        interval_type: str,
        interval_value: int | None,
        current_time: datetime,
    ) -> tuple[datetime, datetime]:
        """
        计算时间窗口的开始和结束时间

        Args:
            interval_type: 时间间隔类型
            interval_value: 自定义间隔值（秒）
            current_time: 当前时间

        Returns:
            tuple[datetime, datetime]: (period_start, period_end)
        """
        if interval_type == QuotaIntervalType.HOURLY:
            period_start = current_time.replace(minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(hours=1)

        elif interval_type == QuotaIntervalType.DAILY:
            period_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)

        elif interval_type == QuotaIntervalType.WEEKLY:
            # 周一作为一周的开始
            days_since_monday = current_time.weekday()
            period_start = (current_time - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            period_end = period_start + timedelta(weeks=1)

        elif interval_type == QuotaIntervalType.MONTHLY:
            period_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # 下个月的第一天
            if current_time.month == 12:
                period_end = period_start.replace(year=current_time.year + 1, month=1)
            else:
                period_end = period_start.replace(month=current_time.month + 1)

        elif interval_type == QuotaIntervalType.CUSTOM:
            if not interval_value:
                raise ValueError("interval_value is required for custom interval type")
            # 计算当前时间在哪个时间窗口内
            epoch = datetime(1970, 1, 1)
            seconds_since_epoch = int((current_time - epoch).total_seconds())
            period_index = seconds_since_epoch // interval_value
            period_start = epoch + timedelta(seconds=period_index * interval_value)
            period_end = period_start + timedelta(seconds=interval_value)

        else:
            raise ValueError(f"Invalid interval_type: {interval_type}")

        return period_start, period_end

    @staticmethod
    def reset_quota(
        tenant_id: str,
        user_id: str | None = None,
    ) -> bool:
        """
        重置配额（清除当前时间窗口的使用记录）

        Args:
            tenant_id: 租户ID
            user_id: 用户ID

        Returns:
            bool: 是否成功
        """
        quota_config = TokenQuotaService.get_active_quota_config(tenant_id, user_id)

        if not quota_config:
            return False

        current_usage = TokenQuotaService.get_current_period_usage(quota_config)

        # 重置使用记录
        current_usage.total_tokens = 0
        current_usage.input_tokens = 0
        current_usage.output_tokens = 0
        current_usage.request_count = 0
        current_usage.model_usage_details = {}
        current_usage.is_exceeded = False
        current_usage.exceeded_at = None

        db.session.commit()

        logger.info("Reset token quota for tenant: %s, user: %s", tenant_id, user_id)

        return True
