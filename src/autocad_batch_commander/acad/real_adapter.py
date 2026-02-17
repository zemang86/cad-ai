"""Real AutoCAD adapter using win32com (Windows only)."""

from __future__ import annotations

from autocad_batch_commander.acad.com_base import COMAdapterBase


class RealAutoCADAdapter(COMAdapterBase):
    """Wraps the AutoCAD COM API via pywin32."""

    _dispatch_name = "AutoCAD.Application"
