"""
初始化默认 Token 配额配置
用于为现有租户创建默认的配额配置
"""

import logging

import click
from flask import current_app

from extensions.ext_database import db
from models.account import Tenant
from models.token_quota import TokenQuotaConfig
from services.token_quota_service import TokenQuotaService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command("init-default-quota", help="Initialize default token quota for all tenants")
@click.option(
    "--token-limit",
    default=100000,
    type=int,
    help="Daily token limit (default: 100000)",
)
@click.option(
    "--interval-type",
    default="daily",
    type=click.Choice(["hourly", "daily", "weekly", "monthly"]),
    help="Quota interval type (default: daily)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force create even if quota config already exists",
)
def init_default_quota(token_limit: int, interval_type: str, force: bool):
    """
    为所有租户初始化默认的 Token 配额配置

    Args:
        token_limit: Token 配额上限
        interval_type: 时间间隔类型
        force: 是否强制创建（即使已存在配置）
    """
    with current_app.app_context():
        # 获取所有租户
        tenants = db.session.query(Tenant).all()

        logger.info(f"Found {len(tenants)} tenants")

        # 默认的云端模型配置
        default_cloud_models = [
            {"provider": "openai", "model": "gpt-4"},
            {"provider": "openai", "model": "gpt-3.5-turbo"},
            {"provider": "anthropic", "model": "claude-3-opus"},
            {"provider": "anthropic", "model": "claude-3-sonnet"},
        ]

        # 默认的本地模型配置
        default_local_models = [
            {"provider": "ollama", "model": "llama2"},
            {"provider": "ollama", "model": "mistral"},
            {"provider": "ollama", "model": "codellama"},
        ]

        success_count = 0
        skip_count = 0
        error_count = 0

        for tenant in tenants:
            try:
                # 检查是否已存在配额配置
                existing_config = (
                    db.session.query(TokenQuotaConfig)
                    .filter_by(tenant_id=tenant.id, user_id=None, name="默认配额")
                    .first()
                )

                if existing_config and not force:
                    logger.info(f"Tenant {tenant.id} already has default quota config, skipping")
                    skip_count += 1
                    continue

                if existing_config and force:
                    logger.info(f"Tenant {tenant.id} already has default quota config, updating")
                    # 更新现有配置
                    existing_config.token_limit = token_limit
                    existing_config.interval_type = interval_type
                    existing_config.cloud_models = default_cloud_models
                    existing_config.local_models = default_local_models
                    db.session.commit()
                    success_count += 1
                    continue

                # 获取租户的第一个管理员作为创建人
                from models.account import TenantAccountJoin, TenantAccountRole

                admin_join = (
                    db.session.query(TenantAccountJoin)
                    .filter_by(tenant_id=tenant.id, role=TenantAccountRole.OWNER)
                    .first()
                )

                if not admin_join:
                    admin_join = (
                        db.session.query(TenantAccountJoin)
                        .filter_by(tenant_id=tenant.id, role=TenantAccountRole.ADMIN)
                        .first()
                    )

                if not admin_join:
                    logger.warning(f"Tenant {tenant.id} has no admin, skipping")
                    skip_count += 1
                    continue

                # 创建默认配额配置
                quota_config = TokenQuotaService.create_quota_config(
                    tenant_id=tenant.id,
                    user_id=None,  # 租户级配置
                    name="默认配额",
                    description=f"系统默认配额：每{interval_type} {token_limit:,} tokens",
                    interval_type=interval_type,
                    token_limit=token_limit,
                    cloud_models=default_cloud_models,
                    local_models=default_local_models,
                    created_by=admin_join.account_id,
                    priority=0,
                    extra_config={
                        "alert_threshold": 0.8,  # 80% 时告警
                        "auto_created": True,
                        "created_by_script": True,
                    },
                )

                logger.info(
                    f"Created default quota config for tenant {tenant.id}: "
                    f"{token_limit:,} tokens per {interval_type}"
                )
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to create quota config for tenant {tenant.id}: {e}")
                error_count += 1
                continue

        # 输出统计信息
        logger.info("=" * 60)
        logger.info("Default quota initialization completed:")
        logger.info(f"  Total tenants: {len(tenants)}")
        logger.info("  Successfully created/updated: %s", success_count)
        logger.info("  Skipped (already exists): %s", skip_count)
        logger.info("  Errors: %s", error_count)
        logger.info("=" * 60)


if __name__ == "__main__":
    # Create Flask app
    from app_factory import create_app

    app = create_app()

    with app.app_context():
        # Call the Click command
        init_default_quota()
