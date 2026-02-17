"""ZWCAD adapter using win32com (Windows only)."""

from __future__ import annotations

from autocad_batch_commander.acad.com_base import COMAdapterBase


class ZWCADAdapter(COMAdapterBase):
    """Wraps the ZWCAD COM API via pywin32."""

    _dispatch_name = "ZWCAD.Application"
