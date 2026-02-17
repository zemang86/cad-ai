"""Unit tests for chat Pydantic models."""

import pytest
from pydantic import ValidationError

from autocad_batch_commander.chat.models import (
    ChatMessage,
    ChatRequest,
    ChunkMatch,
    FeedbackRequest,
    SessionConsentRequest,
)


class TestChatMessage:
    def test_valid_user(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_valid_assistant(self):
        msg = ChatMessage(role="assistant", content="Hi there")
        assert msg.role == "assistant"

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="system", content="nope")


class TestChatRequest:
    def test_minimal(self):
        req = ChatRequest(session_id="abc-123", message="What is UBBL?")
        assert req.session_id == "abc-123"
        assert req.conversation_history == []

    def test_with_history(self):
        req = ChatRequest(
            session_id="abc",
            message="Follow up",
            conversation_history=[
                ChatMessage(role="user", content="Hi"),
                ChatMessage(role="assistant", content="Hello"),
            ],
        )
        assert len(req.conversation_history) == 2


class TestSessionConsentRequest:
    def test_defaults(self):
        req = SessionConsentRequest(session_id="s1")
        assert req.consent_given is True
        assert req.user_agent is None

    def test_with_agent(self):
        req = SessionConsentRequest(
            session_id="s1", consent_given=True, user_agent="Mozilla/5.0"
        )
        assert req.user_agent == "Mozilla/5.0"


class TestFeedbackRequest:
    def test_valid_up(self):
        req = FeedbackRequest(message_id="m1", session_id="s1", rating="up")
        assert req.rating == "up"
        assert req.comment is None

    def test_valid_down_with_comment(self):
        req = FeedbackRequest(
            message_id="m1", session_id="s1", rating="down", comment="Inaccurate"
        )
        assert req.comment == "Inaccurate"

    def test_invalid_rating(self):
        with pytest.raises(ValidationError):
            FeedbackRequest(message_id="m1", session_id="s1", rating="maybe")


class TestChunkMatch:
    def test_full(self):
        chunk = ChunkMatch(
            file_path="ubbl/03-spatial.md",
            chunk_index=2,
            chunk_text="Minimum corridor width is 1,200 mm.",
            heading_hierarchy=["Spatial Requirements", "Corridors"],
            score=0.92,
        )
        assert chunk.file_path == "ubbl/03-spatial.md"
        assert chunk.score == 0.92

    def test_defaults(self):
        chunk = ChunkMatch(
            file_path="test.md", chunk_index=0, chunk_text="text", score=0.8
        )
        assert chunk.heading_hierarchy == []
