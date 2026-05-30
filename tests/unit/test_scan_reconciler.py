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
