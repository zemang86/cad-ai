"""Rich output helpers for CLI commands."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from autocad_batch_commander.models import AuditResult, ComplianceCheckResult, OperationResult

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
