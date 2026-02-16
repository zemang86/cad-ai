"""Load and query the regulation knowledge base (Markdown files)."""

from __future__ import annotations

from pathlib import Path

from autocad_batch_commander.config import settings


def _knowledge_dir() -> Path:
    """Return the resolved knowledge directory."""
    return settings.knowledge_dir


def load_index() -> str:
    """Read the topic index file and return its contents."""
    index_path = _knowledge_dir() / "qa" / "_index.md"
    if not index_path.exists():
        raise FileNotFoundError(f"Knowledge index not found: {index_path}")
    return index_path.read_text(encoding="utf-8")


def find_relevant_files(query: str) -> list[Path]:
    """Find knowledge base files relevant to a query.

    Scans the topic index for keyword matches and returns paths to
    the matching Markdown files. Uses simple keyword overlap — no
    embeddings or vector search needed for a small corpus.
    """
    index_text = load_index()
    query_lower = query.lower()
    query_words = set(query_lower.split())

    qa_dir = _knowledge_dir() / "qa"
    matched: list[Path] = []

    # Parse the quick-reference section for keyword → file mappings
    for line in index_text.splitlines():
        line_stripped = line.strip()

        # Match quick reference lines: - **keyword** → `file.md`
        if line_stripped.startswith("- **") and "→" in line_stripped:
            keyword_part = line_stripped.split("**")[1].lower()
            keywords = {w.strip() for w in keyword_part.replace("/", " ").split()}

            if keywords & query_words:
                # Extract file paths from the line
                for segment in line_stripped.split("`"):
                    if segment.endswith(".md"):
                        candidate = qa_dir / segment
                        if candidate.exists() and candidate not in matched:
                            matched.append(candidate)

        # Match table rows: | `ubbl/03-spatial-requirements.md` | topics... |
        if "|" in line_stripped and ".md" in line_stripped:
            parts = line_stripped.split("|")
            for part in parts:
                part = part.strip()
                # Check if any query word appears in the topic column
                if any(w in part.lower() for w in query_words if len(w) > 2):
                    # Extract file path from any backtick segment in the row
                    for segment in line_stripped.split("`"):
                        if segment.endswith(".md"):
                            candidate = qa_dir / segment
                            if candidate.exists() and candidate not in matched:
                                matched.append(candidate)

    # Fallback: if no matches found, load all files
    if not matched:
        matched = sorted(qa_dir.rglob("*.md"))
        matched = [f for f in matched if f.name != "_index.md"]

    return matched


def load_files(paths: list[Path]) -> dict[str, str]:
    """Read multiple Markdown files and return {relative_path: content}."""
    qa_dir = _knowledge_dir() / "qa"
    result: dict[str, str] = {}
    for path in paths:
        if path.exists():
            try:
                rel = path.relative_to(qa_dir)
            except ValueError:
                rel = path.name
            result[str(rel)] = path.read_text(encoding="utf-8")
    return result


def query_knowledge_base(query: str) -> dict[str, str]:
    """End-to-end: find relevant files for a query and load their content.

    Returns a dict of {relative_path: markdown_content} for all files
    matching the query. The caller (MCP tool or CLI) can then pass this
    content to Claude for synthesis with citations.
    """
    relevant = find_relevant_files(query)
    return load_files(relevant)
