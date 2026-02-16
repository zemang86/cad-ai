"""Typer CLI entry point for AutoCAD Batch Commander."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from autocad_batch_commander import __version__
from autocad_batch_commander.acad.factory import get_acad_adapter
from autocad_batch_commander.cli.formatters import print_audit_result, print_operation_result
from autocad_batch_commander.models import (
    AuditRequest,
    LayerRenameRequest,
    LayerStandardizeRequest,
    TextReplaceRequest,
)
from autocad_batch_commander.operations.audit_ops import audit_drawings
from autocad_batch_commander.operations.layer_ops import batch_rename_layer, batch_standardize_layers
from autocad_batch_commander.operations.text_ops import batch_find_replace

app = typer.Typer(
    name="autocad-cmd",
    help="AutoCAD Batch Commander — bulk operations for AutoCAD drawings.",
    add_completion=False,
)
console = Console()


@app.command()
def change_text(
    folder: Path = typer.Option(..., "--folder", "-f", help="Folder containing DWG files"),
    find: str = typer.Option(..., "--find", help="Text to find"),
    replace: str = typer.Option(..., "--replace", help="Text to replace with"),
    layers: Optional[str] = typer.Option(None, "--layers", "-l", help="Comma-separated layer filter"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", help="Case-sensitive search"),
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

    adapter = get_acad_adapter(use_mock=mock)
    result = batch_find_replace(adapter, request)
    print_operation_result(result)


@app.command()
def rename_layer(
    folder: Path = typer.Option(..., "--folder", "-f", help="Folder containing DWG files"),
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

    adapter = get_acad_adapter(use_mock=mock)
    result = batch_rename_layer(adapter, request)
    print_operation_result(result)


@app.command()
def standardize_layers(
    folder: Path = typer.Option(..., "--folder", "-f", help="Folder containing DWG files"),
    standard: str = typer.Option("AIA", "--standard", "-s", help="Standard: AIA, BS1192, UBBL"),
    report_only: bool = typer.Option(False, "--report-only", help="Only report; don't modify"),
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

    adapter = get_acad_adapter(use_mock=mock)
    result = batch_standardize_layers(adapter, request)
    print_operation_result(result)


@app.command()
def audit(
    folder: Path = typer.Option(..., "--folder", "-f", help="Folder containing DWG files"),
    standard: str = typer.Option("AIA", "--standard", "-s", help="Standard: AIA, BS1192, UBBL"),
    mock: bool = typer.Option(False, "--mock", help="Use mock adapter (testing)"),
) -> None:
    """Audit drawings for layer compliance."""
    console.print(f"\nAuditing drawings in: {folder}")
    console.print(f"Standard: {standard}")

    request = AuditRequest(folder=folder, standard=standard)

    adapter = get_acad_adapter(use_mock=mock)
    result = audit_drawings(adapter, request)
    print_audit_result(result)


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"\n[bold]AutoCAD Batch Commander[/bold]  v{__version__}")
    console.print("Author: Hazman")
    console.print("License: MIT\n")


if __name__ == "__main__":
    app()
