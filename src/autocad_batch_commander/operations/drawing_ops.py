"""Drawing utility operations: purge, plot, search, info."""

from __future__ import annotations

import re
from pathlib import Path

from loguru import logger

from autocad_batch_commander.acad.port import AutoCADPort
from autocad_batch_commander.models import (
    BatchPlotRequest,
    BatchPurgeRequest,
    DrawingInfoRequest,
    DrawingInfoResult,
    DrawingSearchRequest,
    DrawingSearchResult,
    FileDetail,
    FileInfoDetail,
    FilePlotDetail,
    PlotResult,
    PurgeResult,
    SearchMatch,
)
from autocad_batch_commander.utils.file_ops import create_backup, get_dwg_files


def batch_purge(
    adapter: AutoCADPort,
    request: BatchPurgeRequest,
) -> PurgeResult:
    """Purge unused items (and optionally audit) across DWG files."""
    dwg_files = get_dwg_files(request.folder)
    result = PurgeResult()

    for dwg in dwg_files:
        try:
            if request.backup:
                create_backup(dwg)

            adapter.open_drawing(str(dwg))
            purged = adapter.purge()
            result.total_items_purged += purged

            if request.audit:
                issues = adapter.audit_drawing(fix=True)
                result.audit_issues.extend(issues)

            adapter.save_drawing()
            result.files_purged += 1
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


def batch_plot(
    adapter: AutoCADPort,
    request: BatchPlotRequest,
) -> PlotResult:
    """Plot layouts to PDF/DWF across DWG files."""
    dwg_files = get_dwg_files(request.folder)
    output_dir = request.output_dir or request.folder / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    result = PlotResult()

    for dwg in dwg_files:
        try:
            adapter.open_drawing(str(dwg))
            layouts = adapter.get_layouts()

            for layout in layouts:
                if layout.name == "Model":
                    continue  # skip model space
                if request.layout_name and layout.name != request.layout_name:
                    continue

                stem = Path(dwg).stem
                ext = request.output_format.lower()
                out_path = str(output_dir / f"{stem}_{layout.name}.{ext}")

                success = adapter.plot_layout(
                    layout.name, out_path, request.output_format
                )
                detail = FilePlotDetail(
                    file=str(dwg), layout=layout.name, output_file=out_path
                )
                if not success:
                    detail.error = "Plot failed"
                else:
                    result.files_plotted += 1

                result.details.append(detail)

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


def drawing_search(
    adapter: AutoCADPort,
    request: DrawingSearchRequest,
) -> DrawingSearchResult:
    """Search text, attributes, and layer names across DWG files."""
    dwg_files = get_dwg_files(request.folder)
    result = DrawingSearchResult(search_text=request.search_text)
    flags = 0 if request.case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(request.search_text), flags)

    for dwg in dwg_files:
        try:
            adapter.open_drawing(str(dwg))

            if "text" in request.search_in:
                for t in adapter.get_text_entities():
                    if pattern.search(t.text):
                        result.matches.append(
                            SearchMatch(
                                file=str(dwg),
                                match_type="text",
                                entity_handle=t.handle,
                                layer=t.layer,
                                matched_text=t.text,
                            )
                        )

            if "attributes" in request.search_in:
                for block in adapter.get_blocks():
                    for attr in adapter.get_block_attributes(block.handle):
                        if pattern.search(attr.value) or pattern.search(attr.tag):
                            result.matches.append(
                                SearchMatch(
                                    file=str(dwg),
                                    match_type="attribute",
                                    entity_handle=block.handle,
                                    layer=block.layer,
                                    matched_text=f"{attr.tag}={attr.value}",
                                )
                            )

            if "layers" in request.search_in:
                for layer in adapter.get_layers():
                    if pattern.search(layer.name):
                        result.matches.append(
                            SearchMatch(
                                file=str(dwg),
                                match_type="layer",
                                layer=layer.name,
                                matched_text=layer.name,
                            )
                        )

            result.total_matches += len(
                [m for m in result.matches if m.file == str(dwg)]
            )
            result.files_processed += 1
            adapter.close_drawing()

        except Exception as exc:
            logger.error(f"Error processing {dwg}: {exc}")
            result.errors.append(FileDetail(file=str(dwg), error=str(exc)))
            try:
                adapter.close_drawing()
            except Exception:
                pass

    result.total_matches = len(result.matches)
    return result


def get_drawing_info(
    adapter: AutoCADPort,
    request: DrawingInfoRequest,
) -> DrawingInfoResult:
    """Get comprehensive summary info for each DWG file."""
    dwg_files = get_dwg_files(request.folder)
    result = DrawingInfoResult()

    for dwg in dwg_files:
        try:
            adapter.open_drawing(str(dwg))

            info = FileInfoDetail(
                file=str(dwg),
                layer_count=len(adapter.get_layers()),
                text_count=len(adapter.get_text_entities()),
                dimension_count=len(adapter.get_dimensions()),
                block_count=len(adapter.get_blocks()),
                polyline_count=len(adapter.get_polylines()),
                xref_count=len(adapter.get_xrefs()),
                layout_count=len(adapter.get_layouts()),
                extents=adapter.get_drawing_extents(),
            )

            result.details.append(info)
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
