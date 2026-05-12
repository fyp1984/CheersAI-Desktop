from typing import Any

from extensions.ext_database import db
from libs.desktop_auth import get_account_sso_tags
from models import App
from services.tag_service import TagService


def get_current_user_app_tags(current_user: Any, current_tenant_id: str) -> list[str]:
    return get_account_sso_tags(current_user, current_tenant_id)


def is_app_visible_for_user(app_model: App | None, user_tags: list[str] | None) -> bool:
    if app_model is None or not getattr(app_model, "id", None) or not getattr(app_model, "tenant_id", None):
        return False

    return TagService.is_target_visible("app", str(app_model.tenant_id), str(app_model.id), user_tags)


def get_visible_app_model(
    app_id: str,
    current_user: Any,
    current_tenant_id: str,
    *,
    same_tenant_only: bool = False,
    status: str | None = "normal",
) -> App | None:
    query = db.session.query(App).where(App.id == app_id)
    if same_tenant_only:
        query = query.where(App.tenant_id == current_tenant_id)
    if status is not None:
        query = query.where(App.status == status)

    app_model = query.first()
    current_user_tags = get_current_user_app_tags(current_user, current_tenant_id)
    if not is_app_visible_for_user(app_model, current_user_tags):
        return None

    return app_model
