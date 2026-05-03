from typing import Any

from werkzeug.exceptions import NotFound

from libs.desktop_auth import get_account_sso_tags
from libs.login import current_account_with_tenant
from models.dataset import Dataset
from services.dataset_service import DatasetService
from services.tag_service import TagService


def ensure_dataset_visible(dataset: Dataset | None, current_tenant_id: str, current_user_tags: list[str]) -> Dataset:
    if dataset is None:
        raise NotFound("Dataset not found.")

    if not TagService.is_target_visible("knowledge", current_tenant_id, str(dataset.id), current_user_tags):
        raise NotFound("Dataset not found.")

    return dataset


def get_visible_dataset(dataset_id: str, current_user: Any, current_tenant_id: str | None = None) -> Dataset:
    resolved_tenant_id = current_tenant_id or getattr(current_user, "current_tenant_id", None)
    if not resolved_tenant_id:
        raise NotFound("Dataset not found.")

    current_user_tags = get_account_sso_tags(current_user, resolved_tenant_id)
    dataset = DatasetService.get_dataset(dataset_id)
    return ensure_dataset_visible(dataset, resolved_tenant_id, current_user_tags)


def get_visible_dataset_from_context(dataset_id: str) -> Dataset:
    current_user, current_tenant_id = current_account_with_tenant()
    return get_visible_dataset(dataset_id, current_user, current_tenant_id)
