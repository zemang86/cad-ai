"""Abstract port (Protocol) that all AutoCAD adapters must implement."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

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


@runtime_checkable
class AutoCADPort(Protocol):
    """Protocol defining the interface for interacting with AutoCAD drawings."""

    # ── Drawing lifecycle ──────────────────────────────────────────

    def open_drawing(self, path: str) -> None:
        """Open a drawing file."""
        ...

    def close_drawing(self) -> None:
        """Close the currently open drawing without saving."""
        ...

    def save_drawing(self) -> None:
        """Save the currently open drawing."""
        ...

    # ── Text ───────────────────────────────────────────────────────

    def get_text_entities(self, layers: list[str] | None = None) -> list[TextEntity]:
        """Return all text/mtext entities, optionally filtered by layer names."""
        ...

    def set_text(self, handle: str, new_text: str) -> None:
        """Update the text of an entity identified by its handle."""
        ...

    # ── Layers ─────────────────────────────────────────────────────

    def get_layers(self) -> list[LayerEntity]:
        """Return all layers in the current drawing."""
        ...

    def rename_layer(self, old_name: str, new_name: str) -> bool:
        """Rename a layer. Returns True if the layer existed and was renamed."""
        ...

    def create_layer(
        self, name: str, color: int = 7, is_on: bool = True, is_frozen: bool = False
    ) -> bool:
        """Create a new layer. Returns True if created, False if it already exists."""
        ...

    def set_layer_properties(
        self,
        name: str,
        *,
        color: int | None = None,
        is_on: bool | None = None,
        is_frozen: bool | None = None,
    ) -> bool:
        """Set properties on an existing layer. Returns True if the layer was found."""
        ...

    def delete_layer(self, name: str) -> bool:
        """Delete a layer. Returns True if deleted, False if not found or undeletable."""
        ...

    # ── Geometry ───────────────────────────────────────────────────

    def get_dimensions(self, layers: list[str] | None = None) -> list[DimensionEntity]:
        """Return all dimension entities, optionally filtered by layer."""
        ...

    def get_polylines(self, layers: list[str] | None = None) -> list[PolylineEntity]:
        """Return all polyline entities, optionally filtered by layer."""
        ...

    def get_drawing_extents(self) -> DrawingExtents:
        """Return the bounding box of all entities in the drawing."""
        ...

    # ── Blocks ─────────────────────────────────────────────────────

    def get_blocks(self, layers: list[str] | None = None) -> list[BlockReference]:
        """Return all block references, optionally filtered by layer."""
        ...

    def get_block_attributes(self, handle: str) -> list[BlockAttribute]:
        """Return attributes for a block reference identified by handle."""
        ...

    def set_block_attribute(self, handle: str, tag: str, value: str) -> bool:
        """Set an attribute value on a block reference. Returns True if found."""
        ...

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
        """Insert a block and return the handle of the new block reference."""
        ...

    # ── XREFs ──────────────────────────────────────────────────────

    def get_xrefs(self) -> list[XrefInfo]:
        """Return all external references in the current drawing."""
        ...

    def reload_xref(self, name: str) -> bool:
        """Reload an external reference. Returns True if successful."""
        ...

    def attach_xref(self, name: str, path: str, xref_type: str = "attach") -> bool:
        """Attach an external reference. Returns True if successful."""
        ...

    def detach_xref(self, name: str) -> bool:
        """Detach an external reference. Returns True if successful."""
        ...

    # ── Layouts / Viewports ────────────────────────────────────────

    def get_layouts(self) -> list[LayoutInfo]:
        """Return all layout tabs in the current drawing."""
        ...

    def get_viewports(self, layout_name: str | None = None) -> list[ViewportInfo]:
        """Return viewports, optionally filtered by layout name."""
        ...

    # ── Plot ───────────────────────────────────────────────────────

    def plot_layout(
        self, layout_name: str, output_path: str, output_format: str = "PDF"
    ) -> bool:
        """Plot a layout to a file. Returns True if successful."""
        ...

    # ── Utility ────────────────────────────────────────────────────

    def purge(self) -> int:
        """Purge unused items from the drawing. Returns count of items purged."""
        ...

    def audit_drawing(self, fix: bool = True) -> list[AuditIssue]:
        """Audit the drawing for errors. Returns list of issues found."""
        ...
