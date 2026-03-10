"""Tests de integración para endpoints de autenticación."""
import pytest
from httpx import AsyncClient


REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
ME_URL = "/api/v1/auth/me"

USER_DATA = {
    "email": "user@test.com",
    "password": "password123",
    "full_name": "Test User",
}


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

async def test_register_success(client: AsyncClient):
    response = await client.post(REGISTER_URL, json=USER_DATA)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == USER_DATA["email"]
    assert body["full_name"] == USER_DATA["full_name"]
    assert "id" in body
    assert "hashed_password" not in body


async def test_register_duplicate_email(client: AsyncClient):
    await client.post(REGISTER_URL, json=USER_DATA)
    response = await client.post(REGISTER_URL, json=USER_DATA)
    assert response.status_code == 409


async def test_register_invalid_email(client: AsyncClient):
    response = await client.post(REGISTER_URL, json={**USER_DATA, "email": "no-es-email"})
    assert response.status_code == 422


async def test_register_short_password(client: AsyncClient):
    response = await client.post(REGISTER_URL, json={**USER_DATA, "password": "123"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def test_login_success(client: AsyncClient, registered_user: dict):
    response = await client.post(LOGIN_URL, json={
        "email": USER_DATA["email"],
        "password": USER_DATA["password"],
    })
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, registered_user: dict):
    response = await client.post(LOGIN_URL, json={
        "email": USER_DATA["email"],
        "password": "contraseña_incorrecta",
    })
    assert response.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(LOGIN_URL, json={
        "email": "noexiste@test.com",
        "password": "cualquiera",
    })
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------

async def test_refresh_token_success(client: AsyncClient, registered_user: dict):
    login_resp = await client.post(LOGIN_URL, json={
        "email": USER_DATA["email"],
        "password": USER_DATA["password"],
    })
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_refresh_invalid_token(client: AsyncClient):
    response = await client.post(REFRESH_URL, json={"refresh_token": "token.falso.xyz"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------

async def test_get_me_authenticated(client: AsyncClient, auth_headers: dict):
    response = await client.get(ME_URL, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == USER_DATA["email"]


async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get(ME_URL)
    assert response.status_code == 401


async def test_get_me_invalid_token(client: AsyncClient):
    response = await client.get(ME_URL, headers={"Authorization": "Bearer token.invalido"})
    assert response.status_code == 401
