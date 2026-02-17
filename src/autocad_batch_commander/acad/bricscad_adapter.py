"""BricsCAD adapter using win32com (Windows only)."""

from __future__ import annotations

from autocad_batch_commander.acad.com_base import COMAdapterBase


class BricsCADAdapter(COMAdapterBase):
    """Wraps the BricsCAD COM API via pywin32."""

    _dispatch_name = "BricscadApp.AcadApplication"
