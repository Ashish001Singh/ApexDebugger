from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    voyage_api_key: str = ""
    log_level: str = "INFO"
    environment: str = "development"

    # Optional path to a project-specific best-practices .md the user supplies.
    # Grounding = built-in best_practices.md + this file (if set and exists).
    user_best_practices_path: str = ""

    # LLM model used for reasoning (Phase 2+)
    claude_model: str = "claude-haiku-4-5-20251001"
    openai_model: str = "gpt-4o-mini"

settings = Settings()
