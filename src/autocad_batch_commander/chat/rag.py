"""RAG pipeline — orchestrates retrieval, prompt construction, and streaming."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from autocad_batch_commander.chat.client import get_supabase
from autocad_batch_commander.chat.embeddings import (
    embed_text,
    fetch_highly_rated_examples,
    search_similar,
)
from autocad_batch_commander.chat.models import ChatMessage
from autocad_batch_commander.chat.prompts import (
    SYSTEM_PROMPT,
    format_context_chunks,
    format_few_shot,
)
from autocad_batch_commander.config import settings


def _build_messages(
    user_message: str,
    history: list[ChatMessage],
    context_chunks: list[dict],
    few_shot_examples: list[dict],
) -> list[dict]:
    """Assemble the OpenAI messages array."""
    messages: list[dict] = []

    # System prompt + few-shot + context
    system_parts = [SYSTEM_PROMPT]
    few_shot_block = format_few_shot(few_shot_examples)
    if few_shot_block:
        system_parts.append(few_shot_block)
    if context_chunks:
        system_parts.append(format_context_chunks(context_chunks))
    messages.append({"role": "system", "content": "\n\n".join(system_parts)})

    # Conversation history (last N turns)
    max_history = settings.chat_max_history
    recent = history[-max_history:]
    for msg in recent:
        messages.append({"role": msg.role, "content": msg.content})

    # Current user message
    messages.append({"role": "user", "content": user_message})
    return messages


def _persist_messages(
    session_id: str,
    user_message: str,
    assistant_message: str,
    context_chunks: list[dict],
    model: str,
) -> str:
    """Save user + assistant messages to Supabase. Returns assistant message_id."""
    supabase = get_supabase()

    # User message
    supabase.table("chat_messages").insert(
        {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": "user",
            "content": user_message,
            "context_chunks": None,
            "model": None,
            "prompt_tokens": None,
            "completion_tokens": None,
        }
    ).execute()

    # Assistant message
    assistant_id = str(uuid.uuid4())
    chunk_refs = [
        {"file_path": c["file_path"], "chunk_index": c["chunk_index"], "score": c["score"]}
        for c in context_chunks
    ]
    supabase.table("chat_messages").insert(
        {
            "id": assistant_id,
            "session_id": session_id,
            "role": "assistant",
            "content": assistant_message,
            "context_chunks": chunk_refs,
            "model": model,
            "prompt_tokens": None,
            "completion_tokens": None,
        }
    ).execute()

    # Update session last_active_at
    supabase.table("chat_sessions").update(
        {"last_active_at": "now()"}
    ).eq("id", session_id).execute()

    return assistant_id


async def generate_chat_response(
    session_id: str,
    message: str,
    history: list[ChatMessage],
) -> AsyncGenerator[dict, None]:
    """Stream a RAG-augmented chat response.

    Yields dicts: {"type": "delta", "content": "..."} and
    {"type": "done", "message_id": "..."} at the end.
    """
    from openai import OpenAI

    # 1. Embed query and search
    query_embedding = embed_text(message)
    chunks = search_similar(query_embedding)
    context_chunks = [
        {
            "file_path": c.file_path,
            "chunk_index": c.chunk_index,
            "chunk_text": c.chunk_text,
            "heading_hierarchy": c.heading_hierarchy,
            "score": c.score,
        }
        for c in chunks
    ]

    # 2. Fetch few-shot examples
    try:
        few_shot = fetch_highly_rated_examples(limit=3)
    except Exception:
        few_shot = []

    # 3. Build messages
    messages = _build_messages(message, history, context_chunks, few_shot)

    # 4. Stream OpenAI completion
    client = OpenAI(api_key=settings.openai_api_key)
    model = settings.openai_model
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    full_response = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            full_response += delta.content
            yield {"type": "delta", "content": delta.content}

    # 5. Persist messages
    try:
        assistant_id = _persist_messages(
            session_id, message, full_response, context_chunks, model
        )
    except Exception:
        assistant_id = str(uuid.uuid4())

    yield {"type": "done", "message_id": assistant_id}
