from __future__ import annotations

import logging
import socket
from typing import Any
from urllib.parse import urlparse, urlunparse

import requests

from configs import dify_config
from extensions.ext_database import db
from models.account import Account
from services.errors.account import AccountPasswordError, CurrentPasswordIncorrectError

logger = logging.getLogger(__name__)


class SSOAccountService:
    def __init__(self) -> None:
        self.sso_base_url = self._normalize_sso_base_url(dify_config.SSO_API_URL)
        self.sso_owner = (dify_config.SSO_PROVISION_OWNER or "").strip() or "CheersAI"
        self.client_id = dify_config.SSO_PROVISION_CLIENT_ID or dify_config.DESKTOP_SSO_CLIENT_ID
        self.client_secret = dify_config.SSO_PROVISION_CLIENT_SECRET or dify_config.DESKTOP_SSO_CLIENT_SECRET
        self.ssl_verify = dify_config.BETA_PROVISION_SSL_VERIFY

    def is_enabled(self) -> bool:
        return bool(self.sso_base_url and self.client_id and self.client_secret)

    def is_sso_account(self, account: Account) -> bool:
        config = account.custom_config_dict
        return bool(
            config.get("desktop_sso_subject")
            or config.get("desktop_sso_username")
            or config.get("desktop_sso_owner")
            or (account.password is None and account.email and account.name)
        )

    def update_password(self, account: Account, current_password: str | None, new_password: str) -> None:
        if not self.is_enabled():
            raise AccountPasswordError("SSO password service is not configured.")

        owner, username = self._resolve_identity(account)
        config = account.custom_config_dict
        payload = {
            "userOwner": owner,
            "userName": username,
            "newPassword": new_password,
        }
        if current_password:
            payload["oldPassword"] = current_password

        response = self._request(
            method="POST",
            path="/api/set-password",
            data=payload,
            auth=(self.client_id, self.client_secret),
        )
        if not self._is_success_response(response):
            error_message = self._build_http_error("Failed to update SSO password", response)
            if self._is_current_password_error(error_message):
                raise CurrentPasswordIncorrectError(error_message)
            raise AccountPasswordError(error_message)

        self._clear_signin_lock(owner, username)

        config.update({
            "desktop_sso_owner": owner,
            "desktop_sso_username": username,
            "desktop_sso_password_set": True,
        })
        account.custom_config_dict = config
        db.session.commit()

    def _resolve_identity(self, account: Account) -> tuple[str, str]:
        config = account.custom_config_dict
        owner = (config.get("desktop_sso_owner") or self.sso_owner or "").strip()
        username = (
            config.get("desktop_sso_username")
            or config.get("desktop_sso_preferred_username")
            or account.name
            or ""
        ).strip()
        if not owner or not username:
            raise AccountPasswordError("Unable to resolve linked SSO user identity.")
        return owner, username

    def _get_user(self, owner: str, username: str) -> dict[str, Any] | None:
        response = self._request(
            method="GET",
            path="/api/get-user",
            params={"id": f"{owner}/{username}"},
            auth=(self.client_id, self.client_secret),
        )
        if not self._is_success_response(response):
            return None
        payload = self._extract_data(response)
        return payload if isinstance(payload, dict) else None

    def _request(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        auth: tuple[str, str] | None = None,
    ) -> requests.Response:
        url = f"{self.sso_base_url}{path}"
        try:
            return self._send_request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                auth=auth,
                verify=self.ssl_verify,
            )
        except requests.RequestException as exc:
            fallback_url, fallback_headers = self._build_ip_fallback_request(url)
            if not fallback_url:
                raise

            logger.warning("Retrying SSO request via IP fallback for %s after %s", path, exc.__class__.__name__)
            return self._send_request(
                method=method,
                url=fallback_url,
                params=params,
                json=json,
                data=data,
                auth=auth,
                verify=False,
                headers=fallback_headers,
            )

    def _send_request(
        self,
        *,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        data: dict[str, Any] | None,
        auth: tuple[str, str] | None,
        verify: bool,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        return requests.request(
            method=method,
            url=url,
            params=params,
            json=json,
            data=data,
            auth=auth,
            timeout=15,
            verify=verify,
            headers=headers,
        )

    def _clear_signin_lock(self, owner: str, username: str) -> None:
        sso_user = self._get_user(owner, username)
        if not sso_user:
            return

        sso_user["signinWrongTimes"] = 0
        sso_user["lastSigninWrongTime"] = ""
        response = self._request(
            method="POST",
            path="/api/update-user",
            params={
                "id": f"{owner}/{username}",
                "columns": "signin_wrong_times,last_signin_wrong_time",
            },
            json=sso_user,
            auth=(self.client_id, self.client_secret),
        )
        if not self._is_success_response(response):
            logger.warning("Failed to clear SSO sign-in lock for %s/%s", owner, username)

    @staticmethod
    def _build_ip_fallback_request(url: str) -> tuple[str | None, dict[str, str] | None]:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if parsed.scheme != "https" or not hostname:
            return None, None

        try:
            resolved_ip = socket.gethostbyname(hostname)
        except OSError:
            return None, None

        if not resolved_ip or resolved_ip == hostname:
            return None, None

        netloc = resolved_ip
        if parsed.port:
            netloc = f"{resolved_ip}:{parsed.port}"

        fallback_url = urlunparse(parsed._replace(netloc=netloc))
        return fallback_url, {"Host": hostname}

    @staticmethod
    def _normalize_sso_base_url(value: str) -> str:
        normalized = (value or "").rstrip("/")
        if normalized.endswith("/api"):
            return normalized[:-4]
        return normalized

    @staticmethod
    def _extract_data(response: requests.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            return None
        if isinstance(payload, dict) and "data" in payload:
            return payload.get("data")
        return payload

    @staticmethod
    def _is_success_response(response: requests.Response) -> bool:
        if response.status_code != 200:
            return False

        try:
            payload = response.json()
        except ValueError:
            return True

        if not isinstance(payload, dict):
            return True

        status = str(payload.get("status", "")).lower()
        if status and status != "ok":
            return False

        return True

    @staticmethod
    def _build_http_error(prefix: str, response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if isinstance(payload, dict):
            message = payload.get("msg") or payload.get("message") or payload.get("error")
            if message:
                return f"{prefix}: {message}"
        return f"{prefix}: HTTP {response.status_code}"

    @staticmethod
    def _is_current_password_error(message: str) -> bool:
        normalized = (message or "").lower()
        return "password or code is incorrect" in normalized or "current password is incorrect" in normalized
