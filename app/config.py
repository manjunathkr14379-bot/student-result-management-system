"""
Centralized application configuration.
Values are loaded from environment variables (see .env.example),
falling back to sensible defaults for local development.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Student Management System"
    database_url: str = "sqlite:///./sms.db"

    # JWT settings
    secret_key: str = "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
