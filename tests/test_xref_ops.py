"""Tests for XREF management operations."""

from __future__ import annotations

from pathlib import Path

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.models import (
    LayerEntity,
    XrefInfo,
    XrefManageRequest,
)
from autocad_batch_commander.operations.xref_ops import manage_xrefs


def _adapter_with_xrefs(tmp_path: Path) -> MockAutoCADAdapter:
    (tmp_path / "plan.dwg").write_bytes(b"fake")

    adapter = MockAutoCADAdapter()
    adapter.add_mock_drawing(
        str(tmp_path / "plan.dwg"),
        layers=[LayerEntity(name="0")],
        xrefs=[
            XrefInfo(name="STRUCTURAL", path="./xref/structural.dwg", status="loaded"),
            XrefInfo(name="MEP", path="./xref/mep.dwg", status="unloaded"),
        ],
    )
    return adapter


def test_list_xrefs(tmp_path: Path) -> None:
    adapter = _adapter_with_xrefs(tmp_path)
    request = XrefManageRequest(folder=tmp_path, action="list")
    result = manage_xrefs(adapter, request)

    assert result.files_processed == 1
    assert result.total_xrefs == 2
    assert result.action == "list"
    assert len(result.details) == 1
    assert result.details[0].xrefs[0].name == "STRUCTURAL"


def test_reload_xref(tmp_path: Path) -> None:
    adapter = _adapter_with_xrefs(tmp_path)
    request = XrefManageRequest(folder=tmp_path, action="reload", xref_name="MEP")
    result = manage_xrefs(adapter, request)

    assert result.files_processed == 1
    assert result.changes == 1


def test_attach_xref(tmp_path: Path) -> None:
    adapter = _adapter_with_xrefs(tmp_path)
    request = XrefManageRequest(
        folder=tmp_path,
        action="attach",
        xref_name="ELECTRICAL",
        xref_path="./xref/electrical.dwg",
    )
    result = manage_xrefs(adapter, request)

    assert result.files_processed == 1
    assert result.changes == 1


def test_attach_duplicate_xref(tmp_path: Path) -> None:
    adapter = _adapter_with_xrefs(tmp_path)
    request = XrefManageRequest(
        folder=tmp_path,
        action="attach",
        xref_name="STRUCTURAL",
        xref_path="./xref/structural.dwg",
    )
    result = manage_xrefs(adapter, request)

    assert result.changes == 0  # already exists


def test_detach_xref(tmp_path: Path) -> None:
    adapter = _adapter_with_xrefs(tmp_path)
    request = XrefManageRequest(folder=tmp_path, action="detach", xref_name="MEP")
    result = manage_xrefs(adapter, request)

    assert result.files_processed == 1
    assert result.changes == 1
