from __future__ import annotations

from typing import Any, Dict

import httpx
import jwt as pyjwt
from flask import Blueprint, Response, jsonify, request

from shared.config import settings

bp = Blueprint("gateway", __name__)

# Service registry: prefix -> {url, auth_required, permission}
ROUTES: Dict[str, Dict[str, Any]] = {
    "/auth": {"url": settings.AUTH_SERVICE_URL, "auth_required": False, "permission": None},
    "/analytics": {"url": settings.ANALYTICS_SERVICE_URL, "auth_required": True, "permission": "analytics:read"},
    "/data": {"url": settings.DATA_FACTORY_URL, "auth_required": True, "permission": "data:read"},
    "/daraja": {"url": settings.DARAJA_SERVICE_URL, "auth_required": True, "permission": "daraja:initiate"},
    "/llm": {"url": settings.LLM_SERVICE_URL, "auth_required": True, "permission": "llm:query"},
}

_client = httpx.AsyncClient(timeout=30.0)


def _match_route(path: str) -> tuple:
    for prefix, config in ROUTES.items():
        if path.startswith(prefix):
            return prefix, config
    return None, None


@bp.route("/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(subpath: str):
    prefix, config = _match_route(f"/{subpath}")
    if not config:
        return jsonify({"error": "route not found"}), 404

    if config["auth_required"]:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "authentication required"}), 401

    if config["permission"]:
        token = request.headers.get("Authorization", "").split(" ", 1)[1]
        try:
            payload = pyjwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            role = payload.get("role", 0)
            if not settings.has_permission(role, config["permission"]):
                return jsonify({"error": f"missing permission: {config['permission']}"}), 403
        except Exception:
            return jsonify({"error": "invalid token"}), 401

    target_url = f"{config['url']}{settings.API_PREFIX}/{subpath}"
    method = request.method.lower()
    headers = {k: v for k, v in request.headers if k.lower() not in ("host", "content-length")}
    params = dict(request.args)
    body = request.get_data()

    try:
        resp = await _client.request(method, target_url, headers=headers, params=params, content=body)
        return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))
    except httpx.RequestError as e:
        return jsonify({"error": "upstream_service_error", "detail": str(e)}), 502


@bp.route("/health", methods=["GET"])
async def health():
    return jsonify({"status": "ok", "service": "api-gateway"})