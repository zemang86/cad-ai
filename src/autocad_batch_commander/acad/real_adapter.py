"""Real AutoCAD adapter using win32com (Windows only)."""

from __future__ import annotations

import sys

from autocad_batch_commander.models import LayerEntity, TextEntity

if sys.platform != "win32":
    raise ImportError("RealAutoCADAdapter requires Windows and pywin32")

import win32com.client  # type: ignore[import-untyped]  # noqa: E402


class RealAutoCADAdapter:
    """Wraps the AutoCAD COM API via pywin32."""

    def __init__(self) -> None:
        self._acad = win32com.client.Dispatch("AutoCAD.Application")
        self._acad.Visible = False
        self._doc = None

    def open_drawing(self, path: str) -> None:
        self._doc = self._acad.Documents.Open(path)

    def close_drawing(self) -> None:
        if self._doc is not None:
            self._doc.Close(False)
            self._doc = None

    def save_drawing(self) -> None:
        if self._doc is None:
            raise RuntimeError("No drawing is open")
        self._doc.Save()

    def get_text_entities(self, layers: list[str] | None = None) -> list[TextEntity]:
        if self._doc is None:
            raise RuntimeError("No drawing is open")
        entities: list[TextEntity] = []
        for entity in self._doc.ModelSpace:
            try:
                if entity.EntityName in ("AcDbText", "AcDbMText"):
                    if layers and entity.Layer not in layers:
                        continue
                    entities.append(
                        TextEntity(
                            handle=entity.Handle,
                            text=entity.TextString,
                            layer=entity.Layer,
                            entity_type=entity.EntityName,
                        )
                    )
            except Exception:
                continue
        return entities

    def set_text(self, handle: str, new_text: str) -> None:
        if self._doc is None:
            raise RuntimeError("No drawing is open")
        entity = self._doc.HandleToObject(handle)
        entity.TextString = new_text

    def get_layers(self) -> list[LayerEntity]:
        if self._doc is None:
            raise RuntimeError("No drawing is open")
        result: list[LayerEntity] = []
        for layer in self._doc.Layers:
            result.append(
                LayerEntity(
                    name=layer.Name,
                    color=layer.color,
                    is_on=layer.LayerOn,
                    is_frozen=layer.Freeze,
                )
            )
        return result

    def rename_layer(self, old_name: str, new_name: str) -> bool:
        if self._doc is None:
            raise RuntimeError("No drawing is open")
        try:
            layer = self._doc.Layers.Item(old_name)
            layer.Name = new_name
            return True
        except Exception:
            return False
