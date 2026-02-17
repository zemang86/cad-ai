"""Tests for drawing utility operations: purge, plot, search, info."""

from __future__ import annotations

from pathlib import Path

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.models import (
    BatchPlotRequest,
    BatchPurgeRequest,
    BlockAttribute,
    BlockReference,
    DimensionEntity,
    DrawingExtents,
    DrawingInfoRequest,
    DrawingSearchRequest,
    LayerEntity,
    LayoutInfo,
    Point3D,
    PolylineEntity,
    TextEntity,
    XrefInfo,
)
from autocad_batch_commander.operations.drawing_ops import (
    batch_plot,
    batch_purge,
    drawing_search,
    get_drawing_info,
)


def _adapter_with_full_drawing(tmp_path: Path) -> MockAutoCADAdapter:
    (tmp_path / "plan.dwg").write_bytes(b"fake")

    adapter = MockAutoCADAdapter()
    adapter.add_mock_drawing(
        str(tmp_path / "plan.dwg"),
        texts=[
            TextEntity(handle="T1", text="BEDROOM 1", layer="TEXT"),
            TextEntity(handle="T2", text="TIMBER DOOR", layer="DOOR"),
        ],
        layers=[
            LayerEntity(name="TEXT", color=7),
            LayerEntity(name="DOOR", color=2),
            LayerEntity(name="DIMENSION", color=6),
        ],
        dimensions=[
            DimensionEntity(handle="D1", value=3600.0, layer="DIMENSION"),
        ],
        polylines=[
            PolylineEntity(
                handle="PL1",
                closed=True,
                area=10800000.0,
                perimeter=13200.0,
                layer="ROOM",
                vertices=[
                    Point3D(x=0, y=0),
                    Point3D(x=3600, y=0),
                    Point3D(x=3600, y=3000),
                    Point3D(x=0, y=3000),
                ],
            ),
        ],
        blocks=[
            BlockReference(
                handle="BLK1",
                name="DOOR_SINGLE",
                insertion_point=Point3D(x=1800, y=0),
                layer="DOOR",
            ),
        ],
        block_attributes={
            "BLK1": [
                BlockAttribute(tag="TYPE", value="SINGLE LEAF", handle="BA1"),
            ],
        },
        xrefs=[
            XrefInfo(name="STRUCTURAL", path="./xref/structural.dwg"),
        ],
        layouts=[
            LayoutInfo(name="Model"),
            LayoutInfo(
                name="A1-PLAN", paper_size="ISO_A1", plot_device="DWG To PDF.pc3"
            ),
        ],
        extents=DrawingExtents(
            min_point=Point3D(x=-500, y=-500),
            max_point=Point3D(x=50000, y=35000),
        ),
    )
    return adapter


def test_batch_purge(tmp_path: Path) -> None:
    adapter = _adapter_with_full_drawing(tmp_path)
    request = BatchPurgeRequest(folder=tmp_path, backup=False)
    result = batch_purge(adapter, request)

    assert result.files_processed == 1
    assert result.files_purged == 1
    assert result.total_items_purged > 0


def test_batch_plot(tmp_path: Path) -> None:
    adapter = _adapter_with_full_drawing(tmp_path)
    out_dir = tmp_path / "plots"
    request = BatchPlotRequest(folder=tmp_path, output_dir=out_dir, output_format="PDF")
    result = batch_plot(adapter, request)

    assert result.files_processed == 1
    assert result.files_plotted == 1  # A1-PLAN, Model is skipped
    assert len(result.details) == 1
    assert "A1-PLAN" in result.details[0].layout


def test_drawing_search_text(tmp_path: Path) -> None:
    adapter = _adapter_with_full_drawing(tmp_path)
    request = DrawingSearchRequest(
        folder=tmp_path, search_text="TIMBER", search_in=["text"]
    )
    result = drawing_search(adapter, request)

    assert result.files_processed == 1
    assert result.total_matches == 1
    assert result.matches[0].matched_text == "TIMBER DOOR"


def test_drawing_search_attributes(tmp_path: Path) -> None:
    adapter = _adapter_with_full_drawing(tmp_path)
    request = DrawingSearchRequest(
        folder=tmp_path, search_text="SINGLE", search_in=["attributes"]
    )
    result = drawing_search(adapter, request)

    assert result.total_matches == 1
    assert result.matches[0].match_type == "attribute"


def test_drawing_search_layers(tmp_path: Path) -> None:
    adapter = _adapter_with_full_drawing(tmp_path)
    request = DrawingSearchRequest(
        folder=tmp_path, search_text="DOOR", search_in=["layers"]
    )
    result = drawing_search(adapter, request)

    assert result.total_matches == 1
    assert result.matches[0].match_type == "layer"


def test_drawing_search_case_insensitive(tmp_path: Path) -> None:
    adapter = _adapter_with_full_drawing(tmp_path)
    request = DrawingSearchRequest(
        folder=tmp_path, search_text="bedroom", search_in=["text"]
    )
    result = drawing_search(adapter, request)

    assert result.total_matches == 1


def test_get_drawing_info(tmp_path: Path) -> None:
    adapter = _adapter_with_full_drawing(tmp_path)
    request = DrawingInfoRequest(folder=tmp_path)
    result = get_drawing_info(adapter, request)

    assert result.files_processed == 1
    info = result.details[0]
    assert info.layer_count == 3
    assert info.text_count == 2
    assert info.dimension_count == 1
    assert info.block_count == 1
    assert info.polyline_count == 1
    assert info.xref_count == 1
    assert info.layout_count == 2
    assert info.extents is not None
    assert info.extents.max_point.x == 50000
