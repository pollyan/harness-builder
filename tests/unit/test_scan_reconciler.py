from __future__ import annotations

import pytest

from harness_builder_agent.schemas.scan import EvidenceBundle, EvidenceFile, LLMCommandCandidate, LLMScanProposal
from harness_builder_agent.tools.scan_reconciler import ScanConflictError, reconcile_scan


def _proposal(command_source: str = "pom.xml", gate: str = "hard") -> LLMScanProposal:
    return LLMScanProposal(
        primary_stack="java-spring",
        stacks=["java", "maven"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
        architecture_signals=["spring mvc"],
        risk_areas=[{"path": "src/main/java", "reason": "backend code"}],
        command_candidates=[
            LLMCommandCandidate(
                id="unit_test",
                command="mvn test",
                type="test",
                gate=gate,
                source=command_source,
                confidence="high",
            )
        ],
        configs=[{"path": "application.yml", "kind": "config"}],
        ci_files=[],
        confidence="high",
        needs_human_confirmation=False,
        reasoning_summary="Maven project.",
    )


def test_reconcile_keeps_hard_gate_when_command_has_evidence():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[],
        key_files=[EvidenceFile(path="pom.xml", kind="build", summary="maven")],
    )

    inventory, commands, metadata = reconcile_scan(evidence, _proposal())

    assert inventory.primary_stack == "java-spring"
    assert commands.commands[0].gate == "hard"
    assert metadata.llm_status == "succeeded"
    assert metadata.warnings == []
    assert inventory.stack_extensions["scan_metadata"]["prompt_version"] == metadata.prompt_version
    assert inventory.stack_extensions["llm_scan_proposal"]["primary_stack"] == "java-spring"


def test_reconcile_downgrades_hard_gate_without_evidence():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[EvidenceFile(path="src/main/java/App.java", kind="source")],
        source_samples=[EvidenceFile(path="src/main/java/App.java", kind="source")],
    )

    _inventory, commands, metadata = reconcile_scan(evidence, _proposal(command_source="missing-pom.xml"))

    assert commands.commands[0].gate == "soft"
    assert commands.commands[0].confidence == "low"
    assert any("without evidence" in warning.message for warning in metadata.warnings)


def test_reconcile_persists_evidence_coverage_and_warnings():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[EvidenceFile(path="pom.xml", kind="build", priority="critical", bucket="build")],
        key_files=[EvidenceFile(path="pom.xml", kind="build", priority="critical", bucket="build")],
        coverage={
            "detected_file_count": 40,
            "selected_evidence_count": 3,
            "bucket_coverage": [
                {
                    "bucket": "source:.java",
                    "total_count": 30,
                    "selected_count": 2,
                    "skipped_count": 28,
                    "selected_paths": ["src/App.java"],
                }
            ],
            "warnings": [{"code": "source_sampling_truncated", "message": "source:.java skipped files"}],
        },
    )

    inventory, _commands, metadata = reconcile_scan(evidence, _proposal())

    assert metadata.coverage["selected_evidence_count"] == 3
    assert metadata.coverage["bucket_coverage"][0]["skipped_count"] == 28
    assert any(warning.code == "source_sampling_truncated" for warning in metadata.warnings)
    assert inventory.stack_extensions["scan_metadata"]["coverage"]["selected_evidence_count"] == 3


def test_reconcile_vetoes_impossible_dotnet_claim():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[EvidenceFile(path="pom.xml", kind="build")],
        key_files=[EvidenceFile(path="pom.xml", kind="build")],
    )
    proposal = _proposal()
    proposal.primary_stack = "dotnet-aspnet"
    proposal.stacks = ["dotnet"]

    with pytest.raises(ScanConflictError, match="dotnet"):
        reconcile_scan(evidence, proposal)


def test_reconcile_warns_when_secondary_stack_claim_lacks_evidence():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[EvidenceFile(path="pom.xml", kind="build", summary="maven")],
        key_files=[EvidenceFile(path="pom.xml", kind="build", summary="maven")],
    )
    proposal = _proposal()
    proposal.stacks = ["java", "maven", "node"]

    inventory, _commands, metadata = reconcile_scan(evidence, proposal)

    validation = inventory.stack_extensions["scan_validation"]
    assert validation["checked_claims"] == ["java-spring", "node"]
    assert validation["supported_claims"] == ["java-spring"]
    assert validation["unsupported_claims"] == [
        {
            "stack": "node",
            "reason": "LLM claimed node but no package.json or JS/TS/Vue evidence was found",
        }
    ]
    assert any(warning.code == "llm_stack_claim_without_evidence" for warning in metadata.warnings)
    assert inventory.stack_extensions["scan_warnings"] == [warning.model_dump(mode="json") for warning in metadata.warnings]


def test_reconcile_does_not_treat_javascript_evidence_as_java_support():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[
            EvidenceFile(path="package.json", kind="build"),
            EvidenceFile(path="src/app.js", kind="source"),
        ],
        key_files=[EvidenceFile(path="package.json", kind="build")],
        source_samples=[EvidenceFile(path="src/app.js", kind="source")],
    )
    proposal = _proposal(command_source="package.json", gate="soft")
    proposal.primary_stack = "node"
    proposal.stacks = ["javascript", "java"]
    proposal.command_candidates = []

    inventory, _commands, metadata = reconcile_scan(evidence, proposal)

    validation = inventory.stack_extensions["scan_validation"]
    assert validation["checked_claims"] == ["node", "java-spring"]
    assert validation["supported_claims"] == ["node"]
    assert validation["unsupported_claims"][0]["stack"] == "java-spring"
    assert any("java-spring" in warning.evidence for warning in metadata.warnings)


def test_reconcile_preserves_python_flask_react_multistack_profile():
    evidence = EvidenceBundle(
        repo_name="ai4se-like",
        root_path="/tmp/ai4se-like",
        files=[
            EvidenceFile(path="pyproject.toml", kind="build", summary="flask dependency"),
            EvidenceFile(path="requirements.txt", kind="build", summary="Flask"),
            EvidenceFile(path="app.py", kind="source", summary="from flask import Flask"),
            EvidenceFile(path="frontend/package.json", kind="build", summary="react vite typescript"),
            EvidenceFile(path="frontend/src/App.tsx", kind="source", summary="React component"),
        ],
        key_files=[
            EvidenceFile(path="pyproject.toml", kind="build", summary="flask dependency"),
            EvidenceFile(path="frontend/package.json", kind="build", summary="react vite typescript"),
        ],
        source_samples=[
            EvidenceFile(path="app.py", kind="source", summary="from flask import Flask"),
            EvidenceFile(path="frontend/src/App.tsx", kind="source", summary="React component"),
        ],
    )
    proposal = LLMScanProposal(
        primary_stack="python-flask",
        stacks=["python", "flask", "react", "typescript", "vite"],
        modules=[
            {"name": "api", "path": ".", "kind": "backend"},
            {"name": "web", "path": "frontend", "kind": "frontend"},
        ],
        architecture_signals=["Flask API and React frontend"],
        risk_areas=[],
        command_candidates=[
            LLMCommandCandidate(
                id="pytest",
                command="pytest",
                type="test",
                gate="hard",
                source="pyproject.toml",
                confidence="high",
            )
        ],
        configs=[{"path": "pyproject.toml", "kind": "python"}],
        ci_files=[],
        confidence="medium",
        needs_human_confirmation=True,
        reasoning_summary="Flask backend and React frontend evidence.",
    )

    inventory, commands, metadata = reconcile_scan(evidence, proposal)

    assert inventory.primary_stack == "python-flask"
    assert inventory.modules[0]["kind"] == "backend"
    assert inventory.modules[1]["kind"] == "frontend"
    validation = inventory.stack_extensions["scan_validation"]
    assert validation["checked_claims"] == ["python-flask", "node"]
    assert validation["supported_claims"] == ["python-flask", "node"]
    assert validation["unsupported_claims"] == []
    assert inventory.stack_extensions["stack_profile"]["composition_label"] == "Python Flask 后端 + React / TypeScript 前端"
    assert commands.commands[0].gate == "hard"
    assert metadata.warnings == []


def test_reconcile_vetoes_impossible_java_claim():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[EvidenceFile(path="package.json", kind="build")],
        key_files=[EvidenceFile(path="package.json", kind="build")],
    )
    proposal = _proposal(command_source="package.json")
    proposal.primary_stack = "java-spring"
    proposal.stacks = ["java"]

    with pytest.raises(ScanConflictError, match="Java"):
        reconcile_scan(evidence, proposal)
