"""Tests for RAG prompt construction (no external API calls)."""

from __future__ import annotations

from autocad_batch_commander.chat.models import ChatMessage
from autocad_batch_commander.chat.prompts import (
    format_context_chunks,
    format_few_shot,
)
from autocad_batch_commander.chat.rag import _build_messages


class TestFormatContextChunks:
    def test_formats_chunks(self):
        chunks = [
            {
                "file_path": "ubbl/03-spatial.md",
                "heading_hierarchy": ["Corridors"],
                "chunk_text": "Minimum corridor width is 1,200 mm.",
            },
            {
                "file_path": "ubbl/04-fire.md",
                "heading_hierarchy": ["Fire Doors", "Ratings"],
                "chunk_text": "Fire doors must be rated for 1 hour.",
            },
        ]
        result = format_context_chunks(chunks)
        assert "ubbl/03-spatial.md" in result
        assert "Corridors" in result
        assert "1,200 mm" in result
        assert "[1]" in result
        assert "[2]" in result

    def test_empty_chunks(self):
        result = format_context_chunks([])
        assert "regulation excerpts" in result


class TestFormatFewShot:
    def test_formats_examples(self):
        examples = [
            {
                "question": "What is minimum corridor width?",
                "answer": "1,200 mm per By-Law 39.",
            },
        ]
        result = format_few_shot(examples)
        assert "**Q:**" in result
        assert "1,200 mm" in result

    def test_empty_returns_empty(self):
        assert format_few_shot([]) == ""


class TestBuildMessages:
    def test_basic_structure(self):
        messages = _build_messages(
            user_message="What is the minimum room size?",
            history=[],
            context_chunks=[
                {
                    "file_path": "ubbl/03-spatial.md",
                    "heading_hierarchy": ["Room Sizes"],
                    "chunk_text": "Minimum habitable room: 11 m².",
                }
            ],
            few_shot_examples=[],
        )
        assert messages[0]["role"] == "system"
        assert "Malaysian building regulations" in messages[0]["content"]
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "What is the minimum room size?"

    def test_includes_history(self):
        history = [
            ChatMessage(role="user", content="Hi"),
            ChatMessage(role="assistant", content="Hello!"),
        ]
        messages = _build_messages("Follow up", history, [], [])
        roles = [m["role"] for m in messages]
        assert roles == ["system", "user", "assistant", "user"]

    def test_truncates_history(self, monkeypatch):
        monkeypatch.setattr(
            "autocad_batch_commander.chat.rag.settings.chat_max_history", 2
        )
        history = [ChatMessage(role="user", content=f"msg {i}") for i in range(10)]
        messages = _build_messages("latest", history, [], [])
        # system + 2 history + current user = 4
        assert len(messages) == 4

    def test_includes_few_shot(self):
        few_shot = [{"question": "Q?", "answer": "A."}]
        messages = _build_messages("test", [], [], few_shot)
        assert "**Q:**" in messages[0]["content"]
