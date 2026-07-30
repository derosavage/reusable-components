from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import jwt as pyjwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from shared.config import settings
from shared.errors import AuthError, ForbiddenError, ValidationError

ph = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
)


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: str, role_bitmask: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': user_id,
        'role': role_bitmask,
        'type': 'access',
        'iat': now,
        'exp': now + timedelta(seconds=settings.JWT_ACCESS_EXPIRY),
        'jti': str(uuid.uuid4()),
    }
    return pyjwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> Tuple[str, datetime]:
    token = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_REFRESH_EXPIRY)
    return token, expires


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = pyjwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get('type') != 'access':
            raise AuthError('Invalid token type')
        return payload
    except pyjwt.ExpiredSignatureError:
        raise AuthError('Token expired')
    except pyjwt.InvalidTokenError:
        raise AuthError('Invalid token')


def check_permission(role_bitmask: int, required_permission: str) -> None:
    if not settings.has_permission(role_bitmask, required_permission):
        raise ForbiddenError(f'Missing permission: {required_permission}')


def generate_password_reset_token() -> Tuple[str, datetime]:
    token = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    return token, expires
