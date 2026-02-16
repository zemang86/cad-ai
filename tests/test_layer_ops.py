"""Tests for batch layer operations."""

from pathlib import Path

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.models import (
    LayerEntity,
    LayerRenameRequest,
    LayerStandardizeRequest,
    TextEntity,
)
from autocad_batch_commander.operations.layer_ops import (
    batch_rename_layer,
    batch_standardize_layers,
)


def _adapter_with_dwg_files(tmp_path: Path) -> MockAutoCADAdapter:
    adapter = MockAutoCADAdapter()

    dwg1 = tmp_path / "floor.dwg"
    dwg1.write_bytes(b"fake")
    dwg2 = tmp_path / "site.dwg"
    dwg2.write_bytes(b"fake")

    adapter.add_mock_drawing(
        str(dwg1),
        texts=[TextEntity(handle="T1", text="wall note", layer="WALL")],
        layers=[
            LayerEntity(name="WALL"),
            LayerEntity(name="DOOR"),
            LayerEntity(name="A-ANNO-TEXT"),
        ],
    )
    adapter.add_mock_drawing(
        str(dwg2),
        texts=[],
        layers=[
            LayerEntity(name="FURNITURE"),
            LayerEntity(name="DOOR"),
        ],
    )
    return adapter


def test_rename_layer(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = LayerRenameRequest(
        folder=tmp_path, old_name="WALL", new_name="A-WALL", backup=False
    )
    result = batch_rename_layer(adapter, request)

    assert result.files_processed == 2
    assert result.files_modified == 1  # only floor.dwg has WALL
    assert result.total_changes == 1


def test_rename_layer_not_found(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = LayerRenameRequest(
        folder=tmp_path, old_name="NOPE", new_name="A-NOPE", backup=False
    )
    result = batch_rename_layer(adapter, request)

    assert result.files_modified == 0


def test_standardize_layers(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = LayerStandardizeRequest(
        folder=tmp_path,
        standard="AIA",
        backup=False,
    )
    result = batch_standardize_layers(adapter, request)

    # floor.dwg: WALL->A-WALL, DOOR->A-DOOR = 2 changes
    # site.dwg: FURNITURE->A-FURN, DOOR->A-DOOR = 2 changes
    assert result.total_changes == 4
    assert result.files_modified == 2


def test_standardize_report_only(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = LayerStandardizeRequest(
        folder=tmp_path,
        standard="AIA",
        report_only=True,
        backup=False,
    )
    result = batch_standardize_layers(adapter, request)

    assert result.total_changes == 4
    assert result.files_modified == 0  # report-only: nothing saved
