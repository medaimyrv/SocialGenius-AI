"""Tests de integración para el CRUD de negocios."""
import pytest
from httpx import AsyncClient

BUSINESSES_URL = "/api/v1/businesses"

BUSINESS_PAYLOAD = {
    "name": "Panadería La Estrella",
    "industry": "Alimentación",
    "description": "Panadería artesanal con productos horneados frescos cada día.",
    "target_audience": "Familias del barrio",
    "brand_voice": "amigable",
}


# ---------------------------------------------------------------------------
# Crear negocio
# ---------------------------------------------------------------------------

async def test_create_business_success(client: AsyncClient, auth_headers: dict):
    response = await client.post(BUSINESSES_URL, json=BUSINESS_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == BUSINESS_PAYLOAD["name"]
    assert body["industry"] == BUSINESS_PAYLOAD["industry"]
    assert "id" in body
    assert "owner_id" in body


async def test_create_business_unauthenticated(client: AsyncClient):
    response = await client.post(BUSINESSES_URL, json=BUSINESS_PAYLOAD)
    assert response.status_code == 401


async def test_create_business_missing_required_fields(client: AsyncClient, auth_headers: dict):
    response = await client.post(BUSINESSES_URL, json={"name": "Solo nombre"}, headers=auth_headers)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Listar negocios
# ---------------------------------------------------------------------------

async def test_list_businesses_empty(client: AsyncClient, auth_headers: dict):
    response = await client.get(BUSINESSES_URL, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_businesses_returns_own_only(client: AsyncClient, auth_headers: dict):
    await client.post(BUSINESSES_URL, json=BUSINESS_PAYLOAD, headers=auth_headers)
    await client.post(BUSINESSES_URL, json={**BUSINESS_PAYLOAD, "name": "Otro Negocio"}, headers=auth_headers)

    response = await client.get(BUSINESSES_URL, headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_businesses_unauthenticated(client: AsyncClient):
    response = await client.get(BUSINESSES_URL)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Obtener negocio por ID
# ---------------------------------------------------------------------------

async def test_get_business_by_id(client: AsyncClient, auth_headers: dict, test_business: dict):
    business_id = test_business["id"]
    response = await client.get(f"{BUSINESSES_URL}/{business_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == business_id


async def test_get_business_not_found(client: AsyncClient, auth_headers: dict):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"{BUSINESSES_URL}/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Actualizar negocio
# ---------------------------------------------------------------------------

async def test_update_business(client: AsyncClient, auth_headers: dict, test_business: dict):
    business_id = test_business["id"]
    response = await client.patch(
        f"{BUSINESSES_URL}/{business_id}",
        json={"name": "Nombre Actualizado"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Nombre Actualizado"
    assert response.json()["industry"] == BUSINESS_PAYLOAD["industry"]


async def test_update_business_not_found(client: AsyncClient, auth_headers: dict):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.patch(
        f"{BUSINESSES_URL}/{fake_id}",
        json={"name": "Nuevo"},
        headers=auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Eliminar negocio
# ---------------------------------------------------------------------------

async def test_delete_business(client: AsyncClient, auth_headers: dict, test_business: dict):
    business_id = test_business["id"]
    response = await client.delete(f"{BUSINESSES_URL}/{business_id}", headers=auth_headers)
    assert response.status_code == 204

    get_resp = await client.get(f"{BUSINESSES_URL}/{business_id}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_delete_business_not_found(client: AsyncClient, auth_headers: dict):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"{BUSINESSES_URL}/{fake_id}", headers=auth_headers)
    assert response.status_code == 404
