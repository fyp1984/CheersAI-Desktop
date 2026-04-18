"""Inner API for Gitea configuration."""
import json
import logging

from flask import Response, request
from flask_restx import Resource, fields

from controllers.console.wraps import setup_required
from controllers.inner_api import inner_api_ns
from libs.login import current_user
from services.filebay_config_service import resolve_filebay_config

logger = logging.getLogger(__name__)

gitea_config_model = inner_api_ns.model('InnerGiteaConfig', {
    'gitea_url': fields.String(description='Gitea server URL'),
    'gitea_owner': fields.String(description='Repository owner'),
    'gitea_repo': fields.String(description='Repository name'),
    'gitea_token': fields.String(description='API token'),
})


@inner_api_ns.route('/enterprise/gitea/config')
class EnterpriseGiteaConfigApi(Resource):
    """Gitea config for backend-to-backend use."""

    method_decorators = [setup_required]

    def _resolve_identifier(self):
        """解析用户标识符（email, username, user_id）"""
        payload = request.get_json(silent=True) or {}
        for key in ("email", "username", "user_id", "identifier"):
            value = payload.get(key)
            if value is None or value == "":
                value = request.args.get(key, "").strip()
            else:
                value = str(value).strip()
            if value:
                return value

        # 如果没有提供标识符，尝试使用当前登录用户
        if getattr(current_user, "is_authenticated", False):
            current_email = getattr(current_user, "email", "") or ""
            if current_email:
                return current_email.strip()
        return ""

    def _handle_request(self):
        """处理请求"""
        identifier = self._resolve_identifier()
        if not identifier:
            return {"message": "email, username, user_id or identifier is required."}, 400

        try:
            config = resolve_filebay_config(identifier, allow_global_fallback=False, mask_token=False)
        except LookupError as exc:
            logger.warning(f"[Enterprise Gitea Config] Lookup failed for {identifier}: {exc}")
            return {"message": str(exc)}, 404
        except Exception as exc:
            logger.error(f"[Enterprise Gitea Config] Error for {identifier}: {exc}", exc_info=True)
            return {"message": f"Failed to resolve FileBay config: {str(exc)}"}, 500

        return Response(json.dumps(config.__dict__, ensure_ascii=False), mimetype="application/json")

    def get(self):
        """GET 请求"""
        return self._handle_request()

    def post(self):
        """POST 请求"""
        return self._handle_request()
