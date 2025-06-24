"""Read .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from pathlib import Path


class Settings(BaseSettings):
    """Get settings."""

    bot_token: SecretStr
    url: SecretStr
    key: SecretStr
    model_config = SettingsConfigDict(env_file=Path(__file__).parent / '.env', env_file_encoding='utf-8')


config = Settings()
