from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select

from core.helper.team_model_encrypter import decrypt_api_key, encrypt_api_key
from core.model_runtime.entities.provider_entities import FormType, ProviderEntity
from core.model_runtime.model_providers.model_provider_factory import ModelProviderFactory
from extensions.ext_database import db
from extensions.ext_redis import redis_client
from models.global_plugin import TeamModelConfig
from services.global_plugin_service import GlobalPluginCacheItem, GlobalPluginService


@dataclass
class TeamModelBinding:
    plugin: GlobalPluginCacheItem
    config: TeamModelConfig
    credentials: dict[str, Any]


class TeamModelConfigService:
    CACHE_TTL = 300
    API_KEY_KEYWORDS = ("api_key", "apikey", "token", "secret")
    BASE_URL_KEYWORDS = ("base_url", "api_base", "api_url", "endpoint", "host", "url")

    @classmethod
    def _cache_key(cls, team_id: str, plugin_code: str) -> str:
        return f"team:{team_id}:model:{plugin_code}"

    @classmethod
    def _build_cache_payload(
        cls,
        *,
        team_id: str,
        plugin_code: str,
        api_key_enc: str,
        base_url: str,
        max_concurrent: int | None,
        max_qps: int | None,
        updated_by: str,
    ) -> dict[str, Any]:
        return {
            "plugin_code": plugin_code,
            "team_id": team_id,
            "api_key_enc": api_key_enc,
            "base_url": base_url,
            "max_concurrent": max_concurrent,
            "max_qps": max_qps,
            "updated_by": updated_by,
        }

    @classmethod
    def _label_text(cls, value) -> str:
        for attr in ("zh_Hans", "en_US"):
            text = getattr(value, attr, None)
            if text:
                return text.lower()
        return ""

    @classmethod
    def _build_credentials(cls, provider_entity: ProviderEntity, api_key: str, base_url: str) -> dict[str, Any]:
        credentials: dict[str, Any] = {}
        api_assigned = False
        url_assigned = False

        if provider_entity.provider_credential_schema:
            for field in provider_entity.provider_credential_schema.credential_form_schemas:
                variable = field.variable.lower()
                label = cls._label_text(field.label)
                if field.type == FormType.SECRET_INPUT and (
                    any(keyword in variable for keyword in cls.API_KEY_KEYWORDS)
                    or any(keyword in label for keyword in cls.API_KEY_KEYWORDS)
                    or not api_assigned
                ):
                    credentials[field.variable] = api_key
                    api_assigned = True
                    continue

                if field.type == FormType.TEXT_INPUT and base_url and (
                    any(keyword in variable for keyword in cls.BASE_URL_KEYWORDS)
                    or any(keyword in label for keyword in cls.BASE_URL_KEYWORDS)
                ):
                    credentials[field.variable] = base_url
                    url_assigned = True
                    continue

                if field.default is not None:
                    credentials[field.variable] = field.default

        if not api_assigned:
            credentials["api_key"] = api_key
        if base_url and not url_assigned:
            credentials["base_url"] = base_url

        return credentials

    @classmethod
    def list_team_model_configs(cls, team_id: str) -> list[dict[str, Any]]:
        config_rows = {
            row.plugin_code: row
            for row in db.session.scalars(
                select(TeamModelConfig).where(TeamModelConfig.team_id == team_id)
            ).all()
        }
        result = []
        for plugin in GlobalPluginService.list_enabled_plugins():
            try:
                ModelProviderFactory(plugin.source_tenant_id).get_provider_schema(plugin.plugin_code)
            except Exception:
                continue

            row = config_rows.get(plugin.plugin_code)
            result.append(
                {
                    "plugin_code": plugin.plugin_code,
                    "name": plugin.name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "enabled": plugin.enabled,
                    "configured": row is not None,
                    "api_key_set": row is not None,
                    "base_url": row.base_url if row else "",
                    "max_concurrent": row.max_concurrent if row else None,
                    "max_qps": row.max_qps if row else None,
                    "updated_at": row.updated_at.isoformat() if row else None,
                }
            )
        return result

    @classmethod
    def save_team_model_config(
        cls,
        *,
        team_id: str,
        updated_by: str,
        plugin_code: str,
        api_key: str | None,
        base_url: str,
        max_concurrent: int | None,
        max_qps: int | None,
    ) -> dict[str, Any]:
        plugin = GlobalPluginService.get_enabled_plugin(plugin_code)
        if not plugin:
            raise ValueError("Global plugin does not exist or is disabled.")

        normalized_api_key = (api_key or "").strip()
        normalized_base_url = base_url.strip()

        record = db.session.scalar(
            select(TeamModelConfig).where(
                TeamModelConfig.team_id == team_id,
                TeamModelConfig.plugin_code == plugin_code,
            )
        )

        resolved_api_key = normalized_api_key
        if record and not resolved_api_key:
            resolved_api_key = decrypt_api_key(record.api_key_enc)

        if not resolved_api_key:
            raise ValueError("API key is required for the initial team model configuration.")

        provider_entity = ModelProviderFactory(plugin.source_tenant_id).get_provider_schema(plugin_code)
        credentials = cls._build_credentials(provider_entity, resolved_api_key, normalized_base_url)
        ModelProviderFactory(plugin.source_tenant_id).provider_credentials_validate(provider=plugin_code, credentials=credentials)

        if not record:
            record = TeamModelConfig(
                team_id=team_id,
                plugin_code=plugin_code,
                api_key_enc=encrypt_api_key(resolved_api_key),
                base_url=normalized_base_url,
                max_concurrent=max_concurrent,
                max_qps=max_qps,
                updated_by=updated_by,
            )
            db.session.add(record)
        else:
            if normalized_api_key:
                record.api_key_enc = encrypt_api_key(normalized_api_key)
            record.base_url = normalized_base_url
            record.max_concurrent = max_concurrent
            record.max_qps = max_qps
            record.updated_by = updated_by

        db.session.commit()

        cache_payload = cls._build_cache_payload(
            team_id=team_id,
            plugin_code=plugin_code,
            api_key_enc=record.api_key_enc,
            base_url=record.base_url,
            max_concurrent=record.max_concurrent,
            max_qps=record.max_qps,
            updated_by=record.updated_by,
        )
        redis_client.setex(cls._cache_key(team_id, plugin_code), cls.CACHE_TTL, json.dumps(cache_payload))

        return {
            "plugin_code": plugin_code,
            "configured": True,
            "base_url": record.base_url,
            "max_concurrent": max_concurrent,
            "max_qps": max_qps,
        }

    @classmethod
    def get_team_model_binding(cls, team_id: str, plugin_code: str) -> TeamModelBinding | None:
        plugin = GlobalPluginService.get_enabled_plugin(plugin_code)
        if not plugin:
            return None

        cache_key = cls._cache_key(team_id, plugin_code)
        cached = redis_client.get(cache_key)
        if cached:
            try:
                payload = json.loads(cached)
                api_key_enc = payload.get("api_key_enc")
                if not api_key_enc:
                    raise ValueError("Missing encrypted api key in cache payload.")
                config = TeamModelConfig(
                    team_id=team_id,
                    plugin_code=plugin_code,
                    api_key_enc=api_key_enc,
                    base_url=payload["base_url"],
                    max_concurrent=payload.get("max_concurrent"),
                    max_qps=payload.get("max_qps"),
                    updated_by=payload.get("updated_by") or "",
                )
                provider_entity = ModelProviderFactory(plugin.source_tenant_id).get_provider_schema(plugin_code)
                credentials = cls._build_credentials(
                    provider_entity,
                    decrypt_api_key(api_key_enc),
                    payload["base_url"],
                )
                return TeamModelBinding(plugin=plugin, config=config, credentials=credentials)
            except Exception:
                redis_client.delete(cache_key)

        config = db.session.scalar(
            select(TeamModelConfig).where(
                TeamModelConfig.team_id == team_id,
                TeamModelConfig.plugin_code == plugin_code,
            )
        )
        if not config:
            return None

        provider_entity = ModelProviderFactory(plugin.source_tenant_id).get_provider_schema(plugin_code)
        api_key = decrypt_api_key(config.api_key_enc)
        credentials = cls._build_credentials(provider_entity, api_key, config.base_url)
        redis_client.setex(
            cache_key,
            cls.CACHE_TTL,
            json.dumps(
                cls._build_cache_payload(
                    team_id=team_id,
                    plugin_code=plugin_code,
                    api_key_enc=config.api_key_enc,
                    base_url=config.base_url,
                    max_concurrent=config.max_concurrent,
                    max_qps=config.max_qps,
                    updated_by=config.updated_by,
                )
            ),
        )
        return TeamModelBinding(plugin=plugin, config=config, credentials=credentials)
