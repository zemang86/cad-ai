#!/usr/bin/env python3
"""Embed knowledge base Markdown files into Supabase pgvector.

Usage:
    .venv/bin/python scripts/embed_knowledge.py              # incremental
    .venv/bin/python scripts/embed_knowledge.py --force       # re-embed all
    .venv/bin/python scripts/embed_knowledge.py --file ubbl/03-spatial-requirements.md
    .venv/bin/python scripts/embed_knowledge.py --dry-run     # preview chunks
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src/ is on the path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from autocad_batch_commander.config import settings


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Strip YAML frontmatter, return (meta, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    return {}, text[end + 3:].strip()


def _count_tokens(text: str) -> int:
    """Count tokens using tiktoken (cl100k_base for text-embedding-3-small)."""
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def chunk_markdown(file_path: str, text: str, max_tokens: int = 800) -> list[dict]:
    """Split Markdown by H2/H3 headings into chunks.

    Each chunk gets the file_path and heading hierarchy prepended for context.
    Returns list of dicts with: file_path, chunk_index, heading_hierarchy,
    chunk_text, token_count.
    """
    _, body = _parse_frontmatter(text)
    lines = body.split("\n")

    chunks: list[dict] = []
    current_h2 = ""
    current_h3 = ""
    current_lines: list[str] = []

    def _flush(h2: str, h3: str) -> None:
        content = "\n".join(current_lines).strip()
        if not content:
            return
        hierarchy = [h for h in [h2, h3] if h]
        token_count = _count_tokens(content)

        # If chunk is too large and we're at H2 level, it will be split
        # at H3 boundaries during parsing. If still too large, we split
        # by paragraph as a fallback.
        if token_count > max_tokens * 2:
            _split_large(file_path, content, hierarchy, chunks, max_tokens)
        else:
            chunks.append({
                "file_path": file_path,
                "chunk_index": len(chunks),
                "heading_hierarchy": hierarchy,
                "chunk_text": content,
                "token_count": token_count,
            })

    def _split_large(
        fp: str, content: str, hierarchy: list[str],
        out: list[dict], max_tok: int,
    ) -> None:
        """Split oversized chunks by double-newline paragraphs."""
        paragraphs = content.split("\n\n")
        buffer: list[str] = []
        buffer_tokens = 0
        for para in paragraphs:
            para_tokens = _count_tokens(para)
            if buffer and buffer_tokens + para_tokens > max_tok:
                out.append({
                    "file_path": fp,
                    "chunk_index": len(out),
                    "heading_hierarchy": hierarchy,
                    "chunk_text": "\n\n".join(buffer),
                    "token_count": buffer_tokens,
                })
                buffer = []
                buffer_tokens = 0
            buffer.append(para)
            buffer_tokens += para_tokens
        if buffer:
            out.append({
                "file_path": fp,
                "chunk_index": len(out),
                "heading_hierarchy": hierarchy,
                "chunk_text": "\n\n".join(buffer),
                "token_count": buffer_tokens,
            })

    for line in lines:
        if line.startswith("## ") and not line.startswith("### "):
            _flush(current_h2, current_h3)
            current_h2 = line[3:].strip()
            current_h3 = ""
            current_lines = [line]
        elif line.startswith("### "):
            _flush(current_h2, current_h3)
            current_h3 = line[4:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    _flush(current_h2, current_h3)

    # Re-index chunk_index sequentially
    for i, chunk in enumerate(chunks):
        chunk["chunk_index"] = i

    return chunks


def discover_files(single_file: str | None = None) -> list[Path]:
    """Find all .md files in knowledge/qa/ (excluding _index.md)."""
    qa_dir = settings.knowledge_dir / "qa"
    if single_file:
        path = qa_dir / single_file
        if not path.exists():
            print(f"File not found: {path}")
            sys.exit(1)
        return [path]
    files = sorted(qa_dir.rglob("*.md"))
    return [f for f in files if f.name != "_index.md"]


def embed_and_upsert(chunks: list[dict], dry_run: bool = False) -> None:
    """Embed chunks via OpenAI and upsert to Supabase."""
    if dry_run:
        print(f"\n  Would embed {len(chunks)} chunks")
        for c in chunks[:5]:
            hierarchy = " > ".join(c["heading_hierarchy"])
            print(f"    [{c['chunk_index']}] {hierarchy} ({c['token_count']} tokens)")
        if len(chunks) > 5:
            print(f"    ... and {len(chunks) - 5} more")
        return

    from autocad_batch_commander.chat.embeddings import embed_texts
    from autocad_batch_commander.chat.client import get_supabase

    # Batch embed
    texts = [c["chunk_text"] for c in chunks]
    print(f"  Embedding {len(texts)} chunks...")
    embeddings = embed_texts(texts)

    supabase = get_supabase()

    # Delete existing rows for this file_path
    file_path = chunks[0]["file_path"]
    supabase.table("knowledge_embeddings").delete().eq(
        "file_path", file_path
    ).execute()

    # Insert fresh rows
    rows = []
    for chunk, embedding in zip(chunks, embeddings):
        rows.append({
            "file_path": chunk["file_path"],
            "chunk_index": chunk["chunk_index"],
            "heading_hierarchy": chunk["heading_hierarchy"],
            "chunk_text": chunk["chunk_text"],
            "token_count": chunk["token_count"],
            "embedding": embedding,
            "metadata": {},
        })

    # Insert in batches of 50
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        supabase.table("knowledge_embeddings").insert(batch).execute()

    print(f"  Upserted {len(rows)} chunks for {file_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed knowledge base into pgvector")
    parser.add_argument("--force", action="store_true", help="Re-embed all files")
    parser.add_argument("--file", type=str, help="Single file relative to knowledge/qa/")
    parser.add_argument("--dry-run", action="store_true", help="Preview chunks without embedding")
    args = parser.parse_args()

    files = discover_files(args.file)
    qa_dir = settings.knowledge_dir / "qa"

    print(f"Found {len(files)} file(s) to process\n")

    total_chunks = 0
    for path in files:
        rel = str(path.relative_to(qa_dir))
        text = path.read_text(encoding="utf-8")
        chunks = chunk_markdown(rel, text)
        total_chunks += len(chunks)
        print(f"  {rel}: {len(chunks)} chunks")

        if chunks:
            embed_and_upsert(chunks, dry_run=args.dry_run)

    print(f"\nDone. Total: {total_chunks} chunks across {len(files)} files.")


if __name__ == "__main__":
    main()
