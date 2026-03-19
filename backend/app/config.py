from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SocialGenius"
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Database (SQLite para desarrollo, PostgreSQL para produccion)
    # En Railway, solo define DATABASE_URL con la URL de Postgres.
    # SYNC_DATABASE_URL se deriva automáticamente si no se define explícitamente.
    DATABASE_URL: str = "sqlite+aiosqlite:///./socialgenius.db"
    SYNC_DATABASE_URL: str = ""

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI (Hugging Face)
    HUGGINGFACE_API_KEY: str = ""
    HUGGINGFACE_MODEL: str = "Qwen/Qwen2.5-72B-Instruct"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRO_PRICE_ID: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    def model_post_init(self, __context) -> None:
        """Deriva SYNC_DATABASE_URL desde DATABASE_URL si no está definida."""
        if not self.SYNC_DATABASE_URL:
            url = self.DATABASE_URL
            # Quitar driver async para obtener URL síncrona (usada por Alembic)
            url = url.replace("sqlite+aiosqlite", "sqlite")
            url = url.replace("postgresql+asyncpg", "postgresql")
            url = url.replace("postgres+asyncpg", "postgresql")
            # Railway a veces devuelve "postgres://" sin "ql"
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            object.__setattr__(self, "SYNC_DATABASE_URL", url)


settings = Settings()
