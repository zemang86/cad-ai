"""Abstract port (Protocol) that all AutoCAD adapters must implement."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from autocad_batch_commander.models import LayerEntity, TextEntity


@runtime_checkable
class AutoCADPort(Protocol):
    """Protocol defining the interface for interacting with AutoCAD drawings."""

    def open_drawing(self, path: str) -> None:
        """Open a drawing file."""
        ...

    def close_drawing(self) -> None:
        """Close the currently open drawing without saving."""
        ...

    def save_drawing(self) -> None:
        """Save the currently open drawing."""
        ...

    def get_text_entities(self, layers: list[str] | None = None) -> list[TextEntity]:
        """Return all text/mtext entities, optionally filtered by layer names."""
        ...

    def set_text(self, handle: str, new_text: str) -> None:
        """Update the text of an entity identified by its handle."""
        ...

    def get_layers(self) -> list[LayerEntity]:
        """Return all layers in the current drawing."""
        ...

    def rename_layer(self, old_name: str, new_name: str) -> bool:
        """Rename a layer. Returns True if the layer existed and was renamed."""
        ...
