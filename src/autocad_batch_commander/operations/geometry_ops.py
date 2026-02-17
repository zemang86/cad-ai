"""Geometry extraction and compliance measurement operations."""

from __future__ import annotations

import json

from loguru import logger

from autocad_batch_commander.acad.port import AutoCADPort
from autocad_batch_commander.config import settings
from autocad_batch_commander.models import (
    AreaExtractionRequest,
    AreaExtractionResult,
    ComplianceMeasurementRequest,
    ComplianceMeasurementResult,
    DimensionExtractionRequest,
    DimensionExtractionResult,
    FileAreaDetail,
    FileDetail,
    FileDimensionDetail,
    MeasurementFinding,
)
from autocad_batch_commander.operations.compliance_ops import load_rule_set
from autocad_batch_commander.utils.file_ops import get_dwg_files


def extract_dimensions(
    adapter: AutoCADPort,
    request: DimensionExtractionRequest,
) -> DimensionExtractionResult:
    """Extract all dimension entities from DWG files in the folder."""
    dwg_files = get_dwg_files(request.folder)
    result = DimensionExtractionResult()

    for dwg in dwg_files:
        try:
            adapter.open_drawing(str(dwg))
            dims = adapter.get_dimensions(layers=request.layers)

            if request.dimension_types:
                dims = [d for d in dims if d.dimension_type in request.dimension_types]

            result.details.append(FileDimensionDetail(file=str(dwg), dimensions=dims))
            result.total_dimensions += len(dims)
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


def extract_areas(
    adapter: AutoCADPort,
    request: AreaExtractionRequest,
) -> AreaExtractionResult:
    """Extract closed polyline areas from DWG files in the folder."""
    dwg_files = get_dwg_files(request.folder)
    result = AreaExtractionResult()

    for dwg in dwg_files:
        try:
            adapter.open_drawing(str(dwg))
            polys = adapter.get_polylines(layers=request.layers)
            closed = [p for p in polys if p.closed]

            if request.min_area is not None:
                closed = [p for p in closed if p.area >= request.min_area]
            if request.max_area is not None:
                closed = [p for p in closed if p.area <= request.max_area]

            result.details.append(FileAreaDetail(file=str(dwg), areas=closed))
            result.total_areas += len(closed)
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


def _load_dimension_mapping() -> list[dict]:
    """Load the layer → rule parameter mapping file."""
    mapping_path = settings.standards_dir / "dimension_mapping.json"
    if not mapping_path.exists():
        return []
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    return data.get("mappings", [])


def _match_layer_to_parameter(layer_name: str, mappings: list[dict]) -> str | None:
    """Check if a layer name matches any mapping pattern."""
    upper = layer_name.upper()
    for m in mappings:
        for pattern in m["layer_patterns"]:
            if pattern.upper() in upper:
                return m["rule_parameter"]
    return None


def measure_compliance(
    adapter: AutoCADPort,
    request: ComplianceMeasurementRequest,
) -> ComplianceMeasurementResult:
    """Extract dimensions from drawings and compare against compliance rules.

    This is the key differentiator: automated measurement verification.
    """
    dwg_files = get_dwg_files(request.folder)
    mappings = _load_dimension_mapping()
    result = ComplianceMeasurementResult()

    # Load all requested rule sets
    rules_by_param: dict[str, list] = {}
    for rule_name in request.rule_sets:
        try:
            rule_set = load_rule_set(rule_name)
            for rule in rule_set.rules:
                if request.building_type and rule.building_type:
                    if request.building_type not in rule.building_type:
                        continue
                rules_by_param.setdefault(rule.parameter, []).append(rule)
        except FileNotFoundError:
            logger.warning(f"Rule set '{rule_name}' not found, skipping")

    for dwg in dwg_files:
        try:
            adapter.open_drawing(str(dwg))
            dims = adapter.get_dimensions()

            for dim in dims:
                param = _match_layer_to_parameter(dim.layer, mappings)
                if param is None:
                    continue

                matching_rules = rules_by_param.get(param, [])
                for rule in matching_rules:
                    result.total_checks += 1
                    if rule.check_type == "min_dimension":
                        status = "pass" if dim.value >= rule.threshold else "fail"
                    elif rule.check_type == "max_dimension":
                        status = "pass" if dim.value <= rule.threshold else "fail"
                    else:
                        status = "pass"

                    if status == "pass":
                        result.pass_count += 1
                    else:
                        result.fail_count += 1

                    result.findings.append(
                        MeasurementFinding(
                            file=str(dwg),
                            rule_id=rule.id,
                            description=rule.description,
                            by_law=rule.by_law,
                            parameter=rule.parameter,
                            threshold=rule.threshold,
                            measured_value=dim.value,
                            unit=rule.unit,
                            status=status,
                            severity=rule.severity,
                        )
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

    return result
