"""Tests for geometry operations: dimensions, areas, compliance measurement."""

from __future__ import annotations

from pathlib import Path

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.models import (
    AreaExtractionRequest,
    ComplianceMeasurementRequest,
    DimensionEntity,
    DimensionExtractionRequest,
    LayerEntity,
    Point3D,
    PolylineEntity,
)
from autocad_batch_commander.operations.geometry_ops import (
    extract_areas,
    extract_dimensions,
    measure_compliance,
)


def _adapter_with_dwg_files(tmp_path: Path) -> MockAutoCADAdapter:
    """Create adapter with real DWG files on disk + mock data registered."""
    (tmp_path / "test.dwg").write_bytes(b"fake")

    adapter = MockAutoCADAdapter()
    adapter.add_mock_drawing(
        str(tmp_path / "test.dwg"),
        layers=[
            LayerEntity(name="DIMENSION", color=6),
            LayerEntity(name="ROOM", color=3),
            LayerEntity(name="CORRIDOR", color=5),
        ],
        dimensions=[
            DimensionEntity(
                handle="D1",
                dimension_type="linear",
                value=3600.0,
                layer="DIMENSION",
                associated_points=[Point3D(x=0, y=0), Point3D(x=3600, y=0)],
            ),
            DimensionEntity(
                handle="D2",
                dimension_type="linear",
                value=1200.0,
                text_override="CORRIDOR WIDTH",
                layer="DIMENSION",
            ),
            DimensionEntity(
                handle="D3",
                dimension_type="aligned",
                value=900.0,
                layer="DIMENSION",
            ),
        ],
        polylines=[
            PolylineEntity(
                handle="PL1",
                vertices=[
                    Point3D(x=0, y=0),
                    Point3D(x=3600, y=0),
                    Point3D(x=3600, y=3000),
                    Point3D(x=0, y=3000),
                ],
                closed=True,
                area=10800000.0,
                perimeter=13200.0,
                layer="ROOM",
            ),
            PolylineEntity(
                handle="PL2",
                vertices=[Point3D(x=0, y=0), Point3D(x=5000, y=0)],
                closed=False,
                area=0.0,
                perimeter=5000.0,
                layer="CORRIDOR",
            ),
        ],
    )
    return adapter


def test_extract_dimensions(tmp_path: Path) -> None:
    adapter = _adapter_with_dwg_files(tmp_path)
    request = DimensionExtractionRequest(folder=tmp_path)
    result = extract_dimensions(adapter, request)

    assert result.files_processed == 1
    assert result.total_dimensions == 3
    assert len(result.details) == 1
    assert result.details[0].dimensions[0].value == 3600.0


def test_extract_dimensions_filter_type(tmp_path: Path) -> None:
    adapter = _adapter_with_dwg_files(tmp_path)
    request = DimensionExtractionRequest(folder=tmp_path, dimension_types=["aligned"])
    result = extract_dimensions(adapter, request)

    assert result.total_dimensions == 1
    assert result.details[0].dimensions[0].dimension_type == "aligned"


def test_extract_dimensions_filter_layer(tmp_path: Path) -> None:
    adapter = _adapter_with_dwg_files(tmp_path)
    request = DimensionExtractionRequest(folder=tmp_path, layers=["NONEXISTENT"])
    result = extract_dimensions(adapter, request)

    assert result.total_dimensions == 0


def test_extract_areas(tmp_path: Path) -> None:
    adapter = _adapter_with_dwg_files(tmp_path)
    request = AreaExtractionRequest(folder=tmp_path)
    result = extract_areas(adapter, request)

    assert result.files_processed == 1
    assert result.total_areas == 1  # only closed polylines
    assert result.details[0].areas[0].area == 10800000.0


def test_extract_areas_min_filter(tmp_path: Path) -> None:
    adapter = _adapter_with_dwg_files(tmp_path)
    request = AreaExtractionRequest(folder=tmp_path, min_area=20000000.0)
    result = extract_areas(adapter, request)

    assert result.total_areas == 0  # 10.8M < 20M


def test_extract_areas_max_filter(tmp_path: Path) -> None:
    adapter = _adapter_with_dwg_files(tmp_path)
    request = AreaExtractionRequest(folder=tmp_path, max_area=20000000.0)
    result = extract_areas(adapter, request)

    assert result.total_areas == 1


def test_measure_compliance(tmp_path: Path) -> None:
    adapter = _adapter_with_dwg_files(tmp_path)
    request = ComplianceMeasurementRequest(folder=tmp_path, rule_sets=["ubbl-spatial"])
    result = measure_compliance(adapter, request)

    assert result.files_processed == 1
    # Whether we get findings depends on dimension_mapping matching
    # At minimum the operation should complete without error
    assert len(result.errors) == 0
