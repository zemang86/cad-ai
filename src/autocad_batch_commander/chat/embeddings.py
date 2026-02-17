"""OpenAI embeddings and pgvector similarity search."""

from __future__ import annotations

from autocad_batch_commander.chat.client import get_supabase
from autocad_batch_commander.chat.models import ChunkMatch
from autocad_batch_commander.config import settings


def _get_openai():
    """Return a lazily-created OpenAI client."""
    from openai import OpenAI

    return OpenAI(api_key=settings.openai_api_key)


def embed_text(text: str) -> list[float]:
    """Embed a single text string using OpenAI."""
    client = _get_openai()
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
    )
    return response.data[0].embedding


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts in a single batch call."""
    if not texts:
        return []
    client = _get_openai()
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


def search_similar(
    query_embedding: list[float],
    top_k: int | None = None,
    threshold: float | None = None,
) -> list[ChunkMatch]:
    """Search pgvector for similar knowledge chunks via Supabase RPC."""
    if top_k is None:
        top_k = settings.chat_max_context_chunks
    if threshold is None:
        threshold = settings.chat_similarity_threshold

    supabase = get_supabase()
    result = supabase.rpc(
        "match_knowledge",
        {
            "query_embedding": query_embedding,
            "match_threshold": threshold,
            "match_count": top_k,
        },
    ).execute()

    chunks: list[ChunkMatch] = []
    for row in result.data or []:
        chunks.append(
            ChunkMatch(
                file_path=row["file_path"],
                chunk_index=row["chunk_index"],
                chunk_text=row["chunk_text"],
                heading_hierarchy=row.get("heading_hierarchy") or [],
                score=row["similarity"],
            )
        )
    return chunks


def fetch_highly_rated_examples(limit: int = 3) -> list[dict]:
    """Fetch highly-rated Q&A pairs from the Supabase view for few-shot."""
    supabase = get_supabase()
    result = (
        supabase.table("highly_rated_qa")
        .select("question, answer")
        .limit(limit)
        .execute()
    )
    return result.data or []
