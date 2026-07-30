from __future__ import annotations

import uuid
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from shared.config import settings

from .auth import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    generate_password_reset_token,
    hash_password,
    hash_token,
    verify_password,
)
from .models import PasswordReset, RefreshToken, User

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not email or not username or not password:
        return jsonify({"error": "email, username, and password required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400

    db = g.db
    existing = db.query(User).filter((User.email == email) | (User.username == username)).first()
    if existing:
        return jsonify({"error": "email or username already taken"}), 409

    user = User(
        id=uuid.uuid4(),
        email=email,
        username=username,
        password_hash=hash_password(password),
        role_bitmask=settings.ROLE_BITS.get("viewer", 0),
    )
    db.add(user)
    db.commit()

    return jsonify({"message": "user created", "user_id": str(user.id)}), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    db = g.db
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"error": "account is deactivated"}), 403
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        return jsonify({"error": "account is locked"}), 423

    user.failed_login_attempts = 0
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(str(user.id), user.role_bitmask)
    refresh_token, refresh_expires = create_refresh_token()

    rt = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=refresh_expires,
    )
    db.add(rt)
    db.commit()

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.JWT_ACCESS_EXPIRY,
        "token_type": "Bearer",
    })


@bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json()
    refresh_token = data.get("refresh_token", "")
    if not refresh_token:
        return jsonify({"error": "refresh_token required"}), 400

    db = g.db
    token_hash = hash_token(refresh_token)
    stored = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc),
    ).first()

    if not stored:
        return jsonify({"error": "invalid or expired refresh token"}), 401

    stored.revoked = True
    db.commit()

    user = db.query(User).filter(User.id == stored.user_id).first()
    if not user or not user.is_active:
        return jsonify({"error": "user not found or inactive"}), 401

    access_token = create_access_token(str(user.id), user.role_bitmask)
    new_refresh_token, new_expires = create_refresh_token()

    rt = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_token(new_refresh_token),
        expires_at=new_expires,
    )
    db.add(rt)
    db.commit()

    return jsonify({
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "expires_in": settings.JWT_ACCESS_EXPIRY,
        "token_type": "Bearer",
    })


@bp.route("/logout", methods=["POST"])
def logout():
    data = request.get_json()
    refresh_token = data.get("refresh_token", "")
    if refresh_token:
        db = g.db
        stored = db.query(RefreshToken).filter(
            RefreshToken.token_hash == hash_token(refresh_token),
            RefreshToken.revoked == False,
        ).first()
        if stored:
            stored.revoked = True
            db.commit()
    return jsonify({"message": "logged out"})


@bp.route("/password-reset/request", methods=["POST"])
def request_password_reset():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    db = g.db
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return jsonify({"message": "if the email exists, a reset link has been sent"})

    token, expires = generate_password_reset_token()
    pr = PasswordReset(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=expires,
    )
    db.add(pr)
    db.commit()

    return jsonify({
        "message": "if the email exists, a reset link has been sent",
        "reset_token": token,
    })


@bp.route("/password-reset/confirm", methods=["POST"])
def confirm_password_reset():
    data = request.get_json()
    token = data.get("token", "")
    new_password = data.get("new_password", "")
    if not token or not new_password:
        return jsonify({"error": "token and new_password required"}), 400
    if len(new_password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400

    db = g.db
    pr = db.query(PasswordReset).filter(
        PasswordReset.token_hash == hash_token(token),
        PasswordReset.used == False,
        PasswordReset.expires_at > datetime.now(timezone.utc),
    ).first()

    if not pr:
        return jsonify({"error": "invalid or expired reset token"}), 401

    user = db.query(User).filter(User.id == pr.user_id).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    user.password_hash = hash_password(new_password)
    pr.used = True
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked == False,
    ).update({"revoked": True})
    db.commit()
    return jsonify({"message": "password reset successful"})


@bp.route("/me", methods=["GET"])
def me():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "missing or invalid Authorization header"}), 401

    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)

    db = g.db
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "role_bitmask": user.role_bitmask,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "auth"})