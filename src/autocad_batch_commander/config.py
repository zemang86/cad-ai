"""Application settings via pydantic-settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings, overridable via environment variables."""

    model_config = {"env_prefix": "ACAD_CMD_"}

    backup_enabled: bool = True
    log_level: str = "INFO"
    standards_dir: Path = Path(__file__).resolve().parent.parent.parent / "standards"
    knowledge_dir: Path = Path(__file__).resolve().parent.parent.parent / "knowledge"
    use_mock: bool = False

    # AI Chat settings
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    supabase_url: str = ""
    supabase_key: str = ""
    chat_max_history: int = 10
    chat_max_context_chunks: int = 6
    chat_similarity_threshold: float = 0.4
    chat_enabled: bool = False


settings = Settings()
