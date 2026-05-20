import logging

from flask import request
from flask_restx import Resource, fields

from configs import dify_config
from controllers.console import console_ns

logger = logging.getLogger(__name__)

sso_proxy_token_model = console_ns.model("SSOProxyToken", {
    "code": fields.String(required=False, description="Authorization code from SSO"),
    "refreshToken": fields.String(required=False, description="Refresh token from SSO"),
    "redirectUri": fields.String(required=False, description="Redirect URI used in authorization"),
    "codeVerifier": fields.String(required=False, description="PKCE code verifier"),
    "grantType": fields.String(required=True, description="authorization_code | refresh_token"),
})

sso_proxy_access_token_model = console_ns.model("SSOProxyAccessToken", {
    "accessToken": fields.String(required=True, description="SSO access token"),
})


def _resolve_sso_base_url() -> str:
    candidate = (dify_config.SSO_API_URL or "").strip()
    if candidate.endswith("/api"):
        candidate = candidate[:-4]
    return candidate.rstrip("/")


def _require_sso_config() -> tuple[str, str, str]:
    sso_base_url = _resolve_sso_base_url()
    client_id = (dify_config.DESKTOP_SSO_CLIENT_ID or "").strip()
    client_secret = (dify_config.DESKTOP_SSO_CLIENT_SECRET or "").strip()
    if not sso_base_url or not client_id:
        raise ValueError("SSO is not configured")
    return sso_base_url, client_id, client_secret


def _request_with_impersonation(method: str, url: str, **kwargs):
    try:
        from curl_cffi import requests as curl_requests
    except Exception as e:
        raise RuntimeError("curl_cffi is not available") from e

    impersonate = kwargs.pop("impersonate", "chrome")
    return curl_requests.request(method, url, impersonate=impersonate, **kwargs)


@console_ns.route("/auth/sso-proxy/token")
class SSOProxyTokenApi(Resource):
    @console_ns.expect(sso_proxy_token_model)
    def post(self):
        try:
            payload = request.get_json() or {}
            grant_type = (payload.get("grantType") or "").strip()
            code = (payload.get("code") or "").strip()
            refresh_token = (payload.get("refreshToken") or "").strip()
            redirect_uri = (payload.get("redirectUri") or "").strip()
            code_verifier = (payload.get("codeVerifier") or "").strip()

            if grant_type not in {"authorization_code", "refresh_token"}:
                return {"error": "Invalid grantType"}, 400

            sso_base_url, client_id, client_secret = _require_sso_config()
            token_url = f"{sso_base_url}/api/login/oauth/access_token"

            form = {
                "grant_type": grant_type,
                "client_id": client_id,
            }
            if grant_type == "authorization_code":
                if not code or not redirect_uri:
                    return {"error": "Missing code or redirectUri"}, 400
                form.update({
                    "code": code,
                    "redirect_uri": redirect_uri,
                })
            else:
                if not refresh_token:
                    return {"error": "Missing refreshToken"}, 400
                form.update({
                    "refresh_token": refresh_token,
                })

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            if client_secret:
                form["client_secret"] = client_secret
            if code_verifier:
                form["code_verifier"] = code_verifier

            response = _request_with_impersonation(
                "POST",
                token_url,
                headers=headers,
                data=form,
                timeout=10,
            )
            if response.status_code != 200:
                return {"error": "Token exchange failed", "status": response.status_code}, response.status_code
            return response.json()
        except ValueError as e:
            return {"error": str(e)}, 500
        except RuntimeError as e:
            return {"error": str(e)}, 500
        except Exception:
            logger.exception("SSO proxy token exchange failed")
            return {"error": "Internal server error"}, 500


@console_ns.route("/auth/sso-proxy/userinfo")
class SSOProxyUserInfoApi(Resource):
    @console_ns.expect(sso_proxy_access_token_model)
    def post(self):
        try:
            payload = request.get_json() or {}
            access_token = (payload.get("accessToken") or "").strip()
            if not access_token:
                return {"error": "Missing accessToken"}, 400

            sso_base_url, _, _ = _require_sso_config()
            userinfo_url = f"{sso_base_url}/api/userinfo"
            response = _request_with_impersonation(
                "GET",
                userinfo_url,
                params={"access_token": access_token},
                timeout=10,
            )
            if response.status_code != 200:
                return {"error": "Failed to fetch user info", "status": response.status_code}, response.status_code
            return response.json()
        except ValueError as e:
            return {"error": str(e)}, 500
        except RuntimeError as e:
            return {"error": str(e)}, 500
        except Exception:
            logger.exception("SSO proxy userinfo failed")
            return {"error": "Internal server error"}, 500


@console_ns.route("/auth/sso-proxy/get-account")
class SSOProxyAccountApi(Resource):
    @console_ns.expect(sso_proxy_access_token_model)
    def post(self):
        try:
            payload = request.get_json() or {}
            access_token = (payload.get("accessToken") or "").strip()
            if not access_token:
                return {"error": "Missing accessToken"}, 400

            sso_base_url, _, _ = _require_sso_config()
            account_url = f"{sso_base_url}/api/get-account"
            response = _request_with_impersonation(
                "GET",
                account_url,
                params={"access_token": access_token},
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            if response.status_code != 200:
                return None, response.status_code
            return response.json()
        except ValueError as e:
            return {"error": str(e)}, 500
        except RuntimeError as e:
            return {"error": str(e)}, 500
        except Exception:
            logger.exception("SSO proxy get-account failed")
            return {"error": "Internal server error"}, 500
