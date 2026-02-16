"""Rule-based compliance checking against Malaysian building regulations."""

from __future__ import annotations

import json

from autocad_batch_commander.config import settings
from autocad_batch_commander.models import (
    ComplianceCheckRequest,
    ComplianceCheckResult,
    ComplianceFinding,
    ComplianceRuleSet,
)


def load_rule_set(rule_name: str) -> ComplianceRuleSet:
    """Load a compliance rule set from standards/rules/<rule_name>.json."""
    rules_dir = settings.standards_dir / "rules"
    rule_path = rules_dir / f"{rule_name}.json"
    if not rule_path.exists():
        raise FileNotFoundError(f"Rule set not found: {rule_path}")
    data = json.loads(rule_path.read_text(encoding="utf-8"))
    return ComplianceRuleSet(**data)


def list_rule_sets() -> list[str]:
    """List available rule set names."""
    rules_dir = settings.standards_dir / "rules"
    if not rules_dir.exists():
        return []
    return sorted(p.stem for p in rules_dir.glob("*.json"))


def check_compliance(request: ComplianceCheckRequest) -> ComplianceCheckResult:
    """Load rule sets and report applicable rules as compliance findings.

    This checks which rules apply based on building_type and category
    filters in the request. For now it reports all applicable rules as
    findings (since we don't yet have spatial measurement data from
    drawings to verify actual compliance).
    """
    findings: list[ComplianceFinding] = []
    rules_loaded = 0

    for rule_name in request.rule_sets:
        try:
            rule_set = load_rule_set(rule_name)
        except FileNotFoundError:
            findings.append(
                ComplianceFinding(
                    rule_id="SYSTEM",
                    description=f"Rule set '{rule_name}' not found",
                    by_law="N/A",
                    severity="error",
                    status="error",
                )
            )
            continue

        for rule in rule_set.rules:
            # Filter by building type if specified
            if request.building_type and rule.building_type:
                if request.building_type not in rule.building_type:
                    continue

            # Filter by category if specified
            if request.categories and rule.category not in request.categories:
                continue

            rules_loaded += 1
            findings.append(
                ComplianceFinding(
                    rule_id=rule.id,
                    description=rule.description,
                    by_law=rule.by_law,
                    severity=rule.severity,
                    status="to_verify",
                    check_type=rule.check_type,
                    parameter=rule.parameter,
                    threshold=rule.threshold,
                    unit=rule.unit,
                    tags=rule.tags,
                )
            )

    return ComplianceCheckResult(
        rule_sets_loaded=len(request.rule_sets),
        total_rules=rules_loaded,
        findings=findings,
    )
