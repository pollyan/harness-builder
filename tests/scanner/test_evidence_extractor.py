"""Tests for evidence_extractor — Task 4 of scanner v2."""
from __future__ import annotations

from pathlib import Path

from harness_builder.scanner.detectors.evidence_extractor import extract_evidence

FIXTURES = Path("tests/fixtures")


def test_extract_java_evidence():
    """LLM says Maven -> extract pom.xml/java details; result has java detected True."""
    repo = FIXTURES / "minimal-java-maven"
    llm_analysis = {"stackAnalysis": {"primary": {"name": "Java / Maven"}}}
    result = extract_evidence(repo, llm_analysis)
    assert "java" in result
    assert result["java"]["detected"] is True


def test_extract_dotnet_evidence():
    """LLM says .NET -> result has dotnet."""
    repo = FIXTURES / "minimal-dotnet"
    llm_analysis = {"stackAnalysis": {"primary": {"name": ".NET"}}}
    result = extract_evidence(repo, llm_analysis)
    assert "dotnet" in result


def test_extract_mixed_stacks():
    """LLM says Java primary and Vue secondary -> java and node evidence present."""
    repo = FIXTURES / "minimal-java-maven"
    llm_analysis = {
        "stackAnalysis": {
            "primary": {"name": "Java"},
            "secondary": [{"name": "Vue.js"}],
        }
    }
    result = extract_evidence(repo, llm_analysis)
    assert result["java"]["detected"] is True
    assert result["node"]["detected"] is True


def test_extract_unknown_stack():
    """Unknown stack -> genericFallback exists."""
    repo = FIXTURES / "unknown-stack"
    llm_analysis = {"stackAnalysis": {"primary": {"name": "Custom Stack"}}}
    result = extract_evidence(repo, llm_analysis)
    assert "genericFallback" in result


def test_extract_always_includes_filesystem():
    """Always include filesystem, ci, codeStructure."""
    repo = FIXTURES / "minimal-java-maven"
    llm_analysis = {"stackAnalysis": {"primary": {"name": "Java"}}}
    result = extract_evidence(repo, llm_analysis)
    assert "filesystem" in result
    assert "ci" in result
    assert "codeStructure" in result


def test_extract_detector_error_isolated(monkeypatch):
    """A failing selected detector should not abort evidence extraction."""
    from harness_builder.scanner.detectors import evidence_extractor

    def broken_detector(repo_root):
        raise RuntimeError("detector exploded")

    monkeypatch.setattr(evidence_extractor, "detect_java_maven", broken_detector)
    repo = FIXTURES / "minimal-java-maven"
    llm_analysis = {"stackAnalysis": {"primary": {"name": "Java"}}}

    result = extract_evidence(repo, llm_analysis)

    assert result["java"]["detected"] is False
    assert result["java"]["error"] == "detector exploded"
    assert "filesystem" in result


def test_extract_evidence_from_nested_stack_analysis():
    """Real LLM stackAnalysis may use nested backend/frontend fields, not primary/secondary."""
    repo = FIXTURES / "minimal-java-maven"
    llm_analysis = {
        "stackAnalysis": {
            "backend": {"language": "Java 8", "buildTool": "Maven"},
            "frontend": {"framework": "Vue.js", "buildTool": "npm"},
        }
    }

    result = extract_evidence(repo, llm_analysis)

    assert result["java"]["detected"] is True
    assert result["node"]["detected"] is True


def test_stack_mentions_does_not_treat_javascript_as_java_or_node():
    """JavaScript in a .NET repo should not imply Java or Node stack detectors."""
    repo = FIXTURES / "minimal-dotnet"
    llm_analysis = {"stackAnalysis": {"languages": ["C#", "JavaScript"], "frameworks": ["ASP.NET Core"]}}

    result = extract_evidence(repo, llm_analysis)

    assert "java" not in result
    assert "node" not in result
    assert result["dotnet"]["detected"] is True


def test_javascript_stack_triggers_node_detector_without_java_false_positive():
    """JavaScript-only stack should trigger node evidence without Java false positive."""
    repo = FIXTURES / "minimal-java-maven"
    llm_analysis = {"stackAnalysis": {"primary": {"name": "JavaScript"}}}

    result = extract_evidence(repo, llm_analysis)

    assert "java" not in result
    assert result["node"]["detected"] is True
