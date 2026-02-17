"""Typer CLI entry point for AutoCAD Batch Commander."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from autocad_batch_commander import __version__
from autocad_batch_commander.acad.factory import get_acad_adapter
from autocad_batch_commander.cli.formatters import (
    print_area_result,
    print_audit_result,
    print_compliance_result,
    print_dimension_result,
    print_drawing_info_result,
    print_measurement_result,
    print_operation_result,
    print_plot_result,
    print_purge_result,
    print_regulation_result,
    print_schedule_result,
    print_search_result,
    print_xref_result,
)
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
from autocad_batch_commander.operations import (
    block_ops,
    drawing_ops,
    geometry_ops,
    xref_ops,
)
from autocad_batch_commander.operations.audit_ops import audit_drawings
from autocad_batch_commander.operations.compliance_ops import (
    check_compliance,
    list_rule_sets,
)
from autocad_batch_commander.operations.layer_ops import (
    batch_rename_layer,
    batch_standardize_layers,
)
from autocad_batch_commander.operations.text_ops import batch_find_replace

app = typer.Typer(
    name="autocad-cmd",
    help="AutoCAD Batch Commander — bulk operations for AutoCAD drawings.",
    add_completion=False,
)
console = Console()


# ── Existing commands ─────────────────────────────────────────────


@app.command()
def change_text(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    find: str = typer.Option(..., "--find", help="Text to find"),
    replace: str = typer.Option(..., "--replace", help="Text to replace with"),
    layers: Optional[str] = typer.Option(
        None, "--layers", "-l", help="Comma-separated layer filter"
    ),
    case_sensitive: bool = typer.Option(
        False, "--case-sensitive", help="Case-sensitive search"
    ),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backups"),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Find and replace text across multiple AutoCAD drawings."""
    console.print(f"\nScanning folder: {folder}")

    layer_list = [s.strip() for s in layers.split(",")] if layers else None
    request = TextReplaceRequest(
        folder=folder,
        find_text=find,
        replace_text=replace,
        layers=layer_list,
        case_sensitive=case_sensitive,
        backup=backup,
    )

    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = batch_find_replace(adapter, request)
    print_operation_result(result)


@app.command()
def rename_layer(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    old_name: str = typer.Option(..., "--old-name", help="Current layer name"),
    new_name: str = typer.Option(..., "--new-name", help="New layer name"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backups"),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Rename a layer across multiple AutoCAD drawings."""
    console.print(f"\nRenaming layer: {old_name} -> {new_name}")
    console.print(f"Folder: {folder}")

    request = LayerRenameRequest(
        folder=folder,
        old_name=old_name,
        new_name=new_name,
        backup=backup,
    )

    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = batch_rename_layer(adapter, request)
    print_operation_result(result)


@app.command()
def standardize_layers(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    standard: str = typer.Option(
        "AIA", "--standard", "-s", help="Standard: AIA, BS1192, UBBL"
    ),
    report_only: bool = typer.Option(
        False, "--report-only", help="Only report; don't modify"
    ),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backups"),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Standardize layer names across multiple AutoCAD drawings."""
    console.print(f"\nStandardizing layers to: {standard}")
    console.print(f"Folder: {folder}")

    request = LayerStandardizeRequest(
        folder=folder,
        standard=standard,
        report_only=report_only,
        backup=backup,
    )

    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = batch_standardize_layers(adapter, request)
    print_operation_result(result)


@app.command()
def audit(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    standard: str = typer.Option(
        "AIA", "--standard", "-s", help="Standard: AIA, BS1192, UBBL"
    ),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Audit drawings for layer compliance."""
    console.print(f"\nAuditing drawings in: {folder}")
    console.print(f"Standard: {standard}")

    request = AuditRequest(folder=folder, standard=standard)

    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = audit_drawings(adapter, request)
    print_audit_result(result)


@app.command()
def query(
    question: str = typer.Argument(..., help="Question about building regulations"),
) -> None:
    """Query Malaysian building regulations knowledge base."""
    console.print(f"\nQuerying regulations: {question}")

    content = query_knowledge_base(question)
    print_regulation_result(question, content)


@app.command()
def check_compliance_cmd(
    rule_sets: Optional[str] = typer.Option(
        None,
        "--rules",
        "-r",
        help="Comma-separated rule set names (default: ubbl-spatial,ubbl-fire)",
    ),
    building_type: Optional[str] = typer.Option(
        None,
        "--building-type",
        "-b",
        help="Building type: residential, commercial, office, etc.",
    ),
    categories: Optional[str] = typer.Option(
        None, "--categories", "-c", help="Comma-separated categories to filter"
    ),
    folder: Optional[Path] = typer.Option(
        None, "--folder", "-f", help="Folder containing DWG files"
    ),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Check compliance against Malaysian building regulation rules."""
    rs = (
        [s.strip() for s in rule_sets.split(",")]
        if rule_sets
        else ["ubbl-spatial", "ubbl-fire"]
    )
    cats = [s.strip() for s in categories.split(",")] if categories else None

    console.print(f"\nChecking compliance: {', '.join(rs)}")
    if building_type:
        console.print(f"Building type: {building_type}")

    request = ComplianceCheckRequest(
        rule_sets=rs,
        building_type=building_type,
        categories=cats,
        folder=folder,
    )
    result = check_compliance(request)
    print_compliance_result(result)


@app.command()
def list_rules() -> None:
    """List available compliance rule sets."""
    rule_sets_list = list_rule_sets()
    console.print("\n[bold]Available Compliance Rule Sets[/bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    if rule_sets_list:
        for rs in rule_sets_list:
            console.print(f"  • {rs}")
    else:
        console.print("  No rule sets found.")
    console.print()


# ── New geometry commands ─────────────────────────────────────────


@app.command()
def extract_dims(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    layers: Optional[str] = typer.Option(
        None, "--layers", "-l", help="Comma-separated layer filter"
    ),
    dim_types: Optional[str] = typer.Option(
        None, "--types", "-t", help="Dimension types: linear,aligned,angular"
    ),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Extract dimensions from AutoCAD drawings."""
    console.print(f"\nExtracting dimensions from: {folder}")

    layer_list = [s.strip() for s in layers.split(",")] if layers else None
    type_list = [s.strip() for s in dim_types.split(",")] if dim_types else None

    request = DimensionExtractionRequest(
        folder=folder, layers=layer_list, dimension_types=type_list
    )
    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = geometry_ops.extract_dimensions(adapter, request)
    print_dimension_result(result)


@app.command()
def extract_areas(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    layers: Optional[str] = typer.Option(
        None, "--layers", "-l", help="Comma-separated layer filter"
    ),
    min_area: Optional[float] = typer.Option(
        None, "--min-area", help="Minimum area filter (sq mm)"
    ),
    max_area: Optional[float] = typer.Option(
        None, "--max-area", help="Maximum area filter (sq mm)"
    ),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Extract areas from closed polylines in AutoCAD drawings."""
    console.print(f"\nExtracting areas from: {folder}")

    layer_list = [s.strip() for s in layers.split(",")] if layers else None
    request = AreaExtractionRequest(
        folder=folder, layers=layer_list, min_area=min_area, max_area=max_area
    )
    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = geometry_ops.extract_areas(adapter, request)
    print_area_result(result)


@app.command()
def check_drawing(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    rule_sets: Optional[str] = typer.Option(
        "ubbl-spatial", "--rules", "-r", help="Comma-separated rule set names"
    ),
    building_type: Optional[str] = typer.Option(
        None, "--building-type", "-b", help="Building type filter"
    ),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Measure drawing dimensions against compliance rules."""
    rs = [s.strip() for s in rule_sets.split(",")] if rule_sets else ["ubbl-spatial"]
    console.print(f"\nChecking drawing compliance: {', '.join(rs)}")
    console.print(f"Folder: {folder}")

    request = ComplianceMeasurementRequest(
        folder=folder, rule_sets=rs, building_type=building_type
    )
    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = geometry_ops.measure_compliance(adapter, request)
    print_measurement_result(result)


# ── New block commands ────────────────────────────────────────────


@app.command()
def update_titleblock(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    block_name: str = typer.Option(
        "TITLE_BLOCK", "--block-name", "-n", help="Title block name"
    ),
    updates: str = typer.Option(
        ...,
        "--updates",
        "-u",
        help="Comma-separated TAG=VALUE pairs (e.g. DATE=2024-01-01,DRAWN_BY=AH)",
    ),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backups"),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Update title block attributes across drawings."""
    console.print(f"\nUpdating title blocks: {block_name}")

    update_dict: dict[str, str] = {}
    for pair in updates.split(","):
        if "=" in pair:
            tag, value = pair.split("=", 1)
            update_dict[tag.strip()] = value.strip()

    request = TitleBlockUpdateRequest(
        folder=folder, block_name=block_name, updates=update_dict, backup=backup
    )
    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = block_ops.batch_update_title_blocks(adapter, request)
    print_operation_result(result)


@app.command()
def extract_schedule(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    block_name: str = typer.Option(
        ..., "--block-name", "-n", help="Block name to extract schedule from"
    ),
    tags: Optional[str] = typer.Option(
        None, "--tags", "-t", help="Comma-separated attribute tags to extract"
    ),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Extract schedule data from block attributes."""
    console.print(f"\nExtracting schedule: {block_name}")

    tag_list = [s.strip() for s in tags.split(",")] if tags else None
    request = ScheduleExtractionRequest(
        folder=folder, block_name=block_name, tags=tag_list
    )
    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = block_ops.extract_schedule(adapter, request)
    print_schedule_result(result)


# ── New XREF commands ─────────────────────────────────────────────


@app.command()
def manage_xrefs_cmd(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    action: str = typer.Option(
        "list", "--action", "-a", help="Action: list, reload, attach, detach"
    ),
    xref_name: Optional[str] = typer.Option(
        None, "--xref-name", "-n", help="XREF name"
    ),
    xref_path: Optional[str] = typer.Option(
        None, "--xref-path", help="XREF file path (for attach)"
    ),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Manage external references across drawings."""
    console.print(f"\nXREF {action}: {folder}")

    request = XrefManageRequest(
        folder=folder, action=action, xref_name=xref_name, xref_path=xref_path
    )
    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = xref_ops.manage_xrefs(adapter, request)
    print_xref_result(result)


# ── New drawing utility commands ──────────────────────────────────


@app.command()
def search_drawings(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    search_text: str = typer.Option(..., "--text", "-t", help="Text to search for"),
    search_in: Optional[str] = typer.Option(
        "text,attributes,layers",
        "--search-in",
        "-s",
        help="Where to search: text,attributes,layers",
    ),
    case_sensitive: bool = typer.Option(
        False, "--case-sensitive", help="Case-sensitive search"
    ),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Search for text across drawings."""
    console.print(f"\nSearching for: {search_text}")

    search_in_list = (
        [s.strip() for s in search_in.split(",")] if search_in else ["text"]
    )
    request = DrawingSearchRequest(
        folder=folder,
        search_text=search_text,
        search_in=search_in_list,
        case_sensitive=case_sensitive,
    )
    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = drawing_ops.drawing_search(adapter, request)
    print_search_result(result)


@app.command()
def batch_plot_cmd(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-o", help="Output directory"
    ),
    layout: Optional[str] = typer.Option(
        None, "--layout", help="Layout name (default: all)"
    ),
    output_format: str = typer.Option(
        "PDF", "--format", help="Output format: PDF or DWF"
    ),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Batch plot drawings to PDF/DWF."""
    console.print(f"\nBatch plotting: {folder}")

    request = BatchPlotRequest(
        folder=folder,
        output_dir=output_dir,
        layout_name=layout,
        output_format=output_format,
    )
    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = drawing_ops.batch_plot(adapter, request)
    print_plot_result(result)


@app.command()
def purge(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    do_audit: bool = typer.Option(
        True, "--audit/--no-audit", help="Run audit after purge"
    ),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backups"),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Purge unused items from drawings."""
    console.print(f"\nPurging: {folder}")

    request = BatchPurgeRequest(folder=folder, audit=do_audit, backup=backup)
    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = drawing_ops.batch_purge(adapter, request)
    print_purge_result(result)


@app.command()
def drawing_info(
    folder: Path = typer.Option(
        ..., "--folder", "-f", help="Folder containing DWG files"
    ),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Show drawing info summary for each DWG file."""
    console.print(f"\nDrawing info: {folder}")

    request = DrawingInfoRequest(folder=folder)
    adapter = get_acad_adapter(use_mock=mock, folder=folder)
    result = drawing_ops.get_drawing_info(adapter, request)
    print_drawing_info_result(result)


# ── Server + Version ──────────────────────────────────────────────


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
) -> None:
    """Launch the web API and UI server."""
    try:
        import uvicorn
    except ImportError:
        console.print(
            "[red]Web dependencies not installed. Run:[/red]\n"
            "  pip install autocad-batch-commander[web]"
        )
        raise typer.Exit(1)

    console.print(f"\nStarting web server at http://{host}:{port}")
    uvicorn.run("autocad_batch_commander.web.api:app", host=host, port=port)


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"\n[bold]AutoCAD Batch Commander[/bold]  v{__version__}")
    console.print("Author: Hazman")
    console.print("License: MIT\n")


if __name__ == "__main__":
    app()
