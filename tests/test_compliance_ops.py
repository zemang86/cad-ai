"""Tests for compliance operations."""

from __future__ import annotations

import pytest

from autocad_batch_commander.models import ComplianceCheckRequest
from autocad_batch_commander.operations.compliance_ops import (
    check_compliance,
    list_rule_sets,
    load_rule_set,
)


def test_load_rule_set_spatial():
    """UBBL spatial rule set loads successfully."""
    rs = load_rule_set("ubbl-spatial")
    assert rs.source_short == "UBBL"
    assert rs.category == "spatial"
    assert len(rs.rules) > 10


def test_load_rule_set_fire():
    """UBBL fire rule set loads successfully."""
    rs = load_rule_set("ubbl-fire")
    assert rs.source_short == "UBBL"
    assert rs.category == "fire"
    assert len(rs.rules) > 5


def test_load_rule_set_not_found():
    """Missing rule set raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_rule_set("nonexistent-rules")


def test_list_rule_sets():
    """Available rule sets include both UBBL sets."""
    sets = list_rule_sets()
    assert "ubbl-spatial" in sets
    assert "ubbl-fire" in sets


def test_check_compliance_all_rules():
    """Check compliance loads all rules when no filters applied."""
    request = ComplianceCheckRequest()
    result = check_compliance(request)
    assert result.rule_sets_loaded == 2
    assert result.total_rules > 20
    assert len(result.findings) == result.total_rules


def test_check_compliance_building_type_filter():
    """Filtering by building type reduces findings."""
    request_all = ComplianceCheckRequest(building_type=None)
    result_all = check_compliance(request_all)

    request_residential = ComplianceCheckRequest(building_type="residential")
    result_residential = check_compliance(request_residential)

    # Residential should have fewer rules than all (some rules are commercial-only)
    assert result_residential.total_rules <= result_all.total_rules
    assert result_residential.total_rules > 0


def test_check_compliance_category_filter():
    """Filtering by category returns only matching rules."""
    request = ComplianceCheckRequest(
        rule_sets=["ubbl-spatial"],
        categories=["corridor"],
    )
    result = check_compliance(request)
    assert result.total_rules > 0
    for finding in result.findings:
        if finding.rule_id != "SYSTEM":
            assert (
                "corridor" in finding.tags
                or finding.parameter == "dead_end_corridor_length"
            )


def test_check_compliance_missing_ruleset():
    """Missing rule set produces an error finding."""
    request = ComplianceCheckRequest(rule_sets=["nonexistent"])
    result = check_compliance(request)
    assert any(f.rule_id == "SYSTEM" and f.status == "error" for f in result.findings)


def test_check_compliance_findings_have_thresholds():
    """Each finding includes threshold data for verification."""
    request = ComplianceCheckRequest(rule_sets=["ubbl-spatial"])
    result = check_compliance(request)
    for finding in result.findings:
        if finding.status == "to_verify":
            assert finding.threshold is not None
            assert finding.unit is not None
            assert finding.check_type is not None


def test_check_compliance_corridor_width_residential():
    """Residential corridor width rule has correct threshold."""
    request = ComplianceCheckRequest(
        rule_sets=["ubbl-spatial"],
        building_type="residential",
        categories=["corridor"],
    )
    result = check_compliance(request)
    corridor_rules = [f for f in result.findings if f.parameter == "corridor_width"]
    assert len(corridor_rules) == 1
    assert corridor_rules[0].threshold == 1.2
    assert corridor_rules[0].unit == "metres"
    assert corridor_rules[0].by_law == "By-Law 34(1)"
