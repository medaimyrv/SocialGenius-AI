import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app as fastapi_app
from app.db.session import get_db
from app.models.base import Base
import app.models.user  # noqa
import app.models.business  # noqa
import app.models.conversation  # noqa
import app.models.message  # noqa
import app.models.content_calendar  # noqa
import app.models.content_piece  # noqa
import app.models.subscription  # noqa

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    response = await client.post("/api/v1/auth/register", json={
        "email": "user@test.com",
        "password": "password123",
        "full_name": "Test User",
    })
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user: dict) -> dict:
    response = await client.post("/api/v1/auth/login", json={
        "email": "user@test.com",
        "password": "password123",
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_business(client: AsyncClient, auth_headers: dict) -> dict:
    response = await client.post("/api/v1/businesses", json={
        "name": "Panadería La Estrella",
        "industry": "Alimentación",
        "description": "Panadería artesanal con productos horneados frescos cada día.",
        "target_audience": "Familias del barrio",
        "brand_voice": "amigable",
    }, headers=auth_headers)
    assert response.status_code == 201
    return response.json()
