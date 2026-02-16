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


settings = Settings()
