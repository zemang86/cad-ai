"""In-memory mock adapter for development and testing on any platform."""

from __future__ import annotations

import uuid
from copy import deepcopy
from dataclasses import dataclass, field

from autocad_batch_commander.models import (
    AuditIssue,
    BlockAttribute,
    BlockReference,
    DimensionEntity,
    DrawingExtents,
    LayerEntity,
    LayoutInfo,
    Point3D,
    PolylineEntity,
    TextEntity,
    ViewportInfo,
    XrefInfo,
)


@dataclass
class MockDrawing:
    """In-memory representation of one DWG file."""

    path: str
    texts: list[TextEntity] = field(default_factory=list)
    layers: list[LayerEntity] = field(default_factory=list)
    dimensions: list[DimensionEntity] = field(default_factory=list)
    polylines: list[PolylineEntity] = field(default_factory=list)
    blocks: list[BlockReference] = field(default_factory=list)
    block_attributes: dict[str, list[BlockAttribute]] = field(default_factory=dict)
    xrefs: list[XrefInfo] = field(default_factory=list)
    layouts: list[LayoutInfo] = field(default_factory=list)
    viewports: list[ViewportInfo] = field(default_factory=list)
    extents: DrawingExtents = field(
        default_factory=lambda: DrawingExtents(
            min_point=Point3D(x=0, y=0, z=0),
            max_point=Point3D(x=100000, y=70000, z=0),
        )
    )
    saved: bool = False


class MockAutoCADAdapter:
    """Simulates AutoCAD drawing operations in memory.

    Usage in tests::

        adapter = MockAutoCADAdapter()
        adapter.add_mock_drawing("plan.dwg", texts=[...], layers=[...])
        adapter.open_drawing("plan.dwg")
    """

    def __init__(self) -> None:
        self._drawings: dict[str, MockDrawing] = {}
        self._current: MockDrawing | None = None

    # ── test helpers ──────────────────────────────────────────────

    def add_mock_drawing(
        self,
        path: str,
        texts: list[TextEntity] | None = None,
        layers: list[LayerEntity] | None = None,
        dimensions: list[DimensionEntity] | None = None,
        polylines: list[PolylineEntity] | None = None,
        blocks: list[BlockReference] | None = None,
        block_attributes: dict[str, list[BlockAttribute]] | None = None,
        xrefs: list[XrefInfo] | None = None,
        layouts: list[LayoutInfo] | None = None,
        viewports: list[ViewportInfo] | None = None,
        extents: DrawingExtents | None = None,
    ) -> None:
        self._drawings[path] = MockDrawing(
            path=path,
            texts=deepcopy(texts or []),
            layers=deepcopy(layers or []),
            dimensions=deepcopy(dimensions or []),
            polylines=deepcopy(polylines or []),
            blocks=deepcopy(blocks or []),
            block_attributes=deepcopy(block_attributes or {}),
            xrefs=deepcopy(xrefs or []),
            layouts=deepcopy(layouts or []),
            viewports=deepcopy(viewports or []),
            extents=deepcopy(
                extents
                or DrawingExtents(
                    min_point=Point3D(x=0, y=0, z=0),
                    max_point=Point3D(x=100000, y=70000, z=0),
                )
            ),
        )

    def _require_drawing(self) -> MockDrawing:
        if self._current is None:
            raise RuntimeError("No drawing is open")
        return self._current

    # ── Drawing lifecycle ─────────────────────────────────────────

    def open_drawing(self, path: str) -> None:
        if path not in self._drawings:
            raise FileNotFoundError(f"Mock drawing not found: {path}")
        self._current = self._drawings[path]

    def close_drawing(self) -> None:
        self._current = None

    def save_drawing(self) -> None:
        self._require_drawing().saved = True

    # ── Text ──────────────────────────────────────────────────────

    def get_text_entities(self, layers: list[str] | None = None) -> list[TextEntity]:
        dwg = self._require_drawing()
        if layers is None:
            return list(dwg.texts)
        return [t for t in dwg.texts if t.layer in layers]

    def set_text(self, handle: str, new_text: str) -> None:
        dwg = self._require_drawing()
        for t in dwg.texts:
            if t.handle == handle:
                t.text = new_text
                return
        raise KeyError(f"Handle not found: {handle}")

    # ── Layers ────────────────────────────────────────────────────

    def get_layers(self) -> list[LayerEntity]:
        return list(self._require_drawing().layers)

    def rename_layer(self, old_name: str, new_name: str) -> bool:
        dwg = self._require_drawing()
        for layer in dwg.layers:
            if layer.name == old_name:
                layer.name = new_name
                for t in dwg.texts:
                    if t.layer == old_name:
                        t.layer = new_name
                return True
        return False

    def create_layer(
        self, name: str, color: int = 7, is_on: bool = True, is_frozen: bool = False
    ) -> bool:
        dwg = self._require_drawing()
        if any(ly.name == name for ly in dwg.layers):
            return False
        dwg.layers.append(
            LayerEntity(name=name, color=color, is_on=is_on, is_frozen=is_frozen)
        )
        return True

    def set_layer_properties(
        self,
        name: str,
        *,
        color: int | None = None,
        is_on: bool | None = None,
        is_frozen: bool | None = None,
    ) -> bool:
        dwg = self._require_drawing()
        for layer in dwg.layers:
            if layer.name == name:
                if color is not None:
                    layer.color = color
                if is_on is not None:
                    layer.is_on = is_on
                if is_frozen is not None:
                    layer.is_frozen = is_frozen
                return True
        return False

    def delete_layer(self, name: str) -> bool:
        dwg = self._require_drawing()
        for i, layer in enumerate(dwg.layers):
            if layer.name == name:
                if name == "0":
                    return False  # cannot delete layer 0
                dwg.layers.pop(i)
                return True
        return False

    # ── Geometry ──────────────────────────────────────────────────

    def get_dimensions(self, layers: list[str] | None = None) -> list[DimensionEntity]:
        dwg = self._require_drawing()
        if layers is None:
            return list(dwg.dimensions)
        return [d for d in dwg.dimensions if d.layer in layers]

    def get_polylines(self, layers: list[str] | None = None) -> list[PolylineEntity]:
        dwg = self._require_drawing()
        if layers is None:
            return list(dwg.polylines)
        return [p for p in dwg.polylines if p.layer in layers]

    def get_drawing_extents(self) -> DrawingExtents:
        return self._require_drawing().extents

    # ── Blocks ────────────────────────────────────────────────────

    def get_blocks(self, layers: list[str] | None = None) -> list[BlockReference]:
        dwg = self._require_drawing()
        if layers is None:
            return list(dwg.blocks)
        return [b for b in dwg.blocks if b.layer in layers]

    def get_block_attributes(self, handle: str) -> list[BlockAttribute]:
        dwg = self._require_drawing()
        return list(dwg.block_attributes.get(handle, []))

    def set_block_attribute(self, handle: str, tag: str, value: str) -> bool:
        dwg = self._require_drawing()
        attrs = dwg.block_attributes.get(handle, [])
        for attr in attrs:
            if attr.tag == tag:
                attr.value = value
                return True
        return False

    def insert_block(
        self,
        name: str,
        insertion_point: Point3D,
        *,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        scale_z: float = 1.0,
        rotation: float = 0.0,
        layer: str = "0",
    ) -> str:
        dwg = self._require_drawing()
        handle = f"BLK_{uuid.uuid4().hex[:8].upper()}"
        ref = BlockReference(
            handle=handle,
            name=name,
            insertion_point=insertion_point,
            layer=layer,
            rotation=rotation,
            scale_x=scale_x,
            scale_y=scale_y,
            scale_z=scale_z,
        )
        dwg.blocks.append(ref)
        return handle

    # ── XREFs ─────────────────────────────────────────────────────

    def get_xrefs(self) -> list[XrefInfo]:
        return list(self._require_drawing().xrefs)

    def reload_xref(self, name: str) -> bool:
        dwg = self._require_drawing()
        for xref in dwg.xrefs:
            if xref.name == name:
                xref.status = "loaded"
                return True
        return False

    def attach_xref(self, name: str, path: str, xref_type: str = "attach") -> bool:
        dwg = self._require_drawing()
        if any(x.name == name for x in dwg.xrefs):
            return False
        dwg.xrefs.append(
            XrefInfo(name=name, path=path, xref_type=xref_type, status="loaded")
        )
        return True

    def detach_xref(self, name: str) -> bool:
        dwg = self._require_drawing()
        for i, xref in enumerate(dwg.xrefs):
            if xref.name == name:
                dwg.xrefs.pop(i)
                return True
        return False

    # ── Layouts / Viewports ───────────────────────────────────────

    def get_layouts(self) -> list[LayoutInfo]:
        return list(self._require_drawing().layouts)

    def get_viewports(self, layout_name: str | None = None) -> list[ViewportInfo]:
        dwg = self._require_drawing()
        return list(dwg.viewports)  # mock doesn't filter by layout

    # ── Plot ──────────────────────────────────────────────────────

    def plot_layout(
        self, layout_name: str, output_path: str, output_format: str = "PDF"
    ) -> bool:
        self._require_drawing()
        return True  # mock always succeeds

    # ── Utility ───────────────────────────────────────────────────

    def purge(self) -> int:
        self._require_drawing()
        return 3  # mock returns a fixed count

    def audit_drawing(self, fix: bool = True) -> list[AuditIssue]:
        self._require_drawing()
        return []  # mock has no issues
