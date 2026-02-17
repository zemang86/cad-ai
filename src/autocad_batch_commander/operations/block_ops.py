"""Block operations: title block updates, schedule extraction, block insertion."""

from __future__ import annotations

from loguru import logger

from autocad_batch_commander.acad.port import AutoCADPort
from autocad_batch_commander.models import (
    BlockInsertRequest,
    FileDetail,
    OperationResult,
    ScheduleExtractionRequest,
    ScheduleResult,
    ScheduleRow,
    TitleBlockUpdateRequest,
)
from autocad_batch_commander.utils.file_ops import create_backup, get_dwg_files


def batch_update_title_blocks(
    adapter: AutoCADPort,
    request: TitleBlockUpdateRequest,
) -> OperationResult:
    """Update title block attributes across all DWG files in the folder."""
    dwg_files = get_dwg_files(request.folder)
    result = OperationResult()

    for dwg in dwg_files:
        detail = FileDetail(file=str(dwg))
        try:
            if request.backup:
                create_backup(dwg)

            adapter.open_drawing(str(dwg))
            blocks = adapter.get_blocks()
            changes = 0

            for block in blocks:
                if block.name != request.block_name:
                    continue
                for tag, value in request.updates.items():
                    if adapter.set_block_attribute(block.handle, tag, value):
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


def extract_schedule(
    adapter: AutoCADPort,
    request: ScheduleExtractionRequest,
) -> ScheduleResult:
    """Extract schedule data from block attributes across DWG files."""
    dwg_files = get_dwg_files(request.folder)
    result = ScheduleResult(block_name=request.block_name)

    for dwg in dwg_files:
        try:
            adapter.open_drawing(str(dwg))
            blocks = adapter.get_blocks()

            for block in blocks:
                if block.name != request.block_name:
                    continue
                attrs = adapter.get_block_attributes(block.handle)
                attr_dict: dict[str, str] = {}
                for attr in attrs:
                    if request.tags is None or attr.tag in request.tags:
                        attr_dict[attr.tag] = attr.value

                if attr_dict:
                    result.rows.append(
                        ScheduleRow(
                            file=str(dwg),
                            block_handle=block.handle,
                            attributes=attr_dict,
                        )
                    )
                    result.total_entries += 1

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


def batch_insert_blocks(
    adapter: AutoCADPort,
    request: BlockInsertRequest,
) -> OperationResult:
    """Insert named blocks at specified points across DWG files."""
    dwg_files = get_dwg_files(request.folder)
    result = OperationResult()

    for dwg in dwg_files:
        detail = FileDetail(file=str(dwg))
        try:
            if request.backup:
                create_backup(dwg)

            adapter.open_drawing(str(dwg))
            changes = 0

            for point in request.insertion_points:
                adapter.insert_block(
                    request.block_name,
                    point,
                    scale_x=request.scale,
                    scale_y=request.scale,
                    scale_z=request.scale,
                    rotation=request.rotation,
                    layer=request.layer,
                )
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
