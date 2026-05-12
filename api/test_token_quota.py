"""
Token 配额系统测试脚本
用于验证配额系统的基本功能
"""

import logging

import click
from flask import current_app

from extensions.ext_database import db
from models.account import Account, Tenant
from services.token_quota_service import TokenQuotaService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command("test-token-quota", help="Test token quota system")
def test_token_quota():
    """测试 Token 配额系统的基本功能"""
    with current_app.app_context():
        logger.info("=" * 60)
        logger.info("开始测试 Token 配额系统")
        logger.info("=" * 60)

        # 获取第一个租户和用户用于测试
        tenant = db.session.query(Tenant).first()
        if not tenant:
            logger.error("没有找到租户，请先创建租户")
            return

        from models.account import TenantAccountJoin

        account_join = db.session.query(TenantAccountJoin).filter_by(tenant_id=tenant.id).first()
        if not account_join:
            logger.error("没有找到用户，请先创建用户")
            return

        account = db.session.query(Account).filter_by(id=account_join.account_id).first()

        logger.info(f"使用租户: {tenant.id}")
        logger.info(f"使用用户: {account.id} ({account.email})")
        logger.info("")

        # 测试 1: 创建配额配置
        logger.info("测试 1: 创建配额配置")
        logger.info("-" * 60)
        try:
            quota_config = TokenQuotaService.create_quota_config(
                tenant_id=tenant.id,
                user_id=None,
                name="测试配额",
                description="用于测试的配额配置",
                interval_type="daily",
                token_limit=10000,
                cloud_models=[
                    {"provider": "openai", "model": "gpt-4"},
                    {"provider": "openai", "model": "gpt-3.5-turbo"},
                ],
                local_models=[
                    {"provider": "ollama", "model": "llama2"},
                    {"provider": "ollama", "model": "mistral"},
                ],
                created_by=account.id,
                priority=0,
            )
            logger.info(f"✅ 配额配置创建成功: {quota_config.id}")
            logger.info(f"   配额上限: {quota_config.token_limit:,} tokens")
            logger.info(f"   时间间隔: {quota_config.interval_type}")
            logger.info(f"   云端模型: {len(quota_config.cloud_models)} 个")
            logger.info(f"   本地模型: {len(quota_config.local_models)} 个")
        except Exception as e:
            logger.error("❌ 创建配额配置失败: %s", e)
            return

        logger.info("")

        # 测试 2: 检查配额
        logger.info("测试 2: 检查配额（初始状态）")
        logger.info("-" * 60)
        try:
            quota_check = TokenQuotaService.check_quota(
                tenant_id=tenant.id, user_id=None, tokens_to_use=1000
            )
            logger.info("✅ 配额检查成功")
            logger.info(f"   是否在配额内: {quota_check['within_quota']}")
            logger.info(f"   剩余 Token: {quota_check['remaining_tokens']:,}")
            logger.info(f"   是否应使用本地模型: {quota_check['should_use_local']}")
        except Exception as e:
            logger.error("❌ 检查配额失败: %s", e)
            return

        logger.info("")

        # 测试 3: 记录 Token 使用
        logger.info("测试 3: 记录 Token 使用")
        logger.info("-" * 60)
        try:
            # 模拟多次使用
            for i in range(5):
                quota_log = TokenQuotaService.record_token_usage(
                    tenant_id=tenant.id,
                    user_id=None,
                    model_provider="openai",
                    model_name="gpt-4",
                    tokens_used=1000,
                    input_tokens=700,
                    output_tokens=300,
                    request_id=f"test_request_{i + 1}",
                )
                logger.info(
                    f"   记录 #{i + 1}: 使用 1,000 tokens, "
                    f"累计: {quota_log.tokens_after:,}/{quota_log.quota_limit:,}"
                )
            logger.info("✅ Token 使用记录成功")
        except Exception as e:
            logger.error("❌ 记录 Token 使用失败: %s", e)
            return

        logger.info("")

        # 测试 4: 再次检查配额
        logger.info("测试 4: 检查配额（使用后）")
        logger.info("-" * 60)
        try:
            quota_check = TokenQuotaService.check_quota(
                tenant_id=tenant.id, user_id=None, tokens_to_use=1000
            )
            logger.info("✅ 配额检查成功")
            logger.info(f"   是否在配额内: {quota_check['within_quota']}")
            logger.info(f"   剩余 Token: {quota_check['remaining_tokens']:,}")
            logger.info(f"   是否应使用本地模型: {quota_check['should_use_local']}")
        except Exception as e:
            logger.error("❌ 检查配额失败: %s", e)
            return

        logger.info("")

        # 测试 5: 模拟超额使用
        logger.info("测试 5: 模拟超额使用")
        logger.info("-" * 60)
        try:
            # 使用大量 Token 以超过配额
            remaining = quota_check["remaining_tokens"]
            tokens_to_use = remaining + 1000

            quota_log = TokenQuotaService.record_token_usage(
                tenant_id=tenant.id,
                user_id=None,
                model_provider="openai",
                model_name="gpt-4",
                tokens_used=tokens_to_use,
                input_tokens=int(tokens_to_use * 0.7),
                output_tokens=int(tokens_to_use * 0.3),
                request_id="test_exceed",
            )
            logger.info(f"   使用 {tokens_to_use:,} tokens")
            logger.info(f"   累计: {quota_log.tokens_after:,}/{quota_log.quota_limit:,}")
            logger.info(f"   是否在配额内: {quota_log.is_within_quota}")
            logger.info(f"   是否切换到本地: {quota_log.switched_to_local}")
            logger.info("✅ 超额使用测试成功")
        except Exception as e:
            logger.error("❌ 超额使用测试失败: %s", e)
            return

        logger.info("")

        # 测试 6: 检查超额后的配额
        logger.info("测试 6: 检查配额（超额后）")
        logger.info("-" * 60)
        try:
            quota_check = TokenQuotaService.check_quota(
                tenant_id=tenant.id, user_id=None, tokens_to_use=1000
            )
            logger.info("✅ 配额检查成功")
            logger.info(f"   是否在配额内: {quota_check['within_quota']}")
            logger.info(f"   剩余 Token: {quota_check['remaining_tokens']:,}")
            logger.info(f"   是否应使用本地模型: {quota_check['should_use_local']}")
            if quota_check["should_use_local"]:
                logger.info("   ⚠️  配额已用完，应切换到本地模型")
        except Exception as e:
            logger.error("❌ 检查配额失败: %s", e)
            return

        logger.info("")

        # 测试 7: 获取统计信息
        logger.info("测试 7: 获取统计信息")
        logger.info("-" * 60)
        try:
            statistics = TokenQuotaService.get_quota_statistics(
                tenant_id=tenant.id, user_id=None
            )
            logger.info("✅ 统计信息获取成功")
            logger.info(f"   总 Token 数: {statistics['total_tokens']:,}")
            logger.info(f"   总请求数: {statistics['total_requests']:,}")
            logger.info(f"   总时间段数: {statistics['total_periods']}")
            logger.info(f"   超额时间段数: {statistics['exceeded_periods']}")
            logger.info("   模型统计:")
            for model_key, stats in statistics["model_statistics"].items():
                logger.info(f"     - {model_key}: {stats['tokens']:,} tokens, {stats['requests']} 请求")
        except Exception as e:
            logger.error("❌ 获取统计信息失败: %s", e)
            return

        logger.info("")

        # 测试 8: 重置配额
        logger.info("测试 8: 重置配额")
        logger.info("-" * 60)
        try:
            success = TokenQuotaService.reset_quota(tenant_id=tenant.id, user_id=None)
            if success:
                logger.info("✅ 配额重置成功")

                # 验证重置后的状态
                quota_check = TokenQuotaService.check_quota(
                    tenant_id=tenant.id, user_id=None, tokens_to_use=0
                )
                logger.info(f"   重置后剩余 Token: {quota_check['remaining_tokens']:,}")
                logger.info(f"   是否应使用本地模型: {quota_check['should_use_local']}")
            else:
                logger.error("❌ 配额重置失败")
        except Exception as e:
            logger.error("❌ 重置配额失败: %s", e)
            return

        logger.info("")

        # 清理测试数据
        logger.info("清理测试数据")
        logger.info("-" * 60)
        try:
            from models.token_quota import TokenQuotaConfig, TokenQuotaLog, TokenQuotaUsage

            # 删除测试创建的配额配置和相关数据
            db.session.query(TokenQuotaLog).filter(
                TokenQuotaLog.tenant_id == tenant.id
            ).delete()
            db.session.query(TokenQuotaUsage).filter(
                TokenQuotaUsage.tenant_id == tenant.id
            ).delete()
            db.session.query(TokenQuotaConfig).filter(
                TokenQuotaConfig.id == quota_config.id
            ).delete()
            db.session.commit()
            logger.info("✅ 测试数据清理成功")
        except Exception as e:
            logger.error("❌ 清理测试数据失败: %s", e)
            db.session.rollback()

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ 所有测试完成！Token 配额系统工作正常")
        logger.info("=" * 60)


if __name__ == "__main__":
    from dify_app import DifyApp

    app = DifyApp("app").create()
    with app.app_context():
        test_token_quota()
