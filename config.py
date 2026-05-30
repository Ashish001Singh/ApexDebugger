from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    voyage_api_key: str = ""
    log_level: str = "INFO"
    environment: str = "development"

    # LLM model used for reasoning (Phase 2+)
    claude_model: str = "claude-sonnet-4-6"


settings = Settings()
