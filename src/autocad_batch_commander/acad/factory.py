"""Factory for selecting the appropriate AutoCAD adapter."""

from __future__ import annotations

import sys
from pathlib import Path

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.acad.port import AutoCADPort
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


# Sample data that resembles a real architectural project
_SAMPLE_DRAWINGS: list[dict] = [
    {
        "suffix": "floor_plan",
        "texts": [
            TextEntity(handle="T1", text="TIMBER DOOR TYPE A", layer="DOOR"),
            TextEntity(handle="T2", text="TIMBER DOOR TYPE B", layer="DOOR"),
            TextEntity(handle="T3", text="TIMBER WINDOW FRAME", layer="WINDOW"),
            TextEntity(handle="T4", text="CONCRETE WALL 150mm", layer="WALL"),
            TextEntity(handle="T5", text="GYPSUM PARTITION WALL", layer="WALL"),
            TextEntity(
                handle="T6", text="FLOOR FINISH: CERAMIC TILE 300x300", layer="TEXT"
            ),
            TextEntity(handle="T7", text="CEILING HEIGHT: 2700mm", layer="TEXT"),
        ],
        "layers": [
            LayerEntity(name="WALL", color=1),
            LayerEntity(name="DOOR", color=2),
            LayerEntity(name="WINDOW", color=3),
            LayerEntity(name="FURNITURE", color=4),
            LayerEntity(name="TEXT", color=7),
            LayerEntity(name="DIMENSION", color=6),
            LayerEntity(name="TITLE", color=7),
            LayerEntity(name="CORRIDOR", color=5),
            LayerEntity(name="ROOM", color=3),
        ],
        "dimensions": [
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
                value=3000.0,
                layer="DIMENSION",
                associated_points=[Point3D(x=0, y=0), Point3D(x=0, y=3000)],
            ),
            DimensionEntity(
                handle="D3",
                dimension_type="linear",
                value=1200.0,
                text_override="CORRIDOR WIDTH",
                layer="DIMENSION",
                associated_points=[Point3D(x=5000, y=0), Point3D(x=6200, y=0)],
            ),
            DimensionEntity(
                handle="D4",
                dimension_type="linear",
                value=900.0,
                text_override="DOOR WIDTH",
                layer="DIMENSION",
                associated_points=[Point3D(x=0, y=0), Point3D(x=900, y=0)],
            ),
        ],
        "polylines": [
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
                vertices=[
                    Point3D(x=4000, y=0),
                    Point3D(x=7600, y=0),
                    Point3D(x=7600, y=4200),
                    Point3D(x=4000, y=4200),
                ],
                closed=True,
                area=15120000.0,
                perimeter=15600.0,
                layer="ROOM",
            ),
        ],
        "blocks": [
            BlockReference(
                handle="BLK1",
                name="DOOR_SINGLE",
                insertion_point=Point3D(x=1800, y=0),
                layer="DOOR",
                rotation=0.0,
            ),
            BlockReference(
                handle="BLK2",
                name="WINDOW_1200",
                insertion_point=Point3D(x=1200, y=3000),
                layer="WINDOW",
                rotation=0.0,
            ),
            BlockReference(
                handle="BLK3",
                name="TITLE_BLOCK",
                insertion_point=Point3D(x=0, y=0),
                layer="TITLE",
                rotation=0.0,
            ),
        ],
        "block_attributes": {
            "BLK1": [
                BlockAttribute(tag="TYPE", value="SINGLE LEAF", handle="BA1"),
                BlockAttribute(tag="SIZE", value="900x2100", handle="BA2"),
                BlockAttribute(tag="MATERIAL", value="TIMBER", handle="BA3"),
            ],
            "BLK2": [
                BlockAttribute(tag="TYPE", value="CASEMENT", handle="BA4"),
                BlockAttribute(tag="SIZE", value="1200x1200", handle="BA5"),
            ],
            "BLK3": [
                BlockAttribute(tag="PROJECT_NO", value="2024-001", handle="BA6"),
                BlockAttribute(
                    tag="PROJECT_NAME", value="RESIDENTIAL TOWER", handle="BA7"
                ),
                BlockAttribute(tag="DRAWN_BY", value="AH", handle="BA8"),
                BlockAttribute(tag="DATE", value="2024-01-15", handle="BA9"),
                BlockAttribute(tag="SCALE", value="1:100", handle="BA10"),
            ],
        },
        "xrefs": [
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
        "layouts": [
            LayoutInfo(name="Model", paper_size="", plot_device="", viewport_count=0),
            LayoutInfo(
                name="A1-PLAN",
                paper_size="ISO_A1_(841.00_x_594.00_MM)",
                plot_device="DWG To PDF.pc3",
                viewport_count=1,
            ),
        ],
        "viewports": [
            ViewportInfo(
                handle="VP1",
                center=Point2D(x=420, y=297),
                width=800,
                height=550,
                scale=100.0,
            ),
        ],
        "extents": DrawingExtents(
            min_point=Point3D(x=-500, y=-500, z=0),
            max_point=Point3D(x=50000, y=35000, z=0),
        ),
    },
    {
        "suffix": "elevation",
        "texts": [
            TextEntity(handle="E1", text="TIMBER DOOR ELEVATION", layer="DOOR"),
            TextEntity(handle="E2", text="ALUMINIUM WINDOW FRAME", layer="WINDOW"),
            TextEntity(handle="E3", text="ROOF TILE: MONIER ELABANA", layer="TEXT"),
        ],
        "layers": [
            LayerEntity(name="WALL", color=1),
            LayerEntity(name="DOOR", color=2),
            LayerEntity(name="WINDOW", color=3),
            LayerEntity(name="ROOF", color=5),
            LayerEntity(name="TEXT", color=7),
            LayerEntity(name="GRID", color=8),
            LayerEntity(name="DIMENSION", color=6),
        ],
        "dimensions": [
            DimensionEntity(
                handle="ED1",
                dimension_type="linear",
                value=2700.0,
                text_override="FFL TO CEILING",
                layer="DIMENSION",
            ),
            DimensionEntity(
                handle="ED2",
                dimension_type="linear",
                value=3300.0,
                text_override="FLOOR TO FLOOR",
                layer="DIMENSION",
            ),
        ],
        "polylines": [],
        "blocks": [
            BlockReference(
                handle="EBLK1",
                name="TITLE_BLOCK",
                insertion_point=Point3D(x=0, y=0),
                layer="TITLE",
            ),
        ],
        "block_attributes": {
            "EBLK1": [
                BlockAttribute(tag="PROJECT_NO", value="2024-001", handle="EBA1"),
                BlockAttribute(tag="DRAWN_BY", value="AH", handle="EBA2"),
            ],
        },
        "xrefs": [],
        "layouts": [
            LayoutInfo(name="Model", paper_size="", plot_device=""),
            LayoutInfo(
                name="A1-ELEVATION",
                paper_size="ISO_A1_(841.00_x_594.00_MM)",
                plot_device="DWG To PDF.pc3",
            ),
        ],
        "viewports": [],
        "extents": DrawingExtents(
            min_point=Point3D(x=0, y=0, z=0),
            max_point=Point3D(x=42000, y=30000, z=0),
        ),
    },
    {
        "suffix": "site_plan",
        "texts": [
            TextEntity(handle="S1", text="TIMBER FENCE 1200mm HIGH", layer="TEXT"),
            TextEntity(handle="S2", text="PARKING LOT - 20 BAYS", layer="TEXT"),
            TextEntity(handle="S3", text="GUARD HOUSE", layer="TEXT"),
        ],
        "layers": [
            LayerEntity(name="WALL", color=1),
            LayerEntity(name="TEXT", color=7),
            LayerEntity(name="DIMENSION", color=6),
            LayerEntity(name="GRID", color=8),
            LayerEntity(name="SITE", color=4),
        ],
        "dimensions": [
            DimensionEntity(
                handle="SD1",
                dimension_type="linear",
                value=5500.0,
                layer="DIMENSION",
            ),
        ],
        "polylines": [
            PolylineEntity(
                handle="SPL1",
                vertices=[
                    Point3D(x=0, y=0),
                    Point3D(x=50000, y=0),
                    Point3D(x=50000, y=35000),
                    Point3D(x=0, y=35000),
                ],
                closed=True,
                area=1750000000.0,
                perimeter=170000.0,
                layer="SITE",
            ),
        ],
        "blocks": [],
        "block_attributes": {},
        "xrefs": [
            XrefInfo(
                name="TOPO_SURVEY",
                path="./xref/topo.dwg",
                xref_type="attach",
                status="loaded",
            ),
        ],
        "layouts": [
            LayoutInfo(name="Model", paper_size="", plot_device=""),
        ],
        "viewports": [],
        "extents": DrawingExtents(
            min_point=Point3D(x=-1000, y=-1000, z=0),
            max_point=Point3D(x=55000, y=40000, z=0),
        ),
    },
]


def _populate_mock(adapter: MockAutoCADAdapter, folder: Path) -> None:
    """Register sample drawing data for each .dwg file found in *folder*."""
    from autocad_batch_commander.utils.file_ops import get_dwg_files

    dwg_files = get_dwg_files(folder)
    for i, dwg in enumerate(dwg_files):
        sample = _SAMPLE_DRAWINGS[i % len(_SAMPLE_DRAWINGS)]
        adapter.add_mock_drawing(
            str(dwg),
            texts=sample["texts"],
            layers=sample["layers"],
            dimensions=sample.get("dimensions"),
            polylines=sample.get("polylines"),
            blocks=sample.get("blocks"),
            block_attributes=sample.get("block_attributes"),
            xrefs=sample.get("xrefs"),
            layouts=sample.get("layouts"),
            viewports=sample.get("viewports"),
            extents=sample.get("extents"),
        )


def _detect_cad_engine() -> str:
    """Auto-detect which CAD application is running (Windows only)."""
    import win32com.client  # type: ignore[import-untyped]

    for engine, prog_id in [
        ("autocad", "AutoCAD.Application"),
        ("bricscad", "BricscadApp.AcadApplication"),
        ("zwcad", "ZWCAD.Application"),
    ]:
        try:
            win32com.client.GetActiveObject(prog_id)
            return engine
        except Exception:
            continue
    return "autocad"  # fallback


def get_acad_adapter(
    *,
    use_mock: bool = False,
    folder: Path | None = None,
    cad_engine: str = "auto",
) -> AutoCADPort:
    """Return an adapter instance based on platform and user preference.

    On non-Windows platforms, the mock adapter is always returned.
    On Windows, the real adapter is returned unless *use_mock* is True.

    When *folder* is provided and the mock adapter is used, it is
    pre-populated with sample architectural drawing data for every
    .dwg file in that folder.

    *cad_engine* selects which CAD application to connect to:
    "auto" (detect running app), "autocad", "bricscad", "zwcad", or "mock".
    """
    if cad_engine == "mock":
        use_mock = True

    if use_mock or sys.platform != "win32":
        adapter = MockAutoCADAdapter()
        if folder is not None:
            _populate_mock(adapter, folder)
        return adapter  # type: ignore[return-value]

    # Windows — select real adapter
    engine = cad_engine if cad_engine != "auto" else _detect_cad_engine()

    if engine == "bricscad":
        from autocad_batch_commander.acad.bricscad_adapter import BricsCADAdapter

        return BricsCADAdapter()  # type: ignore[return-value]
    elif engine == "zwcad":
        from autocad_batch_commander.acad.zwcad_adapter import ZWCADAdapter

        return ZWCADAdapter()  # type: ignore[return-value]
    else:
        from autocad_batch_commander.acad.real_adapter import RealAutoCADAdapter

        return RealAutoCADAdapter()  # type: ignore[return-value]
