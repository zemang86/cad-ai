"""Pydantic models for requests, results, and drawing entities."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


# ── Drawing entities ──────────────────────────────────────────────


class TextEntity(BaseModel):
    """A text or mtext entity inside a drawing."""

    handle: str
    text: str
    layer: str
    entity_type: str = "AcDbText"  # AcDbText | AcDbMText


class LayerEntity(BaseModel):
    """A layer definition inside a drawing."""

    name: str
    color: int = 7
    is_on: bool = True
    is_frozen: bool = False


# ── Requests ──────────────────────────────────────────────────────


class TextReplaceRequest(BaseModel):
    """Parameters for a batch text find-and-replace operation."""

    folder: Path
    find_text: str
    replace_text: str
    layers: list[str] | None = None
    case_sensitive: bool = False
    backup: bool = True


class LayerRenameRequest(BaseModel):
    """Parameters for a batch layer rename operation."""

    folder: Path
    old_name: str
    new_name: str
    backup: bool = True


class LayerStandardizeRequest(BaseModel):
    """Parameters for a batch layer standardization operation."""

    folder: Path
    standard: str = "AIA"
    custom_mappings: dict[str, str] | None = None
    report_only: bool = False
    backup: bool = True


class AuditRequest(BaseModel):
    """Parameters for a drawing audit operation."""

    folder: Path
    standard: str = "AIA"


# ── Results ───────────────────────────────────────────────────────


class FileDetail(BaseModel):
    """Per-file detail in an operation result."""

    file: str
    changes: int = 0
    error: str | None = None


class OperationResult(BaseModel):
    """Result of a batch operation."""

    files_processed: int = 0
    files_modified: int = 0
    total_changes: int = 0
    errors: list[FileDetail] = Field(default_factory=list)
    details: list[FileDetail] = Field(default_factory=list)


class AuditFinding(BaseModel):
    """A single audit finding for one drawing."""

    file: str
    finding_type: str  # e.g. "non_standard_layer", "missing_required_layer"
    severity: str = "warning"  # "error" | "warning" | "info"
    message: str
    layer: str | None = None


class AuditResult(BaseModel):
    """Result of an audit operation."""

    files_processed: int = 0
    total_findings: int = 0
    findings: list[AuditFinding] = Field(default_factory=list)
    compliant_files: int = 0
    non_compliant_files: int = 0


# ── Compliance rules ─────────────────────────────────────────────


class ComplianceRule(BaseModel):
    """A single machine-readable compliance rule."""

    id: str
    description: str
    by_law: str
    category: str
    building_type: list[str] = Field(default_factory=list)
    check_type: str  # min_dimension | max_dimension | min_percentage | min_duration
    parameter: str
    threshold: float
    unit: str
    severity: str = "error"
    tags: list[str] = Field(default_factory=list)


class ComplianceRuleSet(BaseModel):
    """A set of compliance rules from a single source document."""

    source_document: str
    source_short: str
    category: str
    rules: list[ComplianceRule] = Field(default_factory=list)


class ComplianceCheckRequest(BaseModel):
    """Parameters for a compliance check operation."""

    rule_sets: list[str] = Field(default_factory=lambda: ["ubbl-spatial", "ubbl-fire"])
    building_type: str | None = None
    categories: list[str] | None = None
    folder: Path | None = None


class ComplianceFinding(BaseModel):
    """A single compliance finding."""

    rule_id: str
    description: str
    by_law: str
    severity: str = "error"
    status: str = "to_verify"  # to_verify | pass | fail | error
    check_type: str | None = None
    parameter: str | None = None
    threshold: float | None = None
    unit: str | None = None
    tags: list[str] = Field(default_factory=list)


class ComplianceCheckResult(BaseModel):
    """Result of a compliance check."""

    rule_sets_loaded: int = 0
    total_rules: int = 0
    findings: list[ComplianceFinding] = Field(default_factory=list)


# ── Knowledge / regulation queries ───────────────────────────────


class RegulationQuery(BaseModel):
    """A query to the regulation knowledge base."""

    query: str
    topics: list[str] | None = None


class RegulationResult(BaseModel):
    """Result of a regulation knowledge base query."""

    query: str
    files_loaded: int = 0
    content: dict[str, str] = Field(default_factory=dict)
