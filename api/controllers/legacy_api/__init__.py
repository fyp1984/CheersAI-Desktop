import os

import httpx
from flask import Blueprint, Response, request

from controllers.console.auth.apply_beta import ApplyBetaPayload

bp = Blueprint("legacy_api", __name__, url_prefix="/api/nexus")
NEXUS_BETA_APPLY_PATH = "/nexus/api/beta-applications/apply"


def _build_nexus_target_url() -> str | None:
    configured_base = (os.getenv("NEXUS_API_BASE_URL") or os.getenv("NEXT_PUBLIC_NEXUS_API_PREFIX") or "").strip()
    if not configured_base:
        return None

    return f"{configured_base.rstrip('/')}{NEXUS_BETA_APPLY_PATH}"


@bp.post("/beta-applications/apply")
def apply_beta_legacy():
    args = ApplyBetaPayload.model_validate(request.get_json(silent=True) or {})
    target_url = _build_nexus_target_url()
    if not target_url:
        return {"result": "fail", "message": "Nexus API base URL is not configured"}, 500

    try:
        timeout = httpx.Timeout(30.0, connect=10.0)
        with httpx.Client(timeout=timeout) as client:
            upstream_response = client.post(
                target_url,
                json={
                    "name": args.name,
                    "email": args.email,
                    "language": args.language,
                    "invite_code": args.invite_code,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

        excluded_headers = {"content-length", "transfer-encoding", "connection", "content-encoding"}
        response_headers = [
            (key, value)
            for key, value in upstream_response.headers.items()
            if key.lower() not in excluded_headers
        ]

        return Response(
            upstream_response.content,
            status=upstream_response.status_code,
            headers=response_headers,
        )
    except httpx.HTTPError:
        return {"result": "fail", "message": "Nexus apply proxy request failed"}, 502
