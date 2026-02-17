"""Rich output helpers for CLI commands."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from autocad_batch_commander.models import (
    AreaExtractionResult,
    AuditResult,
    ComplianceCheckResult,
    ComplianceMeasurementResult,
    DimensionExtractionResult,
    DrawingInfoResult,
    DrawingSearchResult,
    OperationResult,
    PlotResult,
    PurgeResult,
    ScheduleResult,
    XrefListResult,
)

console = Console()


def print_operation_result(result: OperationResult) -> None:
    """Print a summary of a batch operation result."""
    console.print("\n[green bold]Operation Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Files Processed:  {result.files_processed}")
    console.print(f"  Files Modified:   {result.files_modified}")
    console.print(f"  Total Changes:    {result.total_changes}")
    console.print(f"  Errors:           {len(result.errors)}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.errors:
        console.print("\n[yellow bold]Errors:[/yellow bold]")
        for err in result.errors:
            console.print(f"  {err.file}: {err.error}")


def print_audit_result(result: AuditResult) -> None:
    """Print a summary of an audit result."""
    console.print("\n[green bold]Audit Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Files Audited:      {result.files_processed}")
    console.print(f"  Compliant:          {result.compliant_files}")
    console.print(f"  Non-compliant:      {result.non_compliant_files}")
    console.print(f"  Total Findings:     {result.total_findings}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.findings:
        table = Table(title="Findings", show_lines=False)
        table.add_column("File", style="cyan", no_wrap=True, max_width=30)
        table.add_column("Severity", style="bold")
        table.add_column("Type")
        table.add_column("Message")

        for f in result.findings:
            sev_style = "red" if f.severity == "error" else "yellow"
            table.add_row(
                f.file,
                f"[{sev_style}]{f.severity}[/{sev_style}]",
                f.finding_type,
                f.message,
            )

        console.print(table)


def print_regulation_result(query: str, content: dict[str, str]) -> None:
    """Print regulation query results."""
    console.print("\n[green bold]Regulation Query Results[/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Query:        {query}")
    console.print(f"  Files loaded: {len(content)}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if content:
        for file_path, text in content.items():
            console.print(f"\n[cyan bold]── {file_path} ──[/cyan bold]")
            console.print(text)
    else:
        console.print("\n  [yellow]No matching regulation files found.[/yellow]")


def print_compliance_result(result: ComplianceCheckResult) -> None:
    """Print compliance check results."""
    console.print("\n[green bold]Compliance Check Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Rule sets loaded: {result.rule_sets_loaded}")
    console.print(f"  Applicable rules: {result.total_rules}")
    console.print(f"  Total findings:   {len(result.findings)}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.findings:
        table = Table(title="Compliance Findings", show_lines=False)
        table.add_column("Rule ID", style="cyan", no_wrap=True)
        table.add_column("By-Law", style="bold")
        table.add_column("Description")
        table.add_column("Threshold")
        table.add_column("Severity")
        table.add_column("Status")

        for f in result.findings:
            sev_style = "red" if f.severity == "error" else "yellow"
            threshold_str = f"{f.threshold} {f.unit}" if f.threshold is not None else ""
            table.add_row(
                f.rule_id,
                f.by_law,
                f.description,
                threshold_str,
                f"[{sev_style}]{f.severity}[/{sev_style}]",
                f.status,
            )

        console.print(table)


def print_dimension_result(result: DimensionExtractionResult) -> None:
    """Print dimension extraction results."""
    console.print("\n[green bold]Dimension Extraction Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Files Processed:    {result.files_processed}")
    console.print(f"  Total Dimensions:   {result.total_dimensions}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.details:
        table = Table(title="Dimensions", show_lines=False)
        table.add_column("File", style="cyan", max_width=30)
        table.add_column("Type")
        table.add_column("Value", justify="right")
        table.add_column("Layer")
        table.add_column("Override")

        for detail in result.details:
            for dim in detail.dimensions:
                table.add_row(
                    detail.file.split("/")[-1],
                    dim.dimension_type,
                    f"{dim.value:.1f}",
                    dim.layer,
                    dim.text_override or "",
                )

        console.print(table)


def print_area_result(result: AreaExtractionResult) -> None:
    """Print area extraction results."""
    console.print("\n[green bold]Area Extraction Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Files Processed:  {result.files_processed}")
    console.print(f"  Total Areas:      {result.total_areas}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.details:
        table = Table(title="Closed Polyline Areas", show_lines=False)
        table.add_column("File", style="cyan", max_width=30)
        table.add_column("Handle")
        table.add_column("Layer")
        table.add_column("Area (sq mm)", justify="right")
        table.add_column("Perimeter (mm)", justify="right")

        for detail in result.details:
            for poly in detail.areas:
                table.add_row(
                    detail.file.split("/")[-1],
                    poly.handle,
                    poly.layer,
                    f"{poly.area:,.0f}",
                    f"{poly.perimeter:,.0f}",
                )

        console.print(table)


def print_measurement_result(result: ComplianceMeasurementResult) -> None:
    """Print compliance measurement results."""
    console.print("\n[green bold]Compliance Measurement Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Files Processed:  {result.files_processed}")
    console.print(f"  Total Checks:     {result.total_checks}")
    console.print(f"  Pass:             {result.pass_count}")
    console.print(f"  Fail:             {result.fail_count}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.findings:
        table = Table(title="Measurement Findings", show_lines=False)
        table.add_column("File", style="cyan", max_width=25)
        table.add_column("Rule", style="bold")
        table.add_column("Parameter")
        table.add_column("Measured", justify="right")
        table.add_column("Required", justify="right")
        table.add_column("Status")

        for f in result.findings:
            status_style = "green" if f.status == "pass" else "red"
            table.add_row(
                f.file.split("/")[-1],
                f.rule_id,
                f.parameter,
                f"{f.measured_value:.0f} {f.unit}",
                f"{f.threshold:.0f} {f.unit}",
                f"[{status_style}]{f.status.upper()}[/{status_style}]",
            )

        console.print(table)


def print_schedule_result(result: ScheduleResult) -> None:
    """Print schedule extraction results."""
    console.print("\n[green bold]Schedule Extraction Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Block Name:       {result.block_name}")
    console.print(f"  Files Processed:  {result.files_processed}")
    console.print(f"  Total Entries:    {result.total_entries}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.rows:
        # Collect all unique tags for columns
        all_tags = sorted({tag for row in result.rows for tag in row.attributes})
        table = Table(title=f"{result.block_name} Schedule", show_lines=True)
        table.add_column("File", style="cyan", max_width=25)
        for tag in all_tags:
            table.add_column(tag)

        for row in result.rows:
            values = [row.attributes.get(tag, "") for tag in all_tags]
            table.add_row(row.file.split("/")[-1], *values)

        console.print(table)


def print_xref_result(result: XrefListResult) -> None:
    """Print XREF management results."""
    console.print(f"\n[green bold]XREF {result.action.title()} Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Files Processed:  {result.files_processed}")
    if result.action == "list":
        console.print(f"  Total XREFs:      {result.total_xrefs}")
    else:
        console.print(f"  Changes:          {result.changes}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.details:
        table = Table(title="External References", show_lines=False)
        table.add_column("File", style="cyan", max_width=25)
        table.add_column("XREF Name", style="bold")
        table.add_column("Path")
        table.add_column("Type")
        table.add_column("Status")

        for detail in result.details:
            for xref in detail.xrefs:
                status_style = "green" if xref.status == "loaded" else "red"
                table.add_row(
                    detail.file.split("/")[-1],
                    xref.name,
                    xref.path,
                    xref.xref_type,
                    f"[{status_style}]{xref.status}[/{status_style}]",
                )

        console.print(table)


def print_search_result(result: DrawingSearchResult) -> None:
    """Print drawing search results."""
    console.print("\n[green bold]Drawing Search Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Search Text:      {result.search_text}")
    console.print(f"  Files Processed:  {result.files_processed}")
    console.print(f"  Total Matches:    {result.total_matches}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.matches:
        table = Table(title="Search Matches", show_lines=False)
        table.add_column("File", style="cyan", max_width=25)
        table.add_column("Type", style="bold")
        table.add_column("Layer")
        table.add_column("Match")

        for m in result.matches:
            table.add_row(
                m.file.split("/")[-1],
                m.match_type,
                m.layer,
                m.matched_text,
            )

        console.print(table)


def print_plot_result(result: PlotResult) -> None:
    """Print batch plot results."""
    console.print("\n[green bold]Batch Plot Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Files Processed:  {result.files_processed}")
    console.print(f"  Layouts Plotted:  {result.files_plotted}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.details:
        for d in result.details:
            status = "[green]OK[/green]" if not d.error else f"[red]{d.error}[/red]"
            console.print(f"  {d.layout}: {d.output_file} — {status}")


def print_purge_result(result: PurgeResult) -> None:
    """Print batch purge results."""
    console.print("\n[green bold]Batch Purge Complete![/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Files Processed:  {result.files_processed}")
    console.print(f"  Files Purged:     {result.files_purged}")
    console.print(f"  Items Purged:     {result.total_items_purged}")
    console.print(f"  Audit Issues:     {len(result.audit_issues)}")
    console.print("[dim]" + "━" * 40 + "[/dim]")


def print_drawing_info_result(result: DrawingInfoResult) -> None:
    """Print drawing info summary results."""
    console.print("\n[green bold]Drawing Info Summary[/green bold]")
    console.print("[dim]" + "━" * 40 + "[/dim]")
    console.print(f"  Files Processed:  {result.files_processed}")
    console.print("[dim]" + "━" * 40 + "[/dim]")

    if result.details:
        table = Table(title="Drawing Summary", show_lines=True)
        table.add_column("File", style="cyan", max_width=30)
        table.add_column("Layers", justify="right")
        table.add_column("Texts", justify="right")
        table.add_column("Dims", justify="right")
        table.add_column("Blocks", justify="right")
        table.add_column("Polylines", justify="right")
        table.add_column("XREFs", justify="right")
        table.add_column("Layouts", justify="right")

        for d in result.details:
            table.add_row(
                d.file.split("/")[-1],
                str(d.layer_count),
                str(d.text_count),
                str(d.dimension_count),
                str(d.block_count),
                str(d.polyline_count),
                str(d.xref_count),
                str(d.layout_count),
            )

        console.print(table)
