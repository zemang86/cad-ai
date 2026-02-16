"""Shared fixtures for the test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.models import LayerEntity, TextEntity


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
def dwg_folder(tmp_path: Path) -> Path:
    """Create a temporary folder with dummy .dwg files for file-ops tests."""
    (tmp_path / "plan_a.dwg").write_bytes(b"fake")
    (tmp_path / "plan_b.dwg").write_bytes(b"fake")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "detail.dwg").write_bytes(b"fake")
    (tmp_path / "readme.txt").write_bytes(b"ignore me")
    return tmp_path
