"""FastMCP server exposing AutoCAD batch operations as MCP tools."""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from autocad_batch_commander.acad.factory import get_acad_adapter
from autocad_batch_commander.knowledge.loader import query_knowledge_base
from autocad_batch_commander.models import (
    AreaExtractionRequest,
    AuditRequest,
    BatchPlotRequest,
    BatchPurgeRequest,
    ComplianceCheckRequest,
    ComplianceMeasurementRequest,
    DimensionExtractionRequest,
    DrawingInfoRequest,
    DrawingSearchRequest,
    LayerRenameRequest,
    LayerStandardizeRequest,
    ScheduleExtractionRequest,
    TextReplaceRequest,
    TitleBlockUpdateRequest,
    XrefManageRequest,
)
from autocad_batch_commander.operations.audit_ops import audit_drawings
from autocad_batch_commander.operations.block_ops import (
    batch_update_title_blocks,
    extract_schedule,
)
from autocad_batch_commander.operations.compliance_ops import (
    check_compliance,
    list_rule_sets,
)
from autocad_batch_commander.operations.drawing_ops import (
    batch_plot,
    batch_purge,
    drawing_search,
    get_drawing_info,
)
from autocad_batch_commander.operations.geometry_ops import (
    extract_areas,
    extract_dimensions,
    measure_compliance,
)
from autocad_batch_commander.operations.layer_ops import (
    batch_rename_layer,
    batch_standardize_layers,
)
from autocad_batch_commander.operations.text_ops import batch_find_replace
from autocad_batch_commander.operations.xref_ops import manage_xrefs

mcp = FastMCP("autocad-batch-commander")


# ── Existing tools ────────────────────────────────────────────────


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
def standardize_layers_tool(
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
    Markdown content with by-law citations.

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

    Args:
        rule_sets: Rule set names to check (default: ubbl-spatial, ubbl-fire).
        building_type: Filter rules by building type.
        categories: Filter rules by category.
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
    """List all available compliance rule sets."""
    return {"rule_sets": list_rule_sets()}


# ── New geometry tools ────────────────────────────────────────────


@mcp.tool()
def extract_dimensions_tool(
    folder_path: str,
    layers: list[str] | None = None,
    dimension_types: list[str] | None = None,
) -> dict:
    """Extract all dimension entities from AutoCAD drawings.

    Args:
        folder_path: Path to folder containing DWG files.
        layers: Optional layer name filter.
        dimension_types: Optional filter: linear, aligned, angular, radial, diametric.
    """
    adapter = get_acad_adapter()
    request = DimensionExtractionRequest(
        folder=Path(folder_path), layers=layers, dimension_types=dimension_types
    )
    result = extract_dimensions(adapter, request)
    return result.model_dump()


@mcp.tool()
def extract_areas_tool(
    folder_path: str,
    layers: list[str] | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
) -> dict:
    """Extract areas from closed polylines in AutoCAD drawings.

    Args:
        folder_path: Path to folder containing DWG files.
        layers: Optional layer name filter.
        min_area: Minimum area filter (sq mm).
        max_area: Maximum area filter (sq mm).
    """
    adapter = get_acad_adapter()
    request = AreaExtractionRequest(
        folder=Path(folder_path), layers=layers, min_area=min_area, max_area=max_area
    )
    result = extract_areas(adapter, request)
    return result.model_dump()


@mcp.tool()
def measure_compliance_tool(
    folder_path: str,
    rule_sets: list[str] | None = None,
    building_type: str | None = None,
) -> dict:
    """Measure drawing dimensions against compliance rules automatically.

    Extracts dimensions from drawings and compares against UBBL rule
    thresholds. Uses layer-to-rule mapping to determine which rules
    apply to which dimensions.

    Args:
        folder_path: Path to folder containing DWG files.
        rule_sets: Rule set names (default: ubbl-spatial).
        building_type: Building type filter.
    """
    adapter = get_acad_adapter()
    request = ComplianceMeasurementRequest(
        folder=Path(folder_path),
        rule_sets=rule_sets or ["ubbl-spatial"],
        building_type=building_type,
    )
    result = measure_compliance(adapter, request)
    return result.model_dump()


# ── New block tools ───────────────────────────────────────────────


@mcp.tool()
def update_title_blocks_tool(
    folder_path: str,
    updates: dict[str, str],
    block_name: str = "TITLE_BLOCK",
    backup: bool = True,
) -> dict:
    """Update title block attributes across all drawings.

    Args:
        folder_path: Path to folder containing DWG files.
        updates: Dict of TAG -> VALUE pairs to update.
        block_name: Name of the title block (default: TITLE_BLOCK).
        backup: Create backup before modifying.
    """
    adapter = get_acad_adapter()
    request = TitleBlockUpdateRequest(
        folder=Path(folder_path),
        block_name=block_name,
        updates=updates,
        backup=backup,
    )
    result = batch_update_title_blocks(adapter, request)
    return result.model_dump()


@mcp.tool()
def extract_schedule_tool(
    folder_path: str,
    block_name: str,
    tags: list[str] | None = None,
) -> dict:
    """Extract schedule data from block attributes across drawings.

    Useful for generating door schedules, window schedules, room schedules
    from attributed blocks.

    Args:
        folder_path: Path to folder containing DWG files.
        block_name: Name of the block to extract data from.
        tags: Optional list of specific attribute tags to extract.
    """
    adapter = get_acad_adapter()
    request = ScheduleExtractionRequest(
        folder=Path(folder_path), block_name=block_name, tags=tags
    )
    result = extract_schedule(adapter, request)
    return result.model_dump()


# ── New XREF tools ────────────────────────────────────────────────


@mcp.tool()
def manage_xrefs_tool(
    folder_path: str,
    action: str = "list",
    xref_name: str | None = None,
    xref_path: str | None = None,
    xref_type: str = "attach",
) -> dict:
    """Manage external references across drawings.

    Args:
        folder_path: Path to folder containing DWG files.
        action: list, reload, attach, or detach.
        xref_name: XREF name (required for reload/attach/detach).
        xref_path: XREF file path (required for attach).
        xref_type: attach or overlay (for attach action).
    """
    adapter = get_acad_adapter()
    request = XrefManageRequest(
        folder=Path(folder_path),
        action=action,
        xref_name=xref_name,
        xref_path=xref_path,
        xref_type=xref_type,
    )
    result = manage_xrefs(adapter, request)
    return result.model_dump()


# ── New drawing utility tools ─────────────────────────────────────


@mcp.tool()
def search_drawings_tool(
    folder_path: str,
    search_text: str,
    search_in: list[str] | None = None,
    case_sensitive: bool = False,
) -> dict:
    """Search for text across drawings in text entities, block attributes, and layer names.

    Args:
        folder_path: Path to folder containing DWG files.
        search_text: Text to search for.
        search_in: Where to search: text, attributes, layers (default: all).
        case_sensitive: Case-sensitive search.
    """
    adapter = get_acad_adapter()
    request = DrawingSearchRequest(
        folder=Path(folder_path),
        search_text=search_text,
        search_in=search_in or ["text", "attributes", "layers"],
        case_sensitive=case_sensitive,
    )
    result = drawing_search(adapter, request)
    return result.model_dump()


@mcp.tool()
def batch_plot_tool(
    folder_path: str,
    output_dir: str | None = None,
    layout_name: str | None = None,
    output_format: str = "PDF",
) -> dict:
    """Batch plot drawing layouts to PDF or DWF.

    Args:
        folder_path: Path to folder containing DWG files.
        output_dir: Output directory (default: <folder>/plots/).
        layout_name: Specific layout to plot (default: all non-Model layouts).
        output_format: PDF or DWF.
    """
    adapter = get_acad_adapter()
    request = BatchPlotRequest(
        folder=Path(folder_path),
        output_dir=Path(output_dir) if output_dir else None,
        layout_name=layout_name,
        output_format=output_format,
    )
    result = batch_plot(adapter, request)
    return result.model_dump()


@mcp.tool()
def batch_purge_tool(
    folder_path: str,
    audit: bool = True,
    backup: bool = True,
) -> dict:
    """Purge unused items from drawings and optionally audit for errors.

    Args:
        folder_path: Path to folder containing DWG files.
        audit: Run audit after purge.
        backup: Create backup before modifying.
    """
    adapter = get_acad_adapter()
    request = BatchPurgeRequest(folder=Path(folder_path), audit=audit, backup=backup)
    result = batch_purge(adapter, request)
    return result.model_dump()


@mcp.tool()
def get_drawing_info_tool(
    folder_path: str,
) -> dict:
    """Get comprehensive drawing info summary for each DWG file.

    Returns layer count, text count, dimension count, block count,
    polyline count, XREF count, layout count, and drawing extents.

    Args:
        folder_path: Path to folder containing DWG files.
    """
    adapter = get_acad_adapter()
    request = DrawingInfoRequest(folder=Path(folder_path))
    result = get_drawing_info(adapter, request)
    return result.model_dump()


# ── Natural language tool ─────────────────────────────────────────


@mcp.tool()
def ask_araiden(
    question: str,
    folder_path: str | None = None,
) -> dict:
    """Natural language interface to ARAIDEN CAD automation.

    Ask a question or give an instruction in plain English. ARAIDEN will
    classify the intent and route to the appropriate structured operation.

    Examples:
      - "What dimensions are in my floor plan?"
      - "Update the title block date to 2024-06-01"
      - "Check if corridor widths comply with UBBL"
      - "List all external references"
      - "What's the minimum bedroom size under UBBL?"

    Args:
        question: Natural language question or instruction.
        folder_path: Optional folder containing DWG files.
    """
    from autocad_batch_commander.mcp_server.nl_router import route_question

    return route_question(question, folder_path)


if __name__ == "__main__":
    mcp.run()
