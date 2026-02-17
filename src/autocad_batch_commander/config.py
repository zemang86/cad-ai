"""Application settings via pydantic-settings."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings


def _find_project_root() -> Path:
    """Find the project root by walking up from this file or cwd.

    Works both in development (src layout) and when installed as a package
    (e.g. on Vercel where __file__ points to site-packages).
    """
    # From source: src/autocad_batch_commander/config.py → repo root
    src_root = Path(__file__).resolve().parent.parent.parent
    if (src_root / "knowledge").is_dir():
        return src_root

    # Installed package: try VERCEL_PROJECT_ROOT or cwd
    for candidate in [
        Path(os.environ.get("VERCEL_PROJECT_ROOT", "")),
        Path.cwd(),
    ]:
        if candidate.is_dir() and (candidate / "knowledge").is_dir():
            return candidate

    return src_root  # fallback


_PROJECT_ROOT = _find_project_root()


class Settings(BaseSettings):
    """Global application settings, overridable via environment variables."""

    model_config = {"env_prefix": "ACAD_CMD_"}

    backup_enabled: bool = True
    log_level: str = "INFO"
    standards_dir: Path = _PROJECT_ROOT / "standards"
    knowledge_dir: Path = _PROJECT_ROOT / "knowledge"
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
