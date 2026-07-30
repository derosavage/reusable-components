"""
Flask API Gateway middleware — auth, rate limiting, error handling.
"""
from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

import jwt as pyjwt
from flask import g, jsonify, request

from shared.config import settings
from shared.errors import AuthError, RateLimitError

_rate_buckets: Dict[str, Dict[str, Any]] = {}


def rate_limit(requests: Optional[int] = None, window: Optional[int] = None):
    req_limit = requests or settings.RATE_LIMIT_REQUESTS
    win = window or settings.RATE_LIMIT_WINDOW
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr or "unknown"
            key = f"{client_ip}:{request.path}"
            now = time.time()
            bucket = _rate_buckets.get(key, {"tokens": req_limit, "last_refill": now})
            elapsed = now - bucket["last_refill"]
            bucket["tokens"] = min(req_limit, bucket["tokens"] + elapsed * (req_limit / win))
            bucket["last_refill"] = now
            if bucket["tokens"] < 1:
                raise RateLimitError("Too many requests")
            bucket["tokens"] -= 1
            _rate_buckets[key] = bucket
            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_auth(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "missing or invalid Authorization header"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = pyjwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            if payload.get("type") != "access":
                return jsonify({"error": "invalid token type"}), 401
            g.user_id = payload["sub"]
            g.role_bitmask = payload.get("role", 0)
        except pyjwt.ExpiredSignatureError:
            return jsonify({"error": "token expired"}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({"error": "invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper


def require_permission(permission: str):
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            role_bitmask = getattr(g, "role_bitmask", 0)
            if not settings.has_permission(role_bitmask, permission):
                return jsonify({"error": f"missing permission: {permission}"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def handle_errors(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except RateLimitError as e:
            return jsonify(e.to_dict()), e.status_code
        except AuthError as e:
            return jsonify(e.to_dict()), e.status_code
        except Exception as e:
            return jsonify({"error": "internal_error", "detail": str(e)}), 500
    return wrapper
