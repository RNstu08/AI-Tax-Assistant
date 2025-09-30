from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """
    Centralized application settings.
    Reads from environment variables and an optional .env file.
    """

    environment: str = "dev"
    groq_api_key: str | None = None
    extractor_model: str = "llama-3.1-8b-instant"
    reasoner_model: str = "llama-3.1-70b-versatile"
    sqlite_path: str = ".data/profile.db"
    chroma_path: str = ".data/chroma"
    log_level: str = "INFO"
    enable_json_logs: bool = True
    # model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    # Load from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
