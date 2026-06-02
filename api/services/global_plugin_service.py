from __future__ import annotations

import json
from collections.abc import Sequence

from pydantic import BaseModel
import sqlalchemy as sa
from sqlalchemy import select

from core.model_runtime.model_providers.model_provider_factory import ModelProviderFactory
from core.plugin.entities.plugin import PluginCategory
from core.plugin.impl.plugin import PluginInstaller
from extensions.ext_database import db
from extensions.ext_redis import redis_client
from libs.desktop_auth import BUILTIN_ADMIN_OWNER, BUILTIN_ADMIN_USERNAMES
from models.account import Account, TenantAccountJoin
from models.global_plugin import SystemPlugin


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
    CACHE_KEY = "global:plugins:v2"
    CACHE_TTL = 300

    @classmethod
    def _load_enabled_records(cls) -> list[SystemPlugin]:
        stmt = select(SystemPlugin).where(SystemPlugin.enabled == sa.true())
        return list(db.session.scalars(stmt).all())

    @classmethod
    def _records_to_items(cls, records: Sequence[SystemPlugin]) -> list[GlobalPluginCacheItem]:
        return [
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

    @classmethod
    def _cache_items(cls, items: Sequence[GlobalPluginCacheItem]) -> list[GlobalPluginCacheItem]:
        cached_items = list(items)
        redis_client.setex(cls.CACHE_KEY, cls.CACHE_TTL, json.dumps([item.model_dump() for item in cached_items]))
        return cached_items

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
        synced_items = cls._sync_from_builtin_admin_workspace()
        if synced_items:
            return synced_items

        return cls._cache_items(cls._records_to_items(cls._load_enabled_records()))

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
            installed_plugins = PluginInstaller().list_plugins(source_tenant_id)
        except Exception:
            return []

        plugin_unique_identifiers = sorted({
            plugin.plugin_unique_identifier
            for plugin in installed_plugins
            if plugin.plugin_unique_identifier
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
    def _get_non_model_plugin_code(cls, plugin) -> str | None:
        declaration = plugin.declaration

        if declaration.category == PluginCategory.Tool and declaration.tool:
            return f"{plugin.plugin_id}/{declaration.tool.identity.name}"

        if declaration.category == PluginCategory.AgentStrategy and declaration.agent_strategy:
            return f"{plugin.plugin_id}/{declaration.agent_strategy.identity.name}"

        if declaration.category == PluginCategory.Datasource and declaration.datasource:
            return f"{plugin.plugin_id}/{declaration.datasource.identity.name}"

        if declaration.category == PluginCategory.Trigger and declaration.trigger:
            return f"{plugin.plugin_id}/{declaration.trigger.identity.name}"

        if declaration.category == PluginCategory.Extension:
            return plugin.plugin_id

        return None

    @classmethod
    def _upsert_system_plugin(
        cls,
        *,
        plugin_code: str,
        plugin_id: str,
        plugin_unique_identifier: str,
        source_tenant_id: str,
        source_account_id: str | None,
        name: str,
        version: str,
        description: str | None,
    ) -> None:
        existing = db.session.scalar(select(SystemPlugin).where(SystemPlugin.plugin_code == plugin_code))
        if not existing:
            db.session.add(
                SystemPlugin(
                    plugin_code=plugin_code,
                    plugin_id=plugin_id,
                    plugin_unique_identifier=plugin_unique_identifier,
                    source_tenant_id=source_tenant_id,
                    source_account_id=source_account_id,
                    name=name,
                    version=version,
                    description=description,
                    enabled=True,
                )
            )
            return

        existing.plugin_id = plugin_id
        existing.plugin_unique_identifier = plugin_unique_identifier
        existing.source_tenant_id = source_tenant_id
        existing.source_account_id = source_account_id
        existing.name = name
        existing.version = version
        existing.description = description
        existing.enabled = True

    @classmethod
    def sync_installed_plugins(
        cls,
        *,
        source_tenant_id: str,
        source_account_id: str | None,
        plugin_unique_identifiers: Sequence[str],
    ) -> list[GlobalPluginCacheItem]:
        identifier_set = set(plugin_unique_identifiers)
        installed_plugins = [
            plugin
            for plugin in PluginInstaller().list_plugins(source_tenant_id)
            if plugin.plugin_unique_identifier in identifier_set
        ]
        if not installed_plugins:
            return cls._cache_items(cls._records_to_items(cls._load_enabled_records()))

        plugin_model_providers = [
            plugin_model_provider
            for plugin_model_provider in ModelProviderFactory(source_tenant_id).get_plugin_model_providers()
            if plugin_model_provider.plugin_unique_identifier in identifier_set
        ]
        installed_plugins_by_identifier = {
            plugin.plugin_unique_identifier: plugin
            for plugin in installed_plugins
        }

        for plugin_model_provider in plugin_model_providers:
            declaration = plugin_model_provider.declaration
            installed_plugin = installed_plugins_by_identifier.get(plugin_model_provider.plugin_unique_identifier)
            cls._upsert_system_plugin(
                plugin_code=declaration.provider,
                plugin_id=plugin_model_provider.plugin_id,
                plugin_unique_identifier=plugin_model_provider.plugin_unique_identifier,
                source_tenant_id=source_tenant_id,
                source_account_id=source_account_id,
                name=cls._display_text(declaration.label)
                or (installed_plugin.name if installed_plugin else declaration.provider),
                version=installed_plugin.version if installed_plugin else getattr(declaration, "version", "") or "",
                description=cls._display_text(declaration.description)
                or (cls._display_text(installed_plugin.declaration.description) if installed_plugin else None),
            )

        synced_model_identifiers = {provider.plugin_unique_identifier for provider in plugin_model_providers}
        for plugin in installed_plugins:
            if plugin.plugin_unique_identifier in synced_model_identifiers:
                continue

            plugin_code = cls._get_non_model_plugin_code(plugin)
            if not plugin_code:
                continue

            declaration = plugin.declaration
            cls._upsert_system_plugin(
                plugin_code=plugin_code,
                plugin_id=plugin.plugin_id,
                plugin_unique_identifier=plugin.plugin_unique_identifier,
                source_tenant_id=source_tenant_id,
                source_account_id=source_account_id,
                name=cls._display_text(declaration.label) or plugin.name,
                version=plugin.version,
                description=cls._display_text(declaration.description),
            )

        db.session.commit()
        return cls._cache_items(cls._records_to_items(cls._load_enabled_records()))
