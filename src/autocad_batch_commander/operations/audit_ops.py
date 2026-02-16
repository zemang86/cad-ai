"""Simplified drawing audit — layer compliance checks."""

from __future__ import annotations

import json

from loguru import logger

from autocad_batch_commander.acad.port import AutoCADPort
from autocad_batch_commander.config import settings
from autocad_batch_commander.models import AuditFinding, AuditRequest, AuditResult
from autocad_batch_commander.utils.file_ops import get_dwg_files


def _load_standard(standard: str) -> dict:
    path = settings.standards_dir / f"{standard.lower()}.json"
    if not path.exists():
        raise FileNotFoundError(f"Standard file not found: {path}")
    return json.loads(path.read_text())


def audit_drawings(
    adapter: AutoCADPort,
    request: AuditRequest,
) -> AuditResult:
    """Audit drawings for layer compliance against a naming standard."""
    standard_data = _load_standard(request.standard)
    valid_layer_names = set(standard_data.get("mappings", {}).values())
    required_layers = set(standard_data.get("required_layers", []))

    dwg_files = get_dwg_files(request.folder)
    result = AuditResult()

    for dwg in dwg_files:
        try:
            adapter.open_drawing(str(dwg))
            layers = adapter.get_layers()
            layer_names = {layer.name for layer in layers}

            file_findings: list[AuditFinding] = []

            # Check for non-standard layer names
            for layer in layers:
                if layer.name not in valid_layer_names and layer.name != "0":
                    file_findings.append(
                        AuditFinding(
                            file=str(dwg),
                            finding_type="non_standard_layer",
                            severity="warning",
                            message=f"Layer '{layer.name}' is not in the {request.standard} standard",
                            layer=layer.name,
                        )
                    )

            # Check for required layers that are missing
            for req_layer in required_layers:
                if req_layer not in layer_names:
                    file_findings.append(
                        AuditFinding(
                            file=str(dwg),
                            finding_type="missing_required_layer",
                            severity="error",
                            message=f"Required layer '{req_layer}' is missing",
                            layer=req_layer,
                        )
                    )

            adapter.close_drawing()
            result.files_processed += 1
            result.findings.extend(file_findings)
            result.total_findings += len(file_findings)

            if file_findings:
                result.non_compliant_files += 1
            else:
                result.compliant_files += 1

        except Exception as exc:
            logger.error(f"Error auditing {dwg}: {exc}")
            result.findings.append(
                AuditFinding(
                    file=str(dwg),
                    finding_type="error",
                    severity="error",
                    message=str(exc),
                )
            )
            result.total_findings += 1
            try:
                adapter.close_drawing()
            except Exception:
                pass

    return result
