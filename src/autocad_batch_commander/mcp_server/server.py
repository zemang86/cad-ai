"""FastMCP server exposing AutoCAD batch operations as MCP tools."""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from autocad_batch_commander.acad.factory import get_acad_adapter
from autocad_batch_commander.knowledge.loader import query_knowledge_base
from autocad_batch_commander.models import (
    AuditRequest,
    ComplianceCheckRequest,
    LayerRenameRequest,
    LayerStandardizeRequest,
    TextReplaceRequest,
)
from autocad_batch_commander.operations.audit_ops import audit_drawings
from autocad_batch_commander.operations.compliance_ops import check_compliance, list_rule_sets
from autocad_batch_commander.operations.layer_ops import batch_rename_layer, batch_standardize_layers
from autocad_batch_commander.operations.text_ops import batch_find_replace

mcp = FastMCP("autocad-batch-commander")


@mcp.tool()
def batch_change_text(
    folder_path: str,
    find_text: str,
    replace_text: str,
    layers: list[str] | None = None,
    case_sensitive: bool = False,
    backup: bool = True,
) -> dict:
    """Find and replace text across multiple AutoCAD drawings.

    Args:
        folder_path: Path to folder containing DWG files.
        find_text: Text string to find.
        replace_text: Text string to replace with.
        layers: Optional list of layer names to restrict the search.
        case_sensitive: Whether the search is case-sensitive.
        backup: Create backup before modifying.
    """
    adapter = get_acad_adapter()
    request = TextReplaceRequest(
        folder=Path(folder_path),
        find_text=find_text,
        replace_text=replace_text,
        layers=layers,
        case_sensitive=case_sensitive,
        backup=backup,
    )
    result = batch_find_replace(adapter, request)
    return result.model_dump()


@mcp.tool()
def batch_rename_layer_tool(
    folder_path: str,
    old_layer_name: str,
    new_layer_name: str,
    backup: bool = True,
) -> dict:
    """Rename a layer across multiple AutoCAD drawings.

    Args:
        folder_path: Path to folder containing DWG files.
        old_layer_name: Current layer name.
        new_layer_name: New layer name.
        backup: Create backup before modifying.
    """
    adapter = get_acad_adapter()
    request = LayerRenameRequest(
        folder=Path(folder_path),
        old_name=old_layer_name,
        new_name=new_layer_name,
        backup=backup,
    )
    result = batch_rename_layer(adapter, request)
    return result.model_dump()


@mcp.tool()
def standardize_layers(
    folder_path: str,
    standard: str = "AIA",
    report_only: bool = False,
    backup: bool = True,
) -> dict:
    """Standardize layer names to a naming convention (AIA, BS1192, UBBL).

    Args:
        folder_path: Path to folder containing DWG files.
        standard: Naming standard to apply (AIA, BS1192, UBBL).
        report_only: If true, only report changes without applying.
        backup: Create backup before modifying.
    """
    adapter = get_acad_adapter()
    request = LayerStandardizeRequest(
        folder=Path(folder_path),
        standard=standard,
        report_only=report_only,
        backup=backup,
    )
    result = batch_standardize_layers(adapter, request)
    return result.model_dump()


@mcp.tool()
def audit_drawings_tool(
    folder_path: str,
    standard: str = "AIA",
) -> dict:
    """Audit drawings for layer compliance against a naming standard.

    Args:
        folder_path: Path to folder containing DWG files.
        standard: Naming standard to check against (AIA, BS1192, UBBL).
    """
    adapter = get_acad_adapter()
    request = AuditRequest(folder=Path(folder_path), standard=standard)
    result = audit_drawings(adapter, request)
    return result.model_dump()


@mcp.tool()
def query_regulations(
    query: str,
) -> dict:
    """Query Malaysian building regulations knowledge base.

    Searches the knowledge base for relevant regulations and returns
    Markdown content with by-law citations. Use this to answer questions
    about UBBL, Fire By-Laws, Bomba guidelines, and other Malaysian
    building regulations.

    Args:
        query: Natural language question about building regulations.
    """
    content = query_knowledge_base(query)
    return {
        "query": query,
        "files_loaded": len(content),
        "content": content,
    }


@mcp.tool()
def check_compliance_tool(
    rule_sets: list[str] | None = None,
    building_type: str | None = None,
    categories: list[str] | None = None,
) -> dict:
    """Check applicable compliance rules from Malaysian building regulations.

    Loads structured compliance rules and returns findings that apply to
    the specified building type and categories. Rules include numeric
    thresholds (dimensions, durations, percentages) with by-law references.

    Args:
        rule_sets: Rule set names to check (default: ubbl-spatial, ubbl-fire).
        building_type: Filter rules by building type (residential, commercial, office, etc.).
        categories: Filter rules by category (room_size, corridor, fire_resistance, etc.).
    """
    request = ComplianceCheckRequest(
        rule_sets=rule_sets or ["ubbl-spatial", "ubbl-fire"],
        building_type=building_type,
        categories=categories,
    )
    result = check_compliance(request)
    return result.model_dump()


@mcp.tool()
def list_available_rules() -> dict:
    """List all available compliance rule sets.

    Returns the names of all JSON rule files in standards/rules/.
    """
    return {"rule_sets": list_rule_sets()}


if __name__ == "__main__":
    mcp.run()
