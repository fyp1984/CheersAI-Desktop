from __future__ import annotations

import json
from collections.abc import Sequence

from pydantic import BaseModel
import sqlalchemy as sa
from sqlalchemy import select

from core.model_runtime.model_providers.model_provider_factory import ModelProviderFactory
from core.plugin.entities.plugin import PluginCategory
from extensions.ext_database import db
from extensions.ext_redis import redis_client
from libs.desktop_auth import BUILTIN_ADMIN_OWNER, BUILTIN_ADMIN_USERNAMES
from models.account import Account, TenantAccountJoin
from models.global_plugin import SystemPlugin
from services.plugin.plugin_service import PluginService


class GlobalPluginCacheItem(BaseModel):
    plugin_code: str
    plugin_id: str
    plugin_unique_identifier: str
    source_tenant_id: str
    source_account_id: str | None = None
    name: str
    version: str
    description: str | None = None
    enabled: bool = True


class GlobalPluginService:
    CACHE_KEY = "global:plugins"
    CACHE_TTL = 300

    @classmethod
    def _load_enabled_records(cls) -> list[SystemPlugin]:
        stmt = select(SystemPlugin).where(SystemPlugin.enabled == sa.true())
        return list(db.session.scalars(stmt).all())

    @classmethod
    def _display_text(cls, value) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        for attr in ("zh_Hans", "en_US"):
            text = getattr(value, attr, None)
            if text:
                return text
        return ""

    @classmethod
    def refresh_cache(cls) -> list[GlobalPluginCacheItem]:
        records = cls._load_enabled_records()
        if not records:
            synced_items = cls._sync_from_builtin_admin_workspace()
            if synced_items:
                return synced_items

        items = [
            GlobalPluginCacheItem(
                plugin_code=record.plugin_code,
                plugin_id=record.plugin_id,
                plugin_unique_identifier=record.plugin_unique_identifier,
                source_tenant_id=record.source_tenant_id,
                source_account_id=record.source_account_id,
                name=record.name,
                version=record.version,
                description=record.description,
                enabled=record.enabled,
            )
            for record in records
        ]
        redis_client.setex(cls.CACHE_KEY, cls.CACHE_TTL, json.dumps([item.model_dump() for item in items]))
        return items

    @classmethod
    def _discover_builtin_admin_workspace(cls) -> tuple[str, str | None] | None:
        stmt = select(Account, TenantAccountJoin).join(
            TenantAccountJoin,
            TenantAccountJoin.account_id == Account.id,
        )
        for account, tenant_join in db.session.execute(stmt):
            config = account.custom_config_dict
            owner = str(config.get("desktop_sso_owner") or "").strip().lower()
            username = str(
                config.get("desktop_sso_username")
                or config.get("desktop_sso_preferred_username")
                or account.name
                or ""
            ).strip().lower()
            if owner == BUILTIN_ADMIN_OWNER and username in BUILTIN_ADMIN_USERNAMES:
                return tenant_join.tenant_id, account.id

        return None

    @classmethod
    def _sync_from_builtin_admin_workspace(cls) -> list[GlobalPluginCacheItem]:
        source = cls._discover_builtin_admin_workspace()
        if not source:
            return []

        source_tenant_id, source_account_id = source
        try:
            installed_plugins = PluginService.list(source_tenant_id)
        except Exception:
            return []

        plugin_unique_identifiers = sorted({
            plugin.plugin_unique_identifier
            for plugin in installed_plugins
            if plugin.declaration.category == PluginCategory.Model
        })
        if not plugin_unique_identifiers:
            return []

        try:
            return cls.sync_installed_plugins(
                source_tenant_id=source_tenant_id,
                source_account_id=source_account_id,
                plugin_unique_identifiers=plugin_unique_identifiers,
            )
        except Exception:
            return []

    @classmethod
    def list_enabled_plugins(cls) -> list[GlobalPluginCacheItem]:
        cached = redis_client.get(cls.CACHE_KEY)
        if cached:
            try:
                payload = json.loads(cached)
                items = [GlobalPluginCacheItem.model_validate(item) for item in payload]
                if items:
                    return items

                synced_items = cls._sync_from_builtin_admin_workspace()
                if synced_items:
                    return synced_items

                return items
            except Exception:
                redis_client.delete(cls.CACHE_KEY)

        return cls.refresh_cache()

    @classmethod
    def get_enabled_plugin(cls, plugin_code: str) -> GlobalPluginCacheItem | None:
        for plugin in cls.list_enabled_plugins():
            if plugin.plugin_code == plugin_code and plugin.enabled:
                return plugin
        return None

    @classmethod
    def sync_installed_plugins(
        cls,
        *,
        source_tenant_id: str,
        source_account_id: str | None,
        plugin_unique_identifiers: Sequence[str],
    ) -> list[GlobalPluginCacheItem]:
        identifier_set = set(plugin_unique_identifiers)
        plugin_model_providers = [
            plugin_model_provider
            for plugin_model_provider in ModelProviderFactory(source_tenant_id).get_plugin_model_providers()
            if plugin_model_provider.plugin_unique_identifier in identifier_set
        ]
        if not plugin_model_providers:
            raise ValueError("No model providers were discovered from the installed plugin package.")

        for plugin_model_provider in plugin_model_providers:
            declaration = plugin_model_provider.declaration
            manifest = PluginService.fetch_plugin_manifest(
                source_tenant_id,
                plugin_model_provider.plugin_unique_identifier,
            )
            existing = db.session.scalar(
                select(SystemPlugin).where(SystemPlugin.plugin_code == declaration.provider)
            )
            if not existing:
                existing = SystemPlugin(
                    plugin_code=declaration.provider,
                    plugin_id=plugin_model_provider.plugin_id,
                    plugin_unique_identifier=plugin_model_provider.plugin_unique_identifier,
                    source_tenant_id=source_tenant_id,
                    source_account_id=source_account_id,
                    name=cls._display_text(declaration.label) or manifest.name,
                    version=manifest.version,
                    description=cls._display_text(declaration.description) or cls._display_text(manifest.description),
                    enabled=True,
                )
                db.session.add(existing)
            else:
                existing.plugin_id = plugin_model_provider.plugin_id
                existing.plugin_unique_identifier = plugin_model_provider.plugin_unique_identifier
                existing.source_tenant_id = source_tenant_id
                existing.source_account_id = source_account_id
                existing.name = cls._display_text(declaration.label) or manifest.name
                existing.version = manifest.version
                existing.description = cls._display_text(declaration.description) or cls._display_text(manifest.description)
                existing.enabled = True

        db.session.commit()
        return cls.refresh_cache()
