"""Tests for block operations: title block updates, schedule extraction."""

from __future__ import annotations

from pathlib import Path

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.models import (
    BlockAttribute,
    BlockReference,
    LayerEntity,
    Point3D,
    ScheduleExtractionRequest,
    TitleBlockUpdateRequest,
)
from autocad_batch_commander.operations.block_ops import (
    batch_update_title_blocks,
    extract_schedule,
)


def _adapter_with_blocks(tmp_path: Path) -> MockAutoCADAdapter:
    (tmp_path / "plan.dwg").write_bytes(b"fake")

    adapter = MockAutoCADAdapter()
    adapter.add_mock_drawing(
        str(tmp_path / "plan.dwg"),
        layers=[LayerEntity(name="TITLE"), LayerEntity(name="DOOR")],
        blocks=[
            BlockReference(
                handle="BLK1",
                name="TITLE_BLOCK",
                insertion_point=Point3D(x=0, y=0),
                layer="TITLE",
            ),
            BlockReference(
                handle="BLK2",
                name="DOOR_SINGLE",
                insertion_point=Point3D(x=1000, y=500),
                layer="DOOR",
            ),
            BlockReference(
                handle="BLK3",
                name="DOOR_SINGLE",
                insertion_point=Point3D(x=3000, y=500),
                layer="DOOR",
            ),
        ],
        block_attributes={
            "BLK1": [
                BlockAttribute(tag="PROJECT_NO", value="2024-001", handle="BA1"),
                BlockAttribute(tag="DRAWN_BY", value="AH", handle="BA2"),
                BlockAttribute(tag="DATE", value="2024-01-15", handle="BA3"),
            ],
            "BLK2": [
                BlockAttribute(tag="TYPE", value="SINGLE LEAF", handle="BA4"),
                BlockAttribute(tag="SIZE", value="900x2100", handle="BA5"),
            ],
            "BLK3": [
                BlockAttribute(tag="TYPE", value="DOUBLE LEAF", handle="BA6"),
                BlockAttribute(tag="SIZE", value="1800x2100", handle="BA7"),
            ],
        },
    )
    return adapter


def test_update_title_blocks(tmp_path: Path) -> None:
    adapter = _adapter_with_blocks(tmp_path)
    request = TitleBlockUpdateRequest(
        folder=tmp_path,
        block_name="TITLE_BLOCK",
        updates={"DATE": "2024-06-01", "DRAWN_BY": "ZA"},
        backup=False,
    )
    result = batch_update_title_blocks(adapter, request)

    assert result.files_processed == 1
    assert result.files_modified == 1
    assert result.total_changes == 2

    # Verify the attributes were updated
    adapter.open_drawing(str(tmp_path / "plan.dwg"))
    attrs = adapter.get_block_attributes("BLK1")
    date_attr = next(a for a in attrs if a.tag == "DATE")
    assert date_attr.value == "2024-06-01"


def test_update_title_blocks_no_match(tmp_path: Path) -> None:
    adapter = _adapter_with_blocks(tmp_path)
    request = TitleBlockUpdateRequest(
        folder=tmp_path,
        block_name="NONEXISTENT",
        updates={"DATE": "2024-06-01"},
        backup=False,
    )
    result = batch_update_title_blocks(adapter, request)

    assert result.files_processed == 1
    assert result.total_changes == 0


def test_extract_schedule(tmp_path: Path) -> None:
    adapter = _adapter_with_blocks(tmp_path)
    request = ScheduleExtractionRequest(
        folder=tmp_path,
        block_name="DOOR_SINGLE",
    )
    result = extract_schedule(adapter, request)

    assert result.files_processed == 1
    assert result.total_entries == 2
    assert result.block_name == "DOOR_SINGLE"
    assert result.rows[0].attributes["TYPE"] == "SINGLE LEAF"
    assert result.rows[1].attributes["TYPE"] == "DOUBLE LEAF"


def test_extract_schedule_with_tags(tmp_path: Path) -> None:
    adapter = _adapter_with_blocks(tmp_path)
    request = ScheduleExtractionRequest(
        folder=tmp_path,
        block_name="DOOR_SINGLE",
        tags=["SIZE"],
    )
    result = extract_schedule(adapter, request)

    assert result.total_entries == 2
    # Only SIZE tag should be in the attributes
    assert "SIZE" in result.rows[0].attributes
    assert "TYPE" not in result.rows[0].attributes
