"""Tests for the Discovery Agent readiness scoring."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.discovery import DiscoveryAgent, SkillAcquisitionSpecification


def make_sas(**overrides) -> SkillAcquisitionSpecification:
    sas = SkillAcquisitionSpecification(source="test")
    for k, v in overrides.items():
        setattr(sas, k, v)
    return sas


def test_all_complete_is_100():
    agent = DiscoveryAgent()
    sas = make_sas(
        goal="do X",
        domain="3D modeling",
        software="Blender",
        software_version="4.0",
        workflow="reproduce",
        success_criteria="cube rendered",
        operate_software=True,
        sandbox_allowed=True,
        operating_system="Linux",
    )
    score, gaps = agent.readiness_score(sas)
    assert score == 100.0, score
    assert gaps == [], gaps


def test_critical_missing_regardless_of_score():
    agent = DiscoveryAgent()
    # Everything else filled, but goal missing -> gate not met.
    sas = make_sas(
        domain="x", software="Blender", workflow="reproduce",
        success_criteria="ok", operate_software=True, sandbox_allowed=True,
        operating_system="Linux",
    )
    score, gaps = agent.readiness_score(sas)
    assert score < 95.0, score
    assert "skill goal is defined" in gaps, gaps


def test_threshold_gate():
    agent = DiscoveryAgent()
    # Only goal + software + workflow filled (3 of 8) = 37.5%.
    sas = make_sas(
        goal="do X", software="Blender", workflow="reproduce",
    )
    score, gaps = agent.readiness_score(sas)
    assert score == 37.5, score
    assert score < 95.0


def test_sas_to_dict_contains_source():
    agent = DiscoveryAgent()
    sas = make_sas(goal="g", source="https://example.com/v")
    d = sas.to_dict()
    assert d["source"] == "https://example.com/v"
    assert d["goal"] == "g"


if __name__ == "__main__":
    test_all_complete_is_100()
    test_critical_missing_regardless_of_score()
    test_threshold_gate()
    test_sas_to_dict_contains_source()
    print("test_discovery.py: OK")
