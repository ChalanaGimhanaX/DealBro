from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), case_sensitive=False)

    # Database (MongoDB)
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "dealbro"

    # Ingestion
    ingestion_interval_minutes: int = 30
    user_agent: str = "DealBro/1.0 (+https://dealbro.com/bot)"

    # Rate Limiting (requests per minute per source)
    rate_limit_hostingdiscussion: int = 30
    rate_limit_lowendtalk: int = 30
    rate_limit_webhostingtalk: int = 20

    # Logging
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # Feature Flags
    enable_webhostingtalk: bool = False

    # LLM API Configuration
    llm_api_url: str = "http://localhost:5005/2121212121/v1/chat/completions"
    llm_api_key: str = ""
    llm_model: str = "gpt-5.1"


settings = Settings()
