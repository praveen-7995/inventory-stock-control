import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Defaults to a local SQLite file so the app runs with zero setup.
    # In production (Render/Supabase) this is overridden by an env var
    # pointing at a real Postgres instance.
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./inventory.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12  # 12 hours
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")


settings = Settings()
