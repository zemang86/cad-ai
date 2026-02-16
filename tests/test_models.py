"""Tests for Pydantic models."""

from pathlib import Path

from autocad_batch_commander.models import (
    AuditFinding,
    AuditResult,
    FileDetail,
    LayerRenameRequest,
    LayerStandardizeRequest,
    OperationResult,
    TextEntity,
    TextReplaceRequest,
)


def test_text_replace_request_defaults():
    req = TextReplaceRequest(folder=Path("/tmp"), find_text="A", replace_text="B")
    assert req.layers is None
    assert req.case_sensitive is False
    assert req.backup is True


def test_layer_rename_request():
    req = LayerRenameRequest(folder=Path("/tmp"), old_name="WALL", new_name="A-WALL")
    assert req.old_name == "WALL"
    assert req.new_name == "A-WALL"


def test_layer_standardize_request_defaults():
    req = LayerStandardizeRequest(folder=Path("/tmp"))
    assert req.standard == "AIA"
    assert req.report_only is False


def test_operation_result_defaults():
    r = OperationResult()
    assert r.files_processed == 0
    assert r.errors == []


def test_audit_finding():
    f = AuditFinding(
        file="plan.dwg",
        finding_type="non_standard_layer",
        message="Bad layer",
        layer="WALL",
    )
    assert f.severity == "warning"


def test_text_entity():
    t = TextEntity(handle="H1", text="hello", layer="0")
    assert t.entity_type == "AcDbText"
