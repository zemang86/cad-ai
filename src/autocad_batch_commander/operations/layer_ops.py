"""Batch layer rename and standardization operations."""

from __future__ import annotations

import json

from loguru import logger

from autocad_batch_commander.acad.port import AutoCADPort
from autocad_batch_commander.config import settings
from autocad_batch_commander.models import (
    FileDetail,
    LayerRenameRequest,
    LayerStandardizeRequest,
    OperationResult,
)
from autocad_batch_commander.utils.file_ops import create_backup, get_dwg_files


def batch_rename_layer(
    adapter: AutoCADPort,
    request: LayerRenameRequest,
) -> OperationResult:
    """Rename a single layer across all DWG files in the folder."""
    dwg_files = get_dwg_files(request.folder)
    result = OperationResult()

    for dwg in dwg_files:
        detail = FileDetail(file=str(dwg))
        try:
            if request.backup:
                create_backup(dwg)

            adapter.open_drawing(str(dwg))
            renamed = adapter.rename_layer(request.old_name, request.new_name)

            if renamed:
                adapter.save_drawing()
                result.files_modified += 1
                result.total_changes += 1
                detail.changes = 1

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


def load_standard_mappings(standard: str) -> dict[str, str]:
    """Load layer name mappings from a standards JSON file."""
    standards_path = settings.standards_dir / f"{standard.lower()}.json"
    if not standards_path.exists():
        raise FileNotFoundError(f"Standard file not found: {standards_path}")
    data = json.loads(standards_path.read_text())
    return data.get("mappings", {})


def batch_standardize_layers(
    adapter: AutoCADPort,
    request: LayerStandardizeRequest,
) -> OperationResult:
    """Standardize layer names across all DWG files based on a naming standard."""
    if request.custom_mappings:
        mappings = request.custom_mappings
    else:
        mappings = load_standard_mappings(request.standard)

    dwg_files = get_dwg_files(request.folder)
    result = OperationResult()

    for dwg in dwg_files:
        detail = FileDetail(file=str(dwg))
        try:
            if request.backup and not request.report_only:
                create_backup(dwg)

            adapter.open_drawing(str(dwg))
            layers = adapter.get_layers()

            changes = 0
            for layer in layers:
                if layer.name in mappings:
                    if not request.report_only:
                        renamed = adapter.rename_layer(layer.name, mappings[layer.name])
                        if renamed:
                            changes += 1
                    else:
                        changes += 1  # count would-be changes in report-only mode

            if changes > 0 and not request.report_only:
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
