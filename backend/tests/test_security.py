"""Tests para funciones de seguridad: JWT y hashing de contraseñas."""
import uuid
from datetime import UTC, datetime

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def test_hash_password_returns_string():
    hashed = hash_password("micontraseña123")
    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_hash_is_not_plaintext():
    plain = "secreto"
    assert hash_password(plain) != plain


def test_verify_password_correct():
    plain = "password123"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("correcta")
    assert verify_password("incorrecta", hashed) is False


def test_same_password_produces_different_hashes():
    plain = "misma"
    h1 = hash_password(plain)
    h2 = hash_password(plain)
    assert h1 != h2  # bcrypt uses random salt


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

def test_create_access_token_returns_string():
    token = create_access_token(uuid.uuid4())
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token_returns_string():
    token = create_refresh_token(uuid.uuid4())
    assert isinstance(token, str)


def test_decode_access_token():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_decode_refresh_token():
    user_id = uuid.uuid4()
    token = create_refresh_token(user_id)
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"


def test_access_and_refresh_tokens_differ():
    user_id = uuid.uuid4()
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)
    assert access != refresh


def test_decode_invalid_token_returns_none():
    assert decode_token("token.invalido.xyz") is None


def test_decode_empty_string_returns_none():
    assert decode_token("") is None


def test_tokens_for_different_users_differ():
    t1 = create_access_token(uuid.uuid4())
    t2 = create_access_token(uuid.uuid4())
    assert t1 != t2
