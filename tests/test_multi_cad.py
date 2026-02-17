"""Tests for multi-CAD adapter support and factory logic."""

from __future__ import annotations

from autocad_batch_commander.acad.factory import get_acad_adapter
from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter


def test_factory_mock_engine() -> None:
    """cad_engine='mock' should always return MockAutoCADAdapter."""
    adapter = get_acad_adapter(cad_engine="mock")
    assert isinstance(adapter, MockAutoCADAdapter)


def test_factory_use_mock_flag() -> None:
    """use_mock=True should return MockAutoCADAdapter."""
    adapter = get_acad_adapter(use_mock=True)
    assert isinstance(adapter, MockAutoCADAdapter)


def test_factory_populates_new_entity_types(tmp_path) -> None:
    """Factory should populate dimensions, blocks, xrefs, etc. in mock."""
    (tmp_path / "test.dwg").write_bytes(b"fake")
    adapter = get_acad_adapter(use_mock=True, folder=tmp_path)

    # open the first DWG and check expanded data
    adapter.open_drawing(str(tmp_path / "test.dwg"))
    dims = adapter.get_dimensions()
    blocks = adapter.get_blocks()
    xrefs = adapter.get_xrefs()
    layouts = adapter.get_layouts()

    assert len(dims) > 0, "Factory should populate dimensions"
    assert len(blocks) > 0, "Factory should populate blocks"
    assert len(xrefs) > 0, "Factory should populate xrefs"
    assert len(layouts) > 0, "Factory should populate layouts"
    adapter.close_drawing()


def test_mock_adapter_new_layer_ops() -> None:
    """Test create_layer, set_layer_properties, delete_layer."""
    adapter = MockAutoCADAdapter()
    adapter.add_mock_drawing("test.dwg", layers=[])
    adapter.open_drawing("test.dwg")

    # Create
    assert adapter.create_layer("NEW-LAYER", color=3) is True
    assert adapter.create_layer("NEW-LAYER") is False  # duplicate

    # Set properties
    assert adapter.set_layer_properties("NEW-LAYER", color=5, is_on=False) is True
    layers = adapter.get_layers()
    layer = next(ly for ly in layers if ly.name == "NEW-LAYER")
    assert layer.color == 5
    assert layer.is_on is False

    # Delete
    assert adapter.delete_layer("NEW-LAYER") is True
    assert adapter.delete_layer("NEW-LAYER") is False  # already deleted

    adapter.close_drawing()


def test_mock_adapter_block_insert() -> None:
    """Test insert_block."""
    from autocad_batch_commander.models import Point3D

    adapter = MockAutoCADAdapter()
    adapter.add_mock_drawing("test.dwg")
    adapter.open_drawing("test.dwg")

    handle = adapter.insert_block("MY_BLOCK", Point3D(x=100, y=200), layer="FURNITURE")
    assert handle.startswith("BLK_")

    blocks = adapter.get_blocks()
    assert len(blocks) == 1
    assert blocks[0].name == "MY_BLOCK"
    assert blocks[0].layer == "FURNITURE"

    adapter.close_drawing()


def test_mock_adapter_purge_and_audit() -> None:
    """Test purge and audit_drawing."""
    adapter = MockAutoCADAdapter()
    adapter.add_mock_drawing("test.dwg")
    adapter.open_drawing("test.dwg")

    purged = adapter.purge()
    assert purged >= 0

    issues = adapter.audit_drawing()
    assert isinstance(issues, list)

    adapter.close_drawing()
