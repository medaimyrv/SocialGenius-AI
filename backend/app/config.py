from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SocialGenius"
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Database (SQLite para desarrollo, PostgreSQL para produccion)
    DATABASE_URL: str = "sqlite+aiosqlite:///./socialgenius.db"
    SYNC_DATABASE_URL: str = "sqlite:///./socialgenius.db"

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI (Hugging Face para desarrollo, OpenAI/Anthropic para produccion)
    HUGGINGFACE_API_KEY: str = ""
    HUGGINGFACE_MODEL: str = "Qwen/Qwen2.5-72B-Instruct"
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRO_PRICE_ID: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
