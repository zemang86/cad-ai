"""Natural language router for the ask_araiden MCP tool.

Classifies user intent via keyword matching (or optionally OpenAI)
and routes to the appropriate structured operation.
"""

from __future__ import annotations

import re
from pathlib import Path

from autocad_batch_commander.knowledge.loader import query_knowledge_base


# Intent patterns: (regex, intent_key)
_INTENT_PATTERNS: list[tuple[str, str]] = [
    (r"\b(dimension|dims?|measurement|measure)\b", "extract_dimensions"),
    (r"\b(area|polyline|room size|floor area)\b", "extract_areas"),
    (r"\b(compliance|comply|check drawing|ubbl check)\b", "measure_compliance"),
    (
        r"\b(title ?block|update title|project (no|number|name)|drawn by)\b",
        "title_block",
    ),
    (r"\b(schedule|door schedule|window schedule)\b", "extract_schedule"),
    (r"\b(xref|external ref|xrefs)\b", "xref_list"),
    (r"\b(search|find text|look for)\b", "search"),
    (r"\b(purge|clean|unused)\b", "purge"),
    (r"\b(plot|pdf|print|dwf)\b", "plot"),
    (r"\b(info|summary|overview|drawing info)\b", "drawing_info"),
    (r"\b(layer|rename layer|standardize)\b", "layers"),
    (r"\b(regulation|by-?law|ubbl|fire|bomba|building code)\b", "regulations"),
    (r"\b(rule|rule set|compliance rule)\b", "rules"),
]


def _classify_intent(question: str) -> str:
    """Classify user intent via keyword pattern matching."""
    q = question.lower()
    for pattern, intent in _INTENT_PATTERNS:
        if re.search(pattern, q):
            return intent
    return "regulations"  # default: query knowledge base


def route_question(question: str, folder_path: str | None = None) -> dict:
    """Route a natural language question to the appropriate operation."""
    intent = _classify_intent(question)
    folder = Path(folder_path) if folder_path else None

    if intent == "regulations":
        content = query_knowledge_base(question)
        return {
            "intent": "regulations",
            "question": question,
            "answer": content,
            "explanation": "Searched the knowledge base for relevant regulations.",
        }

    if intent == "rules":
        from autocad_batch_commander.operations.compliance_ops import (
            check_compliance,
            list_rule_sets,
        )
        from autocad_batch_commander.models import ComplianceCheckRequest

        rule_sets_list = list_rule_sets()
        request = ComplianceCheckRequest(rule_sets=rule_sets_list[:3])
        result = check_compliance(request)
        return {
            "intent": "rules",
            "question": question,
            "answer": result.model_dump(),
            "explanation": f"Listed {len(rule_sets_list)} rule sets with {result.total_rules} applicable rules.",
        }

    # For drawing operations, we need a folder
    if folder is None:
        return {
            "intent": intent,
            "question": question,
            "answer": None,
            "explanation": f"I understand you want to {intent.replace('_', ' ')}, but I need a folder_path to work with DWG files. Please provide the folder_path parameter.",
        }

    from autocad_batch_commander.acad.factory import get_acad_adapter

    adapter = get_acad_adapter(folder=folder)

    if intent == "extract_dimensions":
        from autocad_batch_commander.operations.geometry_ops import extract_dimensions
        from autocad_batch_commander.models import DimensionExtractionRequest

        result = extract_dimensions(adapter, DimensionExtractionRequest(folder=folder))
        return {
            "intent": intent,
            "question": question,
            "answer": result.model_dump(),
            "explanation": f"Extracted {result.total_dimensions} dimensions from {result.files_processed} files.",
        }

    if intent == "extract_areas":
        from autocad_batch_commander.operations.geometry_ops import extract_areas
        from autocad_batch_commander.models import AreaExtractionRequest

        result = extract_areas(adapter, AreaExtractionRequest(folder=folder))
        return {
            "intent": intent,
            "question": question,
            "answer": result.model_dump(),
            "explanation": f"Extracted {result.total_areas} closed polyline areas from {result.files_processed} files.",
        }

    if intent == "measure_compliance":
        from autocad_batch_commander.operations.geometry_ops import measure_compliance
        from autocad_batch_commander.models import ComplianceMeasurementRequest

        result = measure_compliance(
            adapter, ComplianceMeasurementRequest(folder=folder)
        )
        return {
            "intent": intent,
            "question": question,
            "answer": result.model_dump(),
            "explanation": f"Checked {result.total_checks} measurements: {result.pass_count} pass, {result.fail_count} fail.",
        }

    if intent == "xref_list":
        from autocad_batch_commander.operations.xref_ops import manage_xrefs
        from autocad_batch_commander.models import XrefManageRequest

        result = manage_xrefs(adapter, XrefManageRequest(folder=folder, action="list"))
        return {
            "intent": intent,
            "question": question,
            "answer": result.model_dump(),
            "explanation": f"Found {result.total_xrefs} external references across {result.files_processed} files.",
        }

    if intent == "search":
        from autocad_batch_commander.operations.drawing_ops import drawing_search
        from autocad_batch_commander.models import DrawingSearchRequest

        # Extract search term from question
        search_text = question  # simplified; real impl could parse better
        result = drawing_search(
            adapter, DrawingSearchRequest(folder=folder, search_text=search_text)
        )
        return {
            "intent": intent,
            "question": question,
            "answer": result.model_dump(),
            "explanation": f"Found {result.total_matches} matches across {result.files_processed} files.",
        }

    if intent == "drawing_info":
        from autocad_batch_commander.operations.drawing_ops import get_drawing_info
        from autocad_batch_commander.models import DrawingInfoRequest

        result = get_drawing_info(adapter, DrawingInfoRequest(folder=folder))
        return {
            "intent": intent,
            "question": question,
            "answer": result.model_dump(),
            "explanation": f"Summarized {result.files_processed} drawing files.",
        }

    if intent == "purge":
        from autocad_batch_commander.operations.drawing_ops import batch_purge
        from autocad_batch_commander.models import BatchPurgeRequest

        result = batch_purge(adapter, BatchPurgeRequest(folder=folder))
        return {
            "intent": intent,
            "question": question,
            "answer": result.model_dump(),
            "explanation": f"Purged {result.total_items_purged} items from {result.files_purged} files.",
        }

    if intent == "plot":
        from autocad_batch_commander.operations.drawing_ops import batch_plot
        from autocad_batch_commander.models import BatchPlotRequest

        result = batch_plot(adapter, BatchPlotRequest(folder=folder))
        return {
            "intent": intent,
            "question": question,
            "answer": result.model_dump(),
            "explanation": f"Plotted {result.files_plotted} layouts from {result.files_processed} files.",
        }

    # Fallback
    content = query_knowledge_base(question)
    return {
        "intent": "regulations",
        "question": question,
        "answer": content,
        "explanation": "Searched the knowledge base for relevant information.",
    }
