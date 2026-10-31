from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "change-me-in-development"
    access_token_minutes: int = 30
    refresh_token_days: int = 30
    database_url: str = "sqlite:///./kicks_insight.db"
    cors_origins: str = "http://localhost:4200"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    whatsapp_verify_token: str | None = None
    whatsapp_app_secret: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_waba_id: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_business_account_id: str | None = None
    whatsapp_api_version: str = "v26.0"
    whatsapp_webhook_url: str | None = None
    tiktok_client_key: str | None = None
    tiktok_client_secret: str | None = None
    meta_client_id: str | None = None
    meta_client_secret: str | None = None
    web_app_url: str = "http://localhost:4200"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

