"""External reference (XREF) management operations."""

from __future__ import annotations

from loguru import logger

from autocad_batch_commander.acad.port import AutoCADPort
from autocad_batch_commander.models import (
    FileDetail,
    FileXrefDetail,
    XrefListResult,
    XrefManageRequest,
)
from autocad_batch_commander.utils.file_ops import create_backup, get_dwg_files


def manage_xrefs(
    adapter: AutoCADPort,
    request: XrefManageRequest,
) -> XrefListResult:
    """Unified XREF management: list, reload, attach, or detach."""
    dwg_files = get_dwg_files(request.folder)
    result = XrefListResult(action=request.action)

    for dwg in dwg_files:
        try:
            adapter.open_drawing(str(dwg))

            if request.action == "list":
                xrefs = adapter.get_xrefs()
                result.details.append(FileXrefDetail(file=str(dwg), xrefs=xrefs))
                result.total_xrefs += len(xrefs)

            elif request.action == "reload":
                if request.xref_name:
                    if adapter.reload_xref(request.xref_name):
                        result.changes += 1
                        adapter.save_drawing()

            elif request.action == "attach":
                if request.xref_name and request.xref_path:
                    create_backup(dwg)
                    if adapter.attach_xref(
                        request.xref_name,
                        request.xref_path,
                        request.xref_type,
                    ):
                        result.changes += 1
                        adapter.save_drawing()

            elif request.action == "detach":
                if request.xref_name:
                    create_backup(dwg)
                    if adapter.detach_xref(request.xref_name):
                        result.changes += 1
                        adapter.save_drawing()

            result.files_processed += 1
            adapter.close_drawing()

        except Exception as exc:
            logger.error(f"Error processing {dwg}: {exc}")
            result.errors.append(FileDetail(file=str(dwg), error=str(exc)))
            try:
                adapter.close_drawing()
            except Exception:
                pass

    return result
