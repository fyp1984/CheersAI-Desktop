"""Shared helpers for user-scoped FileBay configuration."""

from __future__ import annotations

import logging
from typing import Any

from extensions.ext_database import db
from models.account import Account
from services.filebay_config_service import resolve_filebay_config

logger = logging.getLogger(__name__)


def mask_gitea_token(token: str) -> str:
    """Mask a token for safe UI display."""
    if not token:
        return ""
    if len(token) <= 8:
        return "****"
    return f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"


def is_masked_gitea_token(token: str) -> bool:
    """Treat any value containing '*' as a masked UI token placeholder."""
    return bool(token) and "*" in token


def build_filebay_config_dict(
    *,
    gitea_url: str,
    gitea_owner: str,
    gitea_repo: str,
    gitea_token: str,
    gitea_path: str | None = None,
    mask_token: bool = False,
) -> dict[str, str]:
    config = {
        "gitea_url": gitea_url or "",
        "gitea_owner": gitea_owner or "",
        "gitea_repo": gitea_repo or "",
        "gitea_token": mask_gitea_token(gitea_token or "") if mask_token else (gitea_token or ""),
    }
    if gitea_path is not None:
        config["gitea_path"] = gitea_path or ""
    return config


def has_complete_filebay_config(config: dict[str, Any] | None) -> bool:
    """Return True when a config contains the fields needed for user-scoped FileBay access."""
    if not config:
        return False

    required_keys = ("gitea_url", "gitea_owner", "gitea_repo", "gitea_token")
    for key in required_keys:
        value = config.get(key)
        if not isinstance(value, str) or not value.strip():
            return False

    return not is_masked_gitea_token(config["gitea_token"].strip())


def get_account_filebay_config(account: Account | None, *, mask_token: bool = False) -> dict[str, str] | None:
    """Read FileBay config from account.custom_config_dict if present."""
    if not account or not account.custom_config_dict:
        return None

    user_config = account.custom_config_dict
    if not has_complete_filebay_config(user_config):
        return None

    return build_filebay_config_dict(
        gitea_url=user_config.get("gitea_url", ""),
        gitea_owner=user_config.get("gitea_owner", ""),
        gitea_repo=user_config.get("gitea_repo", ""),
        gitea_token=user_config.get("gitea_token", ""),
        gitea_path=user_config.get("gitea_path"),
        mask_token=mask_token,
    )


def sync_account_filebay_config(account: Account | None, config: dict[str, Any]) -> bool:
    """Persist resolved FileBay config onto the account when it is missing or stale."""
    if not account or not has_complete_filebay_config(config):
        return False

    merged = merge_account_filebay_config(account.custom_config_dict, config)
    if merged == (account.custom_config_dict or {}):
        return False

    account.custom_config_dict = merged
    db.session.commit()
    return True


def resolve_user_filebay_config(
    identifier: str | None,
    *,
    account: Account | None = None,
    mask_token: bool = False,
    allow_global_fallback: bool = False,
    log_prefix: str = "[FileBay Config]",
) -> dict[str, str] | None:
    """Resolve a user's FileBay config without going through an HTTP self-call."""
    normalized_identifier = (identifier or "").strip()
    if not account and normalized_identifier:
        account = db.session.query(Account).filter_by(email=normalized_identifier).first()

    if normalized_identifier:
        try:
            config = resolve_filebay_config(
                normalized_identifier,
                allow_global_fallback=allow_global_fallback,
                mask_token=False,
                refresh_account_config=True,
            )
            if config.gitea_url:
                logger.info("%s Resolved user-scoped FileBay config for %s", log_prefix, normalized_identifier)
                resolved_config = build_filebay_config_dict(
                    gitea_url=config.gitea_url,
                    gitea_owner=config.gitea_owner,
                    gitea_repo=config.gitea_repo,
                    gitea_token=config.gitea_token,
                )
                if account and not allow_global_fallback:
                    sync_account_filebay_config(account, resolved_config)

                return build_filebay_config_dict(
                    gitea_url=resolved_config["gitea_url"],
                    gitea_owner=resolved_config["gitea_owner"],
                    gitea_repo=resolved_config["gitea_repo"],
                    gitea_token=resolved_config["gitea_token"],
                    gitea_path=resolved_config.get("gitea_path"),
                    mask_token=mask_token,
                )
        except LookupError as exc:
            logger.warning("%s Resolve failed for %s: %s", log_prefix, normalized_identifier, exc)
        except Exception as exc:
            logger.warning("%s Unexpected resolve error for %s: %s", log_prefix, normalized_identifier, exc)

    account_config = get_account_filebay_config(account, mask_token=mask_token)
    if account_config:
        logger.info("%s Falling back to persisted account FileBay config", log_prefix)
        return account_config

    return None


def merge_account_filebay_config(existing_config: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Merge FileBay fields into account.custom_config_dict without destroying unrelated keys."""
    merged = dict(existing_config or {})

    for key in ("gitea_url", "gitea_owner", "gitea_repo"):
        value = update.get(key)
        if isinstance(value, str):
            merged[key] = value

    if "gitea_path" in update:
        value = update.get("gitea_path")
        if value is None:
            merged.pop("gitea_path", None)
        elif isinstance(value, str):
            merged["gitea_path"] = value

    token = update.get("gitea_token")
    if isinstance(token, str):
        normalized_token = token.strip()
        if normalized_token and not is_masked_gitea_token(normalized_token):
            merged["gitea_token"] = normalized_token

    return merged
