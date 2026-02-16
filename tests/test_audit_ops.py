"""Tests for audit operations."""

from pathlib import Path

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.models import AuditRequest, LayerEntity
from autocad_batch_commander.operations.audit_ops import audit_drawings


def _adapter_with_dwg_files(tmp_path: Path) -> MockAutoCADAdapter:
    adapter = MockAutoCADAdapter()

    dwg1 = tmp_path / "compliant.dwg"
    dwg1.write_bytes(b"fake")
    dwg2 = tmp_path / "noncompliant.dwg"
    dwg2.write_bytes(b"fake")

    # This drawing has all AIA required layers
    adapter.add_mock_drawing(
        str(dwg1),
        layers=[
            LayerEntity(name="A-WALL"),
            LayerEntity(name="A-DOOR"),
            LayerEntity(name="A-WIND"),
            LayerEntity(name="A-ANNO-TEXT"),
        ],
    )
    # This drawing is missing required layers and has non-standard ones
    adapter.add_mock_drawing(
        str(dwg2),
        layers=[
            LayerEntity(name="WALL"),  # non-standard
            LayerEntity(name="DOOR"),  # non-standard
        ],
    )
    return adapter


def test_audit_finds_non_standard_layers(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = AuditRequest(folder=tmp_path, standard="AIA")
    result = audit_drawings(adapter, request)

    assert result.files_processed == 2
    assert result.compliant_files == 1
    assert result.non_compliant_files == 1
    assert result.total_findings > 0

    # The non-compliant file should have findings for WALL and DOOR
    noncompliant_findings = [f for f in result.findings if "noncompliant" in f.file]
    non_std = [f for f in noncompliant_findings if f.finding_type == "non_standard_layer"]
    assert len(non_std) == 2


def test_audit_finds_missing_required_layers(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = AuditRequest(folder=tmp_path, standard="AIA")
    result = audit_drawings(adapter, request)

    missing = [f for f in result.findings if f.finding_type == "missing_required_layer"]
    # noncompliant.dwg is missing A-WALL, A-DOOR, A-WIND, A-ANNO-TEXT
    assert len(missing) >= 4


def test_audit_compliant_file_has_no_findings(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = AuditRequest(folder=tmp_path, standard="AIA")
    result = audit_drawings(adapter, request)

    compliant_findings = [f for f in result.findings if "compliant.dwg" in f.file and "noncompliant" not in f.file]
    assert len(compliant_findings) == 0
