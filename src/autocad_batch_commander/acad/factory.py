"""Factory for selecting the appropriate AutoCAD adapter."""

from __future__ import annotations

import sys
from pathlib import Path

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.acad.port import AutoCADPort
from autocad_batch_commander.models import LayerEntity, TextEntity


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
            TextEntity(handle="T6", text="FLOOR FINISH: CERAMIC TILE 300x300", layer="TEXT"),
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
        ],
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
        ],
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
        ],
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
        )


def get_acad_adapter(
    *, use_mock: bool = False, folder: Path | None = None
) -> AutoCADPort:
    """Return an adapter instance based on platform and user preference.

    On non-Windows platforms, the mock adapter is always returned.
    On Windows, the real adapter is returned unless *use_mock* is True.

    When *folder* is provided and the mock adapter is used, it is
    pre-populated with sample architectural drawing data for every
    .dwg file in that folder.
    """
    if use_mock or sys.platform != "win32":
        adapter = MockAutoCADAdapter()
        if folder is not None:
            _populate_mock(adapter, folder)
        return adapter  # type: ignore[return-value]

    from autocad_batch_commander.acad.real_adapter import RealAutoCADAdapter

    return RealAutoCADAdapter()  # type: ignore[return-value]
