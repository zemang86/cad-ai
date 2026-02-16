"""In-memory mock adapter for development and testing on any platform."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field

from autocad_batch_commander.models import LayerEntity, TextEntity


@dataclass
class MockDrawing:
    """In-memory representation of one DWG file."""

    path: str
    texts: list[TextEntity] = field(default_factory=list)
    layers: list[LayerEntity] = field(default_factory=list)
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
    ) -> None:
        self._drawings[path] = MockDrawing(
            path=path,
            texts=deepcopy(texts or []),
            layers=deepcopy(layers or []),
        )

    # ── AutoCADPort implementation ────────────────────────────────

    def open_drawing(self, path: str) -> None:
        if path not in self._drawings:
            raise FileNotFoundError(f"Mock drawing not found: {path}")
        self._current = self._drawings[path]

    def close_drawing(self) -> None:
        self._current = None

    def save_drawing(self) -> None:
        if self._current is None:
            raise RuntimeError("No drawing is open")
        self._current.saved = True

    def get_text_entities(self, layers: list[str] | None = None) -> list[TextEntity]:
        if self._current is None:
            raise RuntimeError("No drawing is open")
        if layers is None:
            return list(self._current.texts)
        return [t for t in self._current.texts if t.layer in layers]

    def set_text(self, handle: str, new_text: str) -> None:
        if self._current is None:
            raise RuntimeError("No drawing is open")
        for t in self._current.texts:
            if t.handle == handle:
                t.text = new_text
                return
        raise KeyError(f"Handle not found: {handle}")

    def get_layers(self) -> list[LayerEntity]:
        if self._current is None:
            raise RuntimeError("No drawing is open")
        return list(self._current.layers)

    def rename_layer(self, old_name: str, new_name: str) -> bool:
        if self._current is None:
            raise RuntimeError("No drawing is open")
        for layer in self._current.layers:
            if layer.name == old_name:
                layer.name = new_name
                # Also update text entities that reference this layer
                for t in self._current.texts:
                    if t.layer == old_name:
                        t.layer = new_name
                return True
        return False
