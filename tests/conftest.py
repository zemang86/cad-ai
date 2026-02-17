"""Shared fixtures for the test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.models import (
    BlockAttribute,
    BlockReference,
    DimensionEntity,
    DrawingExtents,
    LayerEntity,
    LayoutInfo,
    Point2D,
    Point3D,
    PolylineEntity,
    TextEntity,
    ViewportInfo,
    XrefInfo,
)


@pytest.fixture
def mock_adapter() -> MockAutoCADAdapter:
    """Return a MockAutoCADAdapter with two pre-loaded drawings."""
    adapter = MockAutoCADAdapter()

    adapter.add_mock_drawing(
        "floor_plan.dwg",
        texts=[
            TextEntity(handle="T1", text="TIMBER DOOR", layer="A-DOOR"),
            TextEntity(handle="T2", text="TIMBER WINDOW FRAME", layer="A-WIND"),
            TextEntity(handle="T3", text="Timber door schedule", layer="A-ANNO-TEXT"),
            TextEntity(handle="T4", text="CONCRETE WALL", layer="A-WALL"),
        ],
        layers=[
            LayerEntity(name="A-DOOR"),
            LayerEntity(name="A-WIND"),
            LayerEntity(name="A-ANNO-TEXT"),
            LayerEntity(name="A-WALL"),
            LayerEntity(name="WALL"),
        ],
    )

    adapter.add_mock_drawing(
        "site_plan.dwg",
        texts=[
            TextEntity(handle="S1", text="TIMBER FENCE", layer="L-SITE"),
            TextEntity(handle="S2", text="PARKING AREA", layer="L-SITE"),
        ],
        layers=[
            LayerEntity(name="L-SITE"),
            LayerEntity(name="DOOR"),
            LayerEntity(name="FURNITURE"),
        ],
    )

    return adapter


@pytest.fixture
def full_mock_adapter() -> MockAutoCADAdapter:
    """Return a MockAutoCADAdapter with all entity types populated."""
    adapter = MockAutoCADAdapter()

    adapter.add_mock_drawing(
        "full_plan.dwg",
        texts=[
            TextEntity(handle="T1", text="BEDROOM 1", layer="TEXT"),
            TextEntity(handle="T2", text="CORRIDOR", layer="TEXT"),
        ],
        layers=[
            LayerEntity(name="WALL", color=1),
            LayerEntity(name="DOOR", color=2),
            LayerEntity(name="WINDOW", color=3),
            LayerEntity(name="TEXT", color=7),
            LayerEntity(name="DIMENSION", color=6),
            LayerEntity(name="ROOM", color=3),
            LayerEntity(name="CORRIDOR", color=5),
            LayerEntity(name="TITLE", color=7),
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
                text_override="DOOR WIDTH",
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
                layer="WALL",
            ),
        ],
        blocks=[
            BlockReference(
                handle="BLK1",
                name="DOOR_SINGLE",
                insertion_point=Point3D(x=1800, y=0),
                layer="DOOR",
            ),
            BlockReference(
                handle="BLK2",
                name="TITLE_BLOCK",
                insertion_point=Point3D(x=0, y=0),
                layer="TITLE",
            ),
        ],
        block_attributes={
            "BLK1": [
                BlockAttribute(tag="TYPE", value="SINGLE LEAF", handle="BA1"),
                BlockAttribute(tag="SIZE", value="900x2100", handle="BA2"),
            ],
            "BLK2": [
                BlockAttribute(tag="PROJECT_NO", value="2024-001", handle="BA3"),
                BlockAttribute(tag="DRAWN_BY", value="AH", handle="BA4"),
                BlockAttribute(tag="DATE", value="2024-01-15", handle="BA5"),
            ],
        },
        xrefs=[
            XrefInfo(
                name="STRUCTURAL",
                path="./xref/structural.dwg",
                xref_type="attach",
                status="loaded",
            ),
            XrefInfo(
                name="MEP", path="./xref/mep.dwg", xref_type="attach", status="loaded"
            ),
        ],
        layouts=[
            LayoutInfo(name="Model", paper_size=""),
            LayoutInfo(
                name="A1-PLAN", paper_size="ISO_A1", plot_device="DWG To PDF.pc3"
            ),
        ],
        viewports=[
            ViewportInfo(
                handle="VP1",
                center=Point2D(x=420, y=297),
                width=800,
                height=550,
                scale=100.0,
            ),
        ],
        extents=DrawingExtents(
            min_point=Point3D(x=-500, y=-500),
            max_point=Point3D(x=50000, y=35000),
        ),
    )

    return adapter


@pytest.fixture
def dwg_folder(tmp_path: Path) -> Path:
    """Create a temporary folder with dummy .dwg files for file-ops tests."""
    (tmp_path / "plan_a.dwg").write_bytes(b"fake")
    (tmp_path / "plan_b.dwg").write_bytes(b"fake")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "detail.dwg").write_bytes(b"fake")
    (tmp_path / "readme.txt").write_bytes(b"ignore me")
    return tmp_path
