"""Pydantic models for requests, results, and drawing entities."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


# ── Geometry primitives ──────────────────────────────────────────


class Point2D(BaseModel):
    """A 2D point."""

    x: float
    y: float


class Point3D(BaseModel):
    """A 3D point."""

    x: float
    y: float
    z: float = 0.0


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


class DimensionEntity(BaseModel):
    """A dimension entity inside a drawing."""

    handle: str
    dimension_type: str = "linear"  # linear | aligned | angular | radial | diametric
    value: float = 0.0
    text_override: str = ""
    layer: str = "DIMENSION"
    associated_points: list[Point3D] = Field(default_factory=list)


class PolylineEntity(BaseModel):
    """A polyline entity inside a drawing."""

    handle: str
    vertices: list[Point3D] = Field(default_factory=list)
    closed: bool = False
    area: float = 0.0
    perimeter: float = 0.0
    layer: str = "0"


class BlockReference(BaseModel):
    """A block reference (insert) inside a drawing."""

    handle: str
    name: str
    insertion_point: Point3D = Field(default_factory=lambda: Point3D(x=0, y=0, z=0))
    layer: str = "0"
    rotation: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0


class BlockAttribute(BaseModel):
    """An attribute attached to a block reference."""

    tag: str
    value: str
    handle: str = ""


class XrefInfo(BaseModel):
    """Information about an external reference."""

    name: str
    path: str
    xref_type: str = "attach"  # attach | overlay
    status: str = "loaded"  # loaded | unloaded | not_found


class LayoutInfo(BaseModel):
    """Information about a layout tab."""

    name: str
    paper_size: str = ""
    plot_device: str = ""
    viewport_count: int = 0


class ViewportInfo(BaseModel):
    """Information about a viewport in a layout."""

    handle: str
    center: Point2D = Field(default_factory=lambda: Point2D(x=0, y=0))
    width: float = 0.0
    height: float = 0.0
    scale: float = 1.0
    frozen_layers: list[str] = Field(default_factory=list)


class DrawingExtents(BaseModel):
    """Bounding box of all entities in a drawing."""

    min_point: Point3D = Field(default_factory=lambda: Point3D(x=0, y=0, z=0))
    max_point: Point3D = Field(default_factory=lambda: Point3D(x=0, y=0, z=0))


class AuditIssue(BaseModel):
    """A single issue found by the drawing audit utility."""

    description: str
    fixed: bool = False


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


class DimensionExtractionRequest(BaseModel):
    """Parameters for extracting dimensions from drawings."""

    folder: Path
    layers: list[str] | None = None
    dimension_types: list[str] | None = None  # filter by type


class AreaExtractionRequest(BaseModel):
    """Parameters for extracting areas from closed polylines."""

    folder: Path
    layers: list[str] | None = None
    min_area: float | None = None
    max_area: float | None = None


class ComplianceMeasurementRequest(BaseModel):
    """Parameters for measuring drawing dimensions against compliance rules."""

    folder: Path
    rule_sets: list[str] = Field(default_factory=lambda: ["ubbl-spatial"])
    building_type: str | None = None
    backup: bool = False


class TitleBlockUpdateRequest(BaseModel):
    """Parameters for updating title block attributes across drawings."""

    folder: Path
    block_name: str = "TITLE_BLOCK"
    updates: dict[str, str] = Field(default_factory=dict)  # tag → value
    backup: bool = True


class ScheduleExtractionRequest(BaseModel):
    """Parameters for extracting schedules from block attributes."""

    folder: Path
    block_name: str
    tags: list[str] | None = None  # specific tags to extract


class BlockInsertRequest(BaseModel):
    """Parameters for inserting blocks into drawings."""

    folder: Path
    block_name: str
    insertion_points: list[Point3D] = Field(default_factory=list)
    layer: str = "0"
    rotation: float = 0.0
    scale: float = 1.0
    backup: bool = True


class XrefManageRequest(BaseModel):
    """Parameters for managing external references."""

    folder: Path
    action: str = "list"  # list | reload | attach | detach
    xref_name: str | None = None
    xref_path: str | None = None
    xref_type: str = "attach"  # attach | overlay


class DrawingSearchRequest(BaseModel):
    """Parameters for searching across drawings."""

    folder: Path
    search_text: str
    search_in: list[str] = Field(
        default_factory=lambda: ["text", "attributes", "layers"]
    )
    case_sensitive: bool = False


class BatchPlotRequest(BaseModel):
    """Parameters for batch plotting drawings to PDF/DWF."""

    folder: Path
    output_dir: Path | None = None
    layout_name: str | None = None  # None = all layouts
    output_format: str = "PDF"  # PDF | DWF


class BatchPurgeRequest(BaseModel):
    """Parameters for batch purging unused items from drawings."""

    folder: Path
    audit: bool = True  # also run audit after purge
    backup: bool = True


class DrawingInfoRequest(BaseModel):
    """Parameters for getting drawing info summaries."""

    folder: Path


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


class FileDimensionDetail(BaseModel):
    """Dimensions extracted from a single file."""

    file: str
    dimensions: list[DimensionEntity] = Field(default_factory=list)
    error: str | None = None


class DimensionExtractionResult(BaseModel):
    """Result of a dimension extraction operation."""

    files_processed: int = 0
    total_dimensions: int = 0
    details: list[FileDimensionDetail] = Field(default_factory=list)
    errors: list[FileDetail] = Field(default_factory=list)


class FileAreaDetail(BaseModel):
    """Areas extracted from a single file."""

    file: str
    areas: list[PolylineEntity] = Field(default_factory=list)
    error: str | None = None


class AreaExtractionResult(BaseModel):
    """Result of an area extraction operation."""

    files_processed: int = 0
    total_areas: int = 0
    details: list[FileAreaDetail] = Field(default_factory=list)
    errors: list[FileDetail] = Field(default_factory=list)


class MeasurementFinding(BaseModel):
    """A single compliance measurement finding."""

    file: str
    rule_id: str
    description: str
    by_law: str
    parameter: str
    threshold: float
    measured_value: float
    unit: str
    status: str = "pass"  # pass | fail
    severity: str = "error"


class ComplianceMeasurementResult(BaseModel):
    """Result of measuring dimensions against compliance rules."""

    files_processed: int = 0
    total_checks: int = 0
    pass_count: int = 0
    fail_count: int = 0
    findings: list[MeasurementFinding] = Field(default_factory=list)
    errors: list[FileDetail] = Field(default_factory=list)


class ScheduleRow(BaseModel):
    """A single row in an extracted schedule."""

    file: str
    block_handle: str
    attributes: dict[str, str] = Field(default_factory=dict)


class ScheduleResult(BaseModel):
    """Result of a schedule extraction operation."""

    files_processed: int = 0
    block_name: str = ""
    total_entries: int = 0
    rows: list[ScheduleRow] = Field(default_factory=list)
    errors: list[FileDetail] = Field(default_factory=list)


class FileXrefDetail(BaseModel):
    """XREFs found in a single file."""

    file: str
    xrefs: list[XrefInfo] = Field(default_factory=list)
    error: str | None = None


class XrefListResult(BaseModel):
    """Result of an XREF management operation."""

    files_processed: int = 0
    action: str = "list"
    total_xrefs: int = 0
    details: list[FileXrefDetail] = Field(default_factory=list)
    changes: int = 0
    errors: list[FileDetail] = Field(default_factory=list)


class SearchMatch(BaseModel):
    """A single search match across drawings."""

    file: str
    match_type: str  # text | attribute | layer
    entity_handle: str = ""
    layer: str = ""
    matched_text: str = ""


class DrawingSearchResult(BaseModel):
    """Result of a drawing search operation."""

    files_processed: int = 0
    search_text: str = ""
    total_matches: int = 0
    matches: list[SearchMatch] = Field(default_factory=list)
    errors: list[FileDetail] = Field(default_factory=list)


class FilePlotDetail(BaseModel):
    """Plot result for a single file."""

    file: str
    output_file: str = ""
    layout: str = ""
    error: str | None = None


class PlotResult(BaseModel):
    """Result of a batch plot operation."""

    files_processed: int = 0
    files_plotted: int = 0
    details: list[FilePlotDetail] = Field(default_factory=list)
    errors: list[FileDetail] = Field(default_factory=list)


class PurgeResult(BaseModel):
    """Result of a batch purge operation."""

    files_processed: int = 0
    files_purged: int = 0
    total_items_purged: int = 0
    audit_issues: list[AuditIssue] = Field(default_factory=list)
    errors: list[FileDetail] = Field(default_factory=list)


class FileInfoDetail(BaseModel):
    """Summary info for a single drawing file."""

    file: str
    layer_count: int = 0
    text_count: int = 0
    dimension_count: int = 0
    block_count: int = 0
    polyline_count: int = 0
    xref_count: int = 0
    layout_count: int = 0
    extents: DrawingExtents | None = None
    error: str | None = None


class DrawingInfoResult(BaseModel):
    """Result of a drawing info summary operation."""

    files_processed: int = 0
    details: list[FileInfoDetail] = Field(default_factory=list)
    errors: list[FileDetail] = Field(default_factory=list)


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
