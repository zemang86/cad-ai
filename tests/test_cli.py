"""Tests for the CLI interface via Typer CliRunner."""

from pathlib import Path

from typer.testing import CliRunner

from autocad_batch_commander.cli.app import app

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "AutoCAD Batch Commander" in result.output


def test_change_text_mock(tmp_path: Path):
    # Create a dummy DWG so the folder isn't empty
    (tmp_path / "test.dwg").write_bytes(b"fake")
    result = runner.invoke(
        app,
        [
            "change-text",
            "--folder", str(tmp_path),
            "--find", "OLD",
            "--replace", "NEW",
            "--mock",
            "--no-backup",
        ],
    )
    assert result.exit_code == 0
    assert "Operation Complete" in result.output


def test_rename_layer_mock(tmp_path: Path):
    (tmp_path / "test.dwg").write_bytes(b"fake")
    result = runner.invoke(
        app,
        [
            "rename-layer",
            "--folder", str(tmp_path),
            "--old-name", "WALL",
            "--new-name", "A-WALL",
            "--mock",
            "--no-backup",
        ],
    )
    assert result.exit_code == 0
    assert "Operation Complete" in result.output


def test_standardize_layers_mock(tmp_path: Path):
    (tmp_path / "test.dwg").write_bytes(b"fake")
    result = runner.invoke(
        app,
        [
            "standardize-layers",
            "--folder", str(tmp_path),
            "--standard", "AIA",
            "--mock",
            "--no-backup",
        ],
    )
    assert result.exit_code == 0
    assert "Operation Complete" in result.output


def test_audit_mock(tmp_path: Path):
    (tmp_path / "test.dwg").write_bytes(b"fake")
    result = runner.invoke(
        app,
        [
            "audit",
            "--folder", str(tmp_path),
            "--standard", "AIA",
            "--mock",
        ],
    )
    assert result.exit_code == 0
    assert "Audit Complete" in result.output
