"""Tests for the knowledge base loader."""

from __future__ import annotations

from autocad_batch_commander.knowledge.loader import (
    find_relevant_files,
    load_files,
    load_index,
    query_knowledge_base,
)


def test_load_index():
    """Index file loads successfully and contains expected content."""
    index = load_index()
    assert "Topic Index" in index
    assert "_index.md" not in index or "ubbl/" in index
    assert "UBBL" in index


def test_find_relevant_files_corridor():
    """Query about corridors returns spatial requirements file."""
    files = find_relevant_files("corridor width")
    assert any("03-spatial-requirements.md" in str(f) for f in files)


def test_find_relevant_files_fire():
    """Query about fire returns fire-related files."""
    files = find_relevant_files("fire resistance")
    assert any("04-fire-requirements.md" in str(f) for f in files)


def test_find_relevant_files_parking():
    """Query about parking returns parking file."""
    files = find_relevant_files("parking")
    assert any("05-parking-requirements.md" in str(f) for f in files)


def test_find_relevant_files_escape():
    """Query about escape routes returns both UBBL fire and fire-bylaws."""
    files = find_relevant_files("escape route")
    file_names = [str(f) for f in files]
    assert any("04-fire-requirements.md" in n for n in file_names)
    assert any("02-fire-escape.md" in n for n in file_names)


def test_find_relevant_files_accessibility():
    """Query about OKU returns accessibility file."""
    files = find_relevant_files("OKU accessibility")
    assert any("06-accessibility-requirements.md" in str(f) for f in files)


def test_find_relevant_files_fallback():
    """Unknown query falls back to loading all files."""
    files = find_relevant_files("xyznonexistenttopic12345")
    # Should return all .md files (excluding _index.md)
    assert len(files) >= 6


def test_load_files():
    """Loading files returns dict with content."""
    files = find_relevant_files("corridor")
    content = load_files(files)
    assert len(content) > 0
    # Content should contain actual regulation text
    for _path, text in content.items():
        assert len(text) > 100


def test_query_knowledge_base_end_to_end():
    """End-to-end query returns content with citations."""
    result = query_knowledge_base("minimum corridor width")
    assert len(result) > 0
    # Should contain By-Law 34 citation
    all_content = "\n".join(result.values())
    assert "By-Law 34" in all_content


def test_query_knowledge_base_room_size():
    """Query about room sizes returns spatial content."""
    result = query_knowledge_base("minimum room size residential")
    assert len(result) > 0
    all_content = "\n".join(result.values())
    assert "By-Law 32" in all_content
