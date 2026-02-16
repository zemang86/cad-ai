"""Tests for batch text find-and-replace operations."""

from pathlib import Path

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.models import TextEntity, TextReplaceRequest
from autocad_batch_commander.operations.text_ops import batch_find_replace


def _adapter_with_dwg_files(tmp_path: Path) -> MockAutoCADAdapter:
    """Create a mock adapter and matching .dwg files on disk."""
    adapter = MockAutoCADAdapter()

    # Create real files so get_dwg_files() finds them
    dwg1 = tmp_path / "plan.dwg"
    dwg1.write_bytes(b"fake")
    dwg2 = tmp_path / "detail.dwg"
    dwg2.write_bytes(b"fake")

    adapter.add_mock_drawing(
        str(dwg1),
        texts=[
            TextEntity(handle="T1", text="TIMBER DOOR", layer="A-DOOR"),
            TextEntity(handle="T2", text="TIMBER FRAME", layer="A-WIND"),
            TextEntity(handle="T3", text="CONCRETE WALL", layer="A-WALL"),
        ],
    )
    adapter.add_mock_drawing(
        str(dwg2),
        texts=[
            TextEntity(handle="D1", text="timber shelf", layer="A-FURN"),
        ],
    )
    return adapter


def test_case_insensitive_replace(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = TextReplaceRequest(
        folder=tmp_path,
        find_text="timber",
        replace_text="ALUMINIUM",
        case_sensitive=False,
        backup=False,
    )
    result = batch_find_replace(adapter, request)

    assert result.files_processed == 2
    assert result.files_modified == 2
    assert result.total_changes == 3  # T1, T2, D1
    assert len(result.errors) == 0


def test_case_sensitive_replace(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = TextReplaceRequest(
        folder=tmp_path,
        find_text="TIMBER",
        replace_text="ALUMINIUM",
        case_sensitive=True,
        backup=False,
    )
    result = batch_find_replace(adapter, request)

    # Only uppercase TIMBER matches (T1 and T2), not "timber shelf" (D1)
    assert result.total_changes == 2


def test_layer_filter(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = TextReplaceRequest(
        folder=tmp_path,
        find_text="timber",
        replace_text="ALUMINIUM",
        layers=["A-DOOR"],
        case_sensitive=False,
        backup=False,
    )
    result = batch_find_replace(adapter, request)

    # Only T1 on layer A-DOOR should match
    assert result.total_changes == 1


def test_no_matches(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = TextReplaceRequest(
        folder=tmp_path,
        find_text="NONEXISTENT",
        replace_text="X",
        backup=False,
    )
    result = batch_find_replace(adapter, request)

    assert result.files_processed == 2
    assert result.files_modified == 0
    assert result.total_changes == 0


def test_backup_created(tmp_path: Path):
    adapter = _adapter_with_dwg_files(tmp_path)
    request = TextReplaceRequest(
        folder=tmp_path,
        find_text="TIMBER",
        replace_text="X",
        case_sensitive=True,
        backup=True,
    )
    batch_find_replace(adapter, request)

    backups = list((tmp_path / ".backups").glob("*.dwg"))
    assert len(backups) == 2  # both files backed up
