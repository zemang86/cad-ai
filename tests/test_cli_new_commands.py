"""Tests for new CLI commands using the Typer test runner."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from autocad_batch_commander.cli.app import app

runner = CliRunner()


def _make_dwg_folder(tmp_path: Path) -> Path:
    (tmp_path / "plan.dwg").write_bytes(b"fake")
    return tmp_path


def test_extract_dims(tmp_path: Path) -> None:
    folder = _make_dwg_folder(tmp_path)
    result = runner.invoke(app, ["extract-dims", "--folder", str(folder), "--mock"])
    assert result.exit_code == 0
    assert "Dimension Extraction Complete" in result.output


def test_extract_areas(tmp_path: Path) -> None:
    folder = _make_dwg_folder(tmp_path)
    result = runner.invoke(app, ["extract-areas", "--folder", str(folder), "--mock"])
    assert result.exit_code == 0
    assert "Area Extraction Complete" in result.output


def test_check_drawing(tmp_path: Path) -> None:
    folder = _make_dwg_folder(tmp_path)
    result = runner.invoke(
        app,
        ["check-drawing", "--folder", str(folder), "--rules", "ubbl-spatial", "--mock"],
    )
    assert result.exit_code == 0
    assert "Compliance Measurement Complete" in result.output


def test_update_titleblock(tmp_path: Path) -> None:
    folder = _make_dwg_folder(tmp_path)
    result = runner.invoke(
        app,
        [
            "update-titleblock",
            "--folder",
            str(folder),
            "--updates",
            "DATE=2024-06-01,DRAWN_BY=ZA",
            "--no-backup",
            "--mock",
        ],
    )
    assert result.exit_code == 0
    assert "Operation Complete" in result.output


def test_extract_schedule(tmp_path: Path) -> None:
    folder = _make_dwg_folder(tmp_path)
    result = runner.invoke(
        app,
        [
            "extract-schedule",
            "--folder",
            str(folder),
            "--block-name",
            "DOOR_SINGLE",
            "--mock",
        ],
    )
    assert result.exit_code == 0
    assert "Schedule Extraction Complete" in result.output


def test_manage_xrefs_list(tmp_path: Path) -> None:
    folder = _make_dwg_folder(tmp_path)
    result = runner.invoke(
        app,
        ["manage-xrefs-cmd", "--folder", str(folder), "--action", "list", "--mock"],
    )
    assert result.exit_code == 0
    assert "XREF" in result.output


def test_search_drawings(tmp_path: Path) -> None:
    folder = _make_dwg_folder(tmp_path)
    result = runner.invoke(
        app,
        ["search-drawings", "--folder", str(folder), "--text", "TIMBER", "--mock"],
    )
    assert result.exit_code == 0
    assert "Drawing Search Complete" in result.output


def test_batch_plot(tmp_path: Path) -> None:
    folder = _make_dwg_folder(tmp_path)
    result = runner.invoke(
        app,
        ["batch-plot-cmd", "--folder", str(folder), "--mock"],
    )
    assert result.exit_code == 0
    assert "Batch Plot Complete" in result.output


def test_purge(tmp_path: Path) -> None:
    folder = _make_dwg_folder(tmp_path)
    result = runner.invoke(
        app,
        ["purge", "--folder", str(folder), "--no-backup", "--mock"],
    )
    assert result.exit_code == 0
    assert "Batch Purge Complete" in result.output


def test_drawing_info(tmp_path: Path) -> None:
    folder = _make_dwg_folder(tmp_path)
    result = runner.invoke(
        app,
        ["drawing-info", "--folder", str(folder), "--mock"],
    )
    assert result.exit_code == 0
    assert "Drawing Info Summary" in result.output
