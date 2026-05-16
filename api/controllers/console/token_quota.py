"""
Token Quota API Controllers
Token 配额管理 API 接口
"""

import logging
from datetime import datetime

from flask import request
from flask_login import current_user, login_required
from flask_restx import Namespace, Resource, fields
from werkzeug.exceptions import Forbidden

from controllers.console import api
from controllers.console.wraps import account_initialization_required
from libs.desktop_auth import has_any_workspace_capability
from libs.helper import TimestampField
from models.token_quota import QuotaIntervalType, QuotaStatus
from services.token_quota_service import TokenQuotaService

logger = logging.getLogger(__name__)
TEAM_TOKEN_QUOTA_MANAGE_CAPABILITIES = (
    "desktop_settings_team",
    "desktop_model_manage",
    "desktop_model_provider_manage",
)

# 创建命名空间
ns = Namespace("token-quota", description="Token 配额管理")
api.add_namespace(ns)


def _require_token_quota_manage_capability() -> None:
    if not has_any_workspace_capability(
        current_user,
        TEAM_TOKEN_QUOTA_MANAGE_CAPABILITIES,
        current_user.current_tenant_id,
    ):
        raise Forbidden("You do not have permission to manage token quota.")

# 定义数据模型
model_info_model = api.model(
    "ModelInfo",
    {
        "provider": fields.String(required=True, description="模型提供商"),
        "model": fields.String(required=True, description="模型名称"),
    },
)

quota_config_model = api.model(
    "TokenQuotaConfig",
    {
        "id": fields.String(description="配额配置ID"),
        "tenant_id": fields.String(description="租户ID"),
        "user_id": fields.String(description="用户ID"),
        "name": fields.String(required=True, description="配置名称"),
        "description": fields.String(description="配置描述"),
        "interval_type": fields.String(
            required=True,
            description="时间间隔类型",
            enum=[e.value for e in QuotaIntervalType],
        ),
        "interval_value": fields.Integer(description="自定义间隔值（秒）"),
        "token_limit": fields.Integer(required=True, description="Token 配额上限"),
        "cloud_models": fields.List(fields.Nested(model_info_model), description="云端模型列表"),
        "local_models": fields.List(fields.Nested(model_info_model), description="本地模型列表"),
        "status": fields.String(description="配额状态", enum=[e.value for e in QuotaStatus]),
        "priority": fields.Integer(description="优先级"),
        "extra_config": fields.Raw(description="额外配置"),
        "created_at": TimestampField(description="创建时间"),
        "updated_at": TimestampField(description="更新时间"),
    },
)

quota_usage_model = api.model(
    "TokenQuotaUsage",
    {
        "id": fields.String(description="使用记录ID"),
        "quota_config_id": fields.String(description="配额配置ID"),
        "period_start": TimestampField(description="时间窗口开始"),
        "period_end": TimestampField(description="时间窗口结束"),
        "total_tokens": fields.Integer(description="总 Token 数"),
        "input_tokens": fields.Integer(description="输入 Token 数"),
        "output_tokens": fields.Integer(description="输出 Token 数"),
        "request_count": fields.Integer(description="请求次数"),
        "model_usage_details": fields.Raw(description="模型使用详情"),
        "is_exceeded": fields.Boolean(description="是否已超额"),
        "exceeded_at": TimestampField(description="超额时间"),
    },
)

quota_check_result_model = api.model(
    "QuotaCheckResult",
    {
        "within_quota": fields.Boolean(description="是否在配额内"),
        "remaining_tokens": fields.Integer(description="剩余 Token 数"),
        "should_use_local": fields.Boolean(description="是否应该使用本地模型"),
        "quota_config": fields.Nested(quota_config_model, allow_null=True),
        "current_usage": fields.Nested(quota_usage_model, allow_null=True),
    },
)


@ns.route("/configs")
class TokenQuotaConfigListApi(Resource):
    """Token 配额配置列表 API"""

    @login_required
    @account_initialization_required
    @ns.doc("list_quota_configs")
    @ns.marshal_list_with(quota_config_model)
    def get(self):
        """获取配额配置列表"""
        _require_token_quota_manage_capability()
        tenant_id = current_user.current_tenant_id

        from models.token_quota import TokenQuotaConfig

        configs = (
            TokenQuotaConfig.query.filter_by(tenant_id=tenant_id)
            .order_by(TokenQuotaConfig.priority.desc(), TokenQuotaConfig.created_at.desc())
            .all()
        )

        return configs

    @login_required
    @account_initialization_required
    @ns.doc("create_quota_config")
    @ns.expect(quota_config_model)
    @ns.marshal_with(quota_config_model, code=201)
    def post(self):
        """创建配额配置"""
        _require_token_quota_manage_capability()
        tenant_id = current_user.current_tenant_id
        user_id = current_user.id
        data = request.get_json()

        try:
            quota_config = TokenQuotaService.create_quota_config(
                tenant_id=tenant_id,
                user_id=data.get("user_id"),  # 可以为其他用户创建配置
                name=data["name"],
                interval_type=data["interval_type"],
                token_limit=data["token_limit"],
                cloud_models=data.get("cloud_models", []),
                local_models=data.get("local_models", []),
                created_by=user_id,
                description=data.get("description"),
                interval_value=data.get("interval_value"),
                priority=data.get("priority", 0),
                extra_config=data.get("extra_config"),
            )

            return quota_config, 201

        except ValueError as e:
            return {"message": str(e)}, 400
        except Exception as e:
            logger.exception("Failed to create quota config")
            return {"message": f"Failed to create quota config: {str(e)}"}, 500


@ns.route("/configs/<string:config_id>")
class TokenQuotaConfigApi(Resource):
    """Token 配额配置详情 API"""

    @login_required
    @account_initialization_required
    @ns.doc("get_quota_config")
    @ns.marshal_with(quota_config_model)
    def get(self, config_id):
        """获取配额配置详情"""
        _require_token_quota_manage_capability()
        from models.token_quota import TokenQuotaConfig

        quota_config = TokenQuotaConfig.query.filter_by(
            id=config_id, tenant_id=current_user.current_tenant_id
        ).first()

        if not quota_config:
            return {"message": "Quota config not found"}, 404

        return quota_config

    @login_required
    @account_initialization_required
    @ns.doc("update_quota_config")
    @ns.expect(quota_config_model)
    @ns.marshal_with(quota_config_model)
    def put(self, config_id):
        """更新配额配置"""
        _require_token_quota_manage_capability()
        from models.token_quota import TokenQuotaConfig

        quota_config = TokenQuotaConfig.query.filter_by(
            id=config_id, tenant_id=current_user.current_tenant_id
        ).first()

        if not quota_config:
            return {"message": "Quota config not found"}, 404

        data = request.get_json()

        try:
            updated_config = TokenQuotaService.update_quota_config(
                config_id=config_id, updated_by=current_user.id, **data
            )

            return updated_config

        except ValueError as e:
            return {"message": str(e)}, 400
        except Exception as e:
            logger.exception("Failed to update quota config")
            return {"message": f"Failed to update quota config: {str(e)}"}, 500

    @login_required
    @account_initialization_required
    @ns.doc("delete_quota_config")
    def delete(self, config_id):
        """删除配额配置"""
        _require_token_quota_manage_capability()
        from extensions.ext_database import db
        from models.token_quota import TokenQuotaConfig

        quota_config = TokenQuotaConfig.query.filter_by(
            id=config_id, tenant_id=current_user.current_tenant_id
        ).first()

        if not quota_config:
            return {"message": "Quota config not found"}, 404

        try:
            db.session.delete(quota_config)
            db.session.commit()

            return {"message": "Quota config deleted successfully"}, 200

        except Exception as e:
            logger.exception("Failed to delete quota config")
            db.session.rollback()
            return {"message": f"Failed to delete quota config: {str(e)}"}, 500


@ns.route("/check")
class TokenQuotaCheckApi(Resource):
    """Token 配额检查 API"""

    @login_required
    @account_initialization_required
    @ns.doc("check_quota")
    @ns.marshal_with(quota_check_result_model)
    def post(self):
        """检查配额是否充足"""
        tenant_id = current_user.current_tenant_id
        data = request.get_json() or {}

        user_id = data.get("user_id")  # 可选，检查特定用户的配额
        tokens_to_use = data.get("tokens_to_use", 0)

        try:
            result = TokenQuotaService.check_quota(
                tenant_id=tenant_id, user_id=user_id, tokens_to_use=tokens_to_use
            )

            return result

        except Exception as e:
            logger.exception("Failed to check quota")
            return {"message": f"Failed to check quota: {str(e)}"}, 500


@ns.route("/usage/current")
class TokenQuotaCurrentUsageApi(Resource):
    """当前时间窗口使用情况 API"""

    @login_required
    @account_initialization_required
    @ns.doc("get_current_usage")
    @ns.marshal_with(quota_usage_model)
    def get(self):
        """获取当前时间窗口的使用情况"""
        tenant_id = current_user.current_tenant_id
        user_id = request.args.get("user_id")  # 可选

        try:
            quota_config = TokenQuotaService.get_active_quota_config(tenant_id, user_id)

            if not quota_config:
                return {"message": "No active quota config found"}, 404

            current_usage = TokenQuotaService.get_current_period_usage(quota_config)

            return current_usage

        except Exception as e:
            logger.exception("Failed to get current usage")
            return {"message": f"Failed to get current usage: {str(e)}"}, 500


@ns.route("/usage/statistics")
class TokenQuotaStatisticsApi(Resource):
    """配额统计 API"""

    @login_required
    @account_initialization_required
    @ns.doc("get_quota_statistics")
    def get(self):
        """获取配额统计信息"""
        _require_token_quota_manage_capability()
        tenant_id = current_user.current_tenant_id
        user_id = request.args.get("user_id")  # 可选
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        # 解析日期
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else None

        try:
            statistics = TokenQuotaService.get_quota_statistics(
                tenant_id=tenant_id, user_id=user_id, start_date=start_date, end_date=end_date
            )

            return statistics

        except Exception as e:
            logger.exception("Failed to get quota statistics")
            return {"message": f"Failed to get quota statistics: {str(e)}"}, 500


@ns.route("/usage/record")
class TokenQuotaRecordApi(Resource):
    """记录 Token 使用 API"""

    @login_required
    @account_initialization_required
    @ns.doc("record_token_usage")
    def post(self):
        """记录 Token 使用"""
        _require_token_quota_manage_capability()
        tenant_id = current_user.current_tenant_id
        data = request.get_json()

        try:
            quota_log = TokenQuotaService.record_token_usage(
                tenant_id=tenant_id,
                model_provider=data["model_provider"],
                model_name=data["model_name"],
                tokens_used=data["tokens_used"],
                user_id=data.get("user_id"),
                request_id=data.get("request_id"),
                input_tokens=data.get("input_tokens", 0),
                output_tokens=data.get("output_tokens", 0),
                extra_info=data.get("extra_info"),
            )

            if quota_log:
                return {
                    "message": "Token usage recorded successfully",
                    "log_id": quota_log.id,
                    "is_within_quota": quota_log.is_within_quota,
                    "switched_to_local": quota_log.switched_to_local,
                }, 201
            else:
                return {"message": "No quota config found, usage not recorded"}, 200

        except KeyError as e:
            return {"message": f"Missing required field: {str(e)}"}, 400
        except Exception as e:
            logger.exception("Failed to record token usage")
            return {"message": f"Failed to record token usage: {str(e)}"}, 500


@ns.route("/reset")
class TokenQuotaResetApi(Resource):
    """重置配额 API"""

    @login_required
    @account_initialization_required
    @ns.doc("reset_quota")
    def post(self):
        """重置配额（清除当前时间窗口的使用记录）"""
        _require_token_quota_manage_capability()
        tenant_id = current_user.current_tenant_id
        data = request.get_json() or {}
        user_id = data.get("user_id")  # 可选

        try:
            success = TokenQuotaService.reset_quota(tenant_id=tenant_id, user_id=user_id)

            if success:
                return {"message": "Quota reset successfully"}, 200
            else:
                return {"message": "No active quota config found"}, 404

        except Exception as e:
            logger.exception("Failed to reset quota")
            return {"message": f"Failed to reset quota: {str(e)}"}, 500
