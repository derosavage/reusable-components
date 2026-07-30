from __future__ import annotations

from typing import Any, Dict, Optional


class AppError(Exception):
    status_code: int = 500
    detail: str = "Internal server error"
    code: str = "internal_error"

    def __init__(self, detail: Optional[str] = None, code: Optional[str] = None, extra: Optional[Dict[str, Any]] = None):
        if detail:
            self.detail = detail
        if code:
            self.code = code
        self.extra = extra or {}

    def to_dict(self) -> Dict[str, Any]:
        return {"error": self.code, "detail": self.detail, **self.extra}


class AuthError(AppError):
    status_code = 401
    detail = "Authentication failed"
    code = "auth_error"


class ForbiddenError(AppError):
    status_code = 403
    detail = "Forbidden"
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found"
    code = "not_found"


class ValidationError(AppError):
    status_code = 422
    detail = "Validation failed"
    code = "validation_error"


class RateLimitError(AppError):
    status_code = 429
    detail = "Too many requests"
    code = "rate_limit_exceeded"


class ServiceUnavailableError(AppError):
    status_code = 503
    detail = "Service unavailable"
    code = "service_unavailable"
