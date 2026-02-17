"""Batch text find-and-replace operation."""

from __future__ import annotations

import re

from loguru import logger

from autocad_batch_commander.acad.port import AutoCADPort
from autocad_batch_commander.models import (
    FileDetail,
    OperationResult,
    TextReplaceRequest,
)
from autocad_batch_commander.utils.file_ops import create_backup, get_dwg_files


def _replace(original: str, find: str, replace: str, *, case_sensitive: bool) -> str:
    if case_sensitive:
        return original.replace(find, replace)
    return re.compile(re.escape(find), re.IGNORECASE).sub(replace, original)


def batch_find_replace(
    adapter: AutoCADPort,
    request: TextReplaceRequest,
) -> OperationResult:
    """Execute a batch text find-and-replace across all DWG files in the folder."""
    dwg_files = get_dwg_files(request.folder)
    result = OperationResult()

    for dwg in dwg_files:
        detail = FileDetail(file=str(dwg))
        try:
            if request.backup:
                create_backup(dwg)

            adapter.open_drawing(str(dwg))
            texts = adapter.get_text_entities(layers=request.layers)

            changes = 0
            for entity in texts:
                if request.case_sensitive:
                    match = request.find_text in entity.text
                else:
                    match = request.find_text.lower() in entity.text.lower()

                if match:
                    new_text = _replace(
                        entity.text,
                        request.find_text,
                        request.replace_text,
                        case_sensitive=request.case_sensitive,
                    )
                    adapter.set_text(entity.handle, new_text)
                    changes += 1

            if changes > 0:
                adapter.save_drawing()
                result.files_modified += 1
                result.total_changes += changes

            detail.changes = changes
            adapter.close_drawing()
            result.files_processed += 1

        except Exception as exc:
            logger.error(f"Error processing {dwg}: {exc}")
            detail.error = str(exc)
            result.errors.append(detail)
            try:
                adapter.close_drawing()
            except Exception:
                pass
            continue

        result.details.append(detail)

    return result
