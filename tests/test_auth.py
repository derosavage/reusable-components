from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from services.auth_service.auth import create_access_token, create_refresh_token, decode_access_token, hash_password, hash_token, verify_password


class TestAuth:
    def test_password_hashing(self):
        pw = "SecureP@ss123"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_token_hashing(self):
        token = "test-token-123"
        assert hash_token(token) == hash_token(token)
        assert len(hash_token(token)) == 64

    def test_create_and_decode_access_token(self):
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id, 0)
        payload = decode_access_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_expired_token(self):
        with patch("services.auth_service.auth.settings.JWT_ACCESS_EXPIRY", -1):
            token = create_access_token(str(uuid.uuid4()), 0)
        with pytest.raises(Exception):
            decode_access_token(token)

    def test_invalid_token(self):
        with pytest.raises(Exception):
            decode_access_token("invalid.token.here")

    def test_create_refresh_token(self):
        token, expires = create_refresh_token()
        assert token
        assert expires > datetime.now(timezone.utc)
