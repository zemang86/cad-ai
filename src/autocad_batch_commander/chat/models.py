"""Pydantic models for the chat module."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message (user or assistant)."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Incoming chat request from the frontend."""

    session_id: str
    message: str
    conversation_history: list[ChatMessage] = Field(default_factory=list)


class SessionConsentRequest(BaseModel):
    """Create/update a chat session with consent."""

    session_id: str
    consent_given: bool = True
    user_agent: str | None = None


class FeedbackRequest(BaseModel):
    """Thumbs up/down feedback on an assistant message."""

    message_id: str
    session_id: str
    rating: str = Field(..., pattern="^(up|down)$")
    comment: str | None = None


class ChunkMatch(BaseModel):
    """A matched knowledge base chunk from pgvector search."""

    file_path: str
    chunk_index: int
    chunk_text: str
    heading_hierarchy: list[str] = Field(default_factory=list)
    score: float
