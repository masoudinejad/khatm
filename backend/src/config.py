import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Collective Recitation API"
    version: str = "1.0.0"
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    database_url: str = os.getenv("DATABASE_URL", "recitations.db")
    token_expiry_days: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
