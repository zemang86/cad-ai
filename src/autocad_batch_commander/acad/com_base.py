"""Shared COM base class for AutoCAD-compatible CAD applications."""

from __future__ import annotations

import sys

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

if sys.platform != "win32":
    raise ImportError("COM adapters require Windows and pywin32")

import win32com.client  # type: ignore[import-untyped]  # noqa: E402


class COMAdapterBase:
    """Base class for COM-based CAD adapters (AutoCAD, BricsCAD, ZWCAD).

    Subclasses set ``_dispatch_name`` to the appropriate COM ProgID.
    """

    _dispatch_name: str = "AutoCAD.Application"

    def __init__(self) -> None:
        self._acad = win32com.client.Dispatch(self._dispatch_name)
        self._acad.Visible = False
        self._doc = None

    def _require_doc(self):
        if self._doc is None:
            raise RuntimeError("No drawing is open")
        return self._doc

    # ── Drawing lifecycle ─────────────────────────────────────────

    def open_drawing(self, path: str) -> None:
        self._doc = self._acad.Documents.Open(path)

    def close_drawing(self) -> None:
        if self._doc is not None:
            self._doc.Close(False)
            self._doc = None

    def save_drawing(self) -> None:
        self._require_doc().Save()

    # ── Text ──────────────────────────────────────────────────────

    def get_text_entities(self, layers: list[str] | None = None) -> list[TextEntity]:
        doc = self._require_doc()
        entities: list[TextEntity] = []
        for entity in doc.ModelSpace:
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
        doc = self._require_doc()
        entity = doc.HandleToObject(handle)
        entity.TextString = new_text

    # ── Layers ────────────────────────────────────────────────────

    def get_layers(self) -> list[LayerEntity]:
        doc = self._require_doc()
        result: list[LayerEntity] = []
        for layer in doc.Layers:
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
        doc = self._require_doc()
        try:
            layer = doc.Layers.Item(old_name)
            layer.Name = new_name
            return True
        except Exception:
            return False

    def create_layer(
        self, name: str, color: int = 7, is_on: bool = True, is_frozen: bool = False
    ) -> bool:
        doc = self._require_doc()
        try:
            doc.Layers.Item(name)
            return False  # already exists
        except Exception:
            layer = doc.Layers.Add(name)
            layer.color = color
            layer.LayerOn = is_on
            if is_frozen:
                layer.Freeze = True
            return True

    def set_layer_properties(
        self,
        name: str,
        *,
        color: int | None = None,
        is_on: bool | None = None,
        is_frozen: bool | None = None,
    ) -> bool:
        doc = self._require_doc()
        try:
            layer = doc.Layers.Item(name)
        except Exception:
            return False
        if color is not None:
            layer.color = color
        if is_on is not None:
            layer.LayerOn = is_on
        if is_frozen is not None:
            layer.Freeze = is_frozen
        return True

    def delete_layer(self, name: str) -> bool:
        doc = self._require_doc()
        try:
            layer = doc.Layers.Item(name)
            layer.Delete()
            return True
        except Exception:
            return False

    # ── Geometry ──────────────────────────────────────────────────

    def get_dimensions(self, layers: list[str] | None = None) -> list[DimensionEntity]:
        doc = self._require_doc()
        dims: list[DimensionEntity] = []
        dim_types = {
            "AcDbRotatedDimension": "linear",
            "AcDbAlignedDimension": "aligned",
            "AcDb3PointAngularDimension": "angular",
            "AcDbRadialDimension": "radial",
            "AcDbDiametricDimension": "diametric",
        }
        for entity in doc.ModelSpace:
            try:
                ename = entity.EntityName
                if ename in dim_types:
                    if layers and entity.Layer not in layers:
                        continue
                    dims.append(
                        DimensionEntity(
                            handle=entity.Handle,
                            dimension_type=dim_types[ename],
                            value=entity.Measurement,
                            text_override=getattr(entity, "TextOverride", ""),
                            layer=entity.Layer,
                        )
                    )
            except Exception:
                continue
        return dims

    def get_polylines(self, layers: list[str] | None = None) -> list[PolylineEntity]:
        doc = self._require_doc()
        polys: list[PolylineEntity] = []
        for entity in doc.ModelSpace:
            try:
                if entity.EntityName in ("AcDbPolyline", "AcDb2dPolyline"):
                    if layers and entity.Layer not in layers:
                        continue
                    coords = list(entity.Coordinates)
                    vertices = [
                        Point3D(x=coords[i], y=coords[i + 1])
                        for i in range(0, len(coords), 2)
                    ]
                    polys.append(
                        PolylineEntity(
                            handle=entity.Handle,
                            vertices=vertices,
                            closed=entity.Closed,
                            area=entity.Area if entity.Closed else 0.0,
                            perimeter=entity.Length,
                            layer=entity.Layer,
                        )
                    )
            except Exception:
                continue
        return polys

    def get_drawing_extents(self) -> DrawingExtents:
        doc = self._require_doc()
        ext_min = doc.GetVariable("EXTMIN")
        ext_max = doc.GetVariable("EXTMAX")
        return DrawingExtents(
            min_point=Point3D(x=ext_min[0], y=ext_min[1], z=ext_min[2]),
            max_point=Point3D(x=ext_max[0], y=ext_max[1], z=ext_max[2]),
        )

    # ── Blocks ────────────────────────────────────────────────────

    def get_blocks(self, layers: list[str] | None = None) -> list[BlockReference]:
        doc = self._require_doc()
        refs: list[BlockReference] = []
        for entity in doc.ModelSpace:
            try:
                if entity.EntityName == "AcDbBlockReference":
                    if layers and entity.Layer not in layers:
                        continue
                    ip = entity.InsertionPoint
                    refs.append(
                        BlockReference(
                            handle=entity.Handle,
                            name=entity.Name,
                            insertion_point=Point3D(x=ip[0], y=ip[1], z=ip[2]),
                            layer=entity.Layer,
                            rotation=entity.Rotation,
                            scale_x=entity.XScaleFactor,
                            scale_y=entity.YScaleFactor,
                            scale_z=entity.ZScaleFactor,
                        )
                    )
            except Exception:
                continue
        return refs

    def get_block_attributes(self, handle: str) -> list[BlockAttribute]:
        doc = self._require_doc()
        entity = doc.HandleToObject(handle)
        attrs: list[BlockAttribute] = []
        try:
            for attr in entity.GetAttributes():
                attrs.append(
                    BlockAttribute(
                        tag=attr.TagString,
                        value=attr.TextString,
                        handle=attr.Handle,
                    )
                )
        except Exception:
            pass
        return attrs

    def set_block_attribute(self, handle: str, tag: str, value: str) -> bool:
        doc = self._require_doc()
        entity = doc.HandleToObject(handle)
        try:
            for attr in entity.GetAttributes():
                if attr.TagString == tag:
                    attr.TextString = value
                    return True
        except Exception:
            pass
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
        doc = self._require_doc()
        pt = (insertion_point.x, insertion_point.y, insertion_point.z)
        ref = doc.ModelSpace.InsertBlock(pt, name, scale_x, scale_y, scale_z, rotation)
        ref.Layer = layer
        return ref.Handle

    # ── XREFs ─────────────────────────────────────────────────────

    def get_xrefs(self) -> list[XrefInfo]:
        doc = self._require_doc()
        xrefs: list[XrefInfo] = []
        for block in doc.Blocks:
            try:
                if block.IsXRef:
                    xrefs.append(
                        XrefInfo(
                            name=block.Name,
                            path=block.Path,
                            xref_type="attach",
                            status="loaded",
                        )
                    )
            except Exception:
                continue
        return xrefs

    def reload_xref(self, name: str) -> bool:
        doc = self._require_doc()
        try:
            doc.Blocks.Item(name).Reload()
            return True
        except Exception:
            return False

    def attach_xref(self, name: str, path: str, xref_type: str = "attach") -> bool:
        doc = self._require_doc()
        try:
            overlay = xref_type == "overlay"
            doc.Blocks.Item(name)  # check if exists
            return False
        except Exception:
            try:
                pt = (0.0, 0.0, 0.0)
                doc.ModelSpace.AttachExternalReference(
                    path, name, pt, 1.0, 1.0, 1.0, 0.0, overlay
                )
                return True
            except Exception:
                return False

    def detach_xref(self, name: str) -> bool:
        doc = self._require_doc()
        try:
            block = doc.Blocks.Item(name)
            block.Detach()
            return True
        except Exception:
            return False

    # ── Layouts / Viewports ───────────────────────────────────────

    def get_layouts(self) -> list[LayoutInfo]:
        doc = self._require_doc()
        layouts: list[LayoutInfo] = []
        for layout in doc.Layouts:
            layouts.append(
                LayoutInfo(
                    name=layout.Name,
                    paper_size=getattr(layout, "CanonicalMediaName", ""),
                    plot_device=getattr(layout, "ConfigName", ""),
                )
            )
        return layouts

    def get_viewports(self, layout_name: str | None = None) -> list[ViewportInfo]:
        doc = self._require_doc()
        vps: list[ViewportInfo] = []
        for entity in doc.PaperSpace:
            try:
                if entity.EntityName == "AcDbViewport":
                    vps.append(
                        ViewportInfo(
                            handle=entity.Handle,
                            width=entity.Width,
                            height=entity.Height,
                            scale=entity.CustomScale,
                        )
                    )
            except Exception:
                continue
        return vps

    # ── Plot ──────────────────────────────────────────────────────

    def plot_layout(
        self, layout_name: str, output_path: str, output_format: str = "PDF"
    ) -> bool:
        doc = self._require_doc()
        try:
            layout = doc.Layouts.Item(layout_name)
            doc.ActiveLayout = layout
            plot = doc.Plot
            plot.PlotToFile(output_path)
            return True
        except Exception:
            return False

    # ── Utility ───────────────────────────────────────────────────

    def purge(self) -> int:
        doc = self._require_doc()
        try:
            doc.PurgeAll()
            return 1  # COM PurgeAll doesn't return count
        except Exception:
            return 0

    def audit_drawing(self, fix: bool = True) -> list[AuditIssue]:
        doc = self._require_doc()
        try:
            doc.AuditInfo(fix)
        except Exception:
            pass
        return []
