"""Tests for file utilities."""

from pathlib import Path

from autocad_batch_commander.utils.file_ops import create_backup, get_dwg_files


def test_get_dwg_files(dwg_folder: Path):
    files = get_dwg_files(dwg_folder)
    assert len(files) == 3
    assert all(f.suffix == ".dwg" for f in files)


def test_get_dwg_files_non_recursive(dwg_folder: Path):
    files = get_dwg_files(dwg_folder, recursive=False)
    assert len(files) == 2  # only top-level


def test_create_backup(dwg_folder: Path):
    target = dwg_folder / "plan_a.dwg"
    backup = create_backup(target)

    assert backup.exists()
    assert backup.parent.name == ".backups"
    assert "plan_a_" in backup.name
