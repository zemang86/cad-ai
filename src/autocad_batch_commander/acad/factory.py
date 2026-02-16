"""Factory for selecting the appropriate AutoCAD adapter."""

from __future__ import annotations

import sys

from autocad_batch_commander.acad.mock_adapter import MockAutoCADAdapter
from autocad_batch_commander.acad.port import AutoCADPort


def get_acad_adapter(*, use_mock: bool = False) -> AutoCADPort:
    """Return an adapter instance based on platform and user preference.

    On non-Windows platforms, the mock adapter is always returned.
    On Windows, the real adapter is returned unless *use_mock* is True.
    """
    if use_mock or sys.platform != "win32":
        return MockAutoCADAdapter()  # type: ignore[return-value]

    from autocad_batch_commander.acad.real_adapter import RealAutoCADAdapter

    return RealAutoCADAdapter()  # type: ignore[return-value]
