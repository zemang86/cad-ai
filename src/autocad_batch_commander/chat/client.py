"""Supabase client singleton."""

from __future__ import annotations

from typing import TYPE_CHECKING

from autocad_batch_commander.config import settings

if TYPE_CHECKING:
    from supabase import Client

_client: Client | None = None


def get_supabase() -> Client:
    """Return the lazily-initialised Supabase client."""
    global _client
    if _client is None:
        from supabase import create_client

        if not settings.supabase_url or not settings.supabase_key:
            raise RuntimeError(
                "ACAD_CMD_SUPABASE_URL and ACAD_CMD_SUPABASE_KEY must be set"
            )
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client
