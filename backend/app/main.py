import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all tables if they don't exist
    from app.db.session import engine
    from app.models.base import Base
    # Import all models so SQLAlchemy registers them
    import app.models.user  # noqa
    import app.models.business  # noqa
    import app.models.conversation  # noqa
    import app.models.message  # noqa
    import app.models.content_calendar  # noqa
    import app.models.content_piece  # noqa
    import app.models.subscription  # noqa
    import app.models.user_activity  # noqa
    import app.models.document  # noqa

    logger.info(f"Connecting to DB: {settings.DATABASE_URL[:30]}...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("DB tables ready ✓")
    logger.info(f"HuggingFace model: {settings.HUGGINGFACE_MODEL}")
    logger.info(f"HuggingFace API key set: {bool(settings.HUGGINGFACE_API_KEY)}")

    yield

    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered social media content strategy assistant",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


# Register API routers
from app.api.v1.router import api_v1_router  # noqa: E402

app.include_router(api_v1_router, prefix="/api/v1")

