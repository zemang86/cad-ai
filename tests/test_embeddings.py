"""Tests for chunking logic and embedding helpers (mocked OpenAI)."""

from __future__ import annotations

from scripts.embed_knowledge import chunk_markdown


class TestChunkMarkdown:
    def test_splits_by_h2(self):
        text = "## Introduction\nSome intro text.\n\n## Requirements\nReq content."
        chunks = chunk_markdown("test.md", text)
        assert len(chunks) == 2
        assert chunks[0]["heading_hierarchy"] == ["Introduction"]
        assert chunks[1]["heading_hierarchy"] == ["Requirements"]

    def test_h3_within_h2(self):
        text = (
            "## Fire Safety\n"
            "Overview.\n"
            "### Compartmentation\n"
            "Compartment details.\n"
            "### Escape Routes\n"
            "Escape details.\n"
        )
        chunks = chunk_markdown("test.md", text)
        assert len(chunks) == 3
        assert chunks[0]["heading_hierarchy"] == ["Fire Safety"]
        assert chunks[1]["heading_hierarchy"] == ["Fire Safety", "Compartmentation"]
        assert chunks[2]["heading_hierarchy"] == ["Fire Safety", "Escape Routes"]

    def test_frontmatter_stripped(self):
        text = (
            "---\nsource: test\n---\n"
            "## Section\nContent here."
        )
        chunks = chunk_markdown("test.md", text)
        assert len(chunks) == 1
        assert "---" not in chunks[0]["chunk_text"]
        assert "source: test" not in chunks[0]["chunk_text"]

    def test_chunk_index_sequential(self):
        text = "## A\nText A.\n## B\nText B.\n## C\nText C."
        chunks = chunk_markdown("test.md", text)
        indices = [c["chunk_index"] for c in chunks]
        assert indices == [0, 1, 2]

    def test_empty_body(self):
        text = "---\nsource: x\n---\n"
        chunks = chunk_markdown("test.md", text)
        assert chunks == []

    def test_no_headings(self):
        text = "Just plain text without any headings.\nAnother line."
        chunks = chunk_markdown("test.md", text)
        # All content goes into one chunk with empty hierarchy
        assert len(chunks) == 1
        assert chunks[0]["heading_hierarchy"] == []

    def test_file_path_preserved(self):
        text = "## Section\nContent."
        chunks = chunk_markdown("ubbl/03-spatial.md", text)
        assert all(c["file_path"] == "ubbl/03-spatial.md" for c in chunks)

    def test_token_count_present(self):
        text = "## Section\nSome content here with several words."
        chunks = chunk_markdown("test.md", text)
        assert all("token_count" in c and c["token_count"] > 0 for c in chunks)
