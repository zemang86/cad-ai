"""System prompt templates for the RAG chat pipeline."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are an expert assistant specialising in Malaysian building regulations, \
particularly the Uniform Building By-Laws 1984 (UBBL) and its 2021 Amendment, \
Fire By-Laws, and related Malaysian Standards (MS 1525, MS 1184, etc.).

Guidelines:
- Always cite specific By-Law numbers, Schedule references, or Standard clauses \
when providing thresholds or requirements (e.g. "By-Law 39(1)", "Fifth Schedule").
- Be precise with numeric thresholds — include the exact value and unit \
(e.g. "minimum 1,200 mm", "not less than 2 hours fire resistance").
- If the context chunks do not contain enough information to answer confidently, \
say so clearly rather than guessing.
- Use Markdown formatting: bold for key values, tables where appropriate, \
and blockquotes for direct citations.
- When multiple building types have different requirements, present them in a \
table or list for clarity.
- Keep answers concise but thorough. Prioritise actionable information that \
architects and engineers need for compliance.
- If the question is outside Malaysian building regulations, politely redirect.
"""

FEW_SHOT_INTRO = "Here are examples of highly-rated previous answers for reference:\n\n"

CONTEXT_INTRO = (
    "Use the following regulation excerpts to answer the user's question. "
    "Cite the source file and By-Law where possible.\n\n"
)


def format_context_chunks(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the system message."""
    parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        heading = " > ".join(chunk.get("heading_hierarchy", []))
        source = chunk.get("file_path", "unknown")
        header = f"[{i}] {source}"
        if heading:
            header += f" — {heading}"
        parts.append(f"{header}\n{chunk['chunk_text']}")
    return CONTEXT_INTRO + "\n---\n".join(parts)


def format_few_shot(examples: list[dict]) -> str:
    """Format highly-rated Q&A pairs as few-shot examples."""
    if not examples:
        return ""
    parts: list[str] = [FEW_SHOT_INTRO]
    for ex in examples:
        parts.append(f"**Q:** {ex['question']}\n**A:** {ex['answer']}\n")
    return "\n".join(parts)
