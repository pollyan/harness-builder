from pathlib import Path

import pytest
import yaml

from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceLog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.tools.candidate_governance import review_candidate
from harness_builder_agent.tools.experience_index import build_experience_index


def _write_asset_candidates(ai: Path, candidate: dict) -> None:
    path = ai / "review" / "asset-candidates.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_maturity_review",
                "candidates": [candidate],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def _guide_candidate(**overrides) -> dict:
    candidate = {
        "id": "guide-project-context-scope",
        "kind": "guide",
        "source_candidate_id": "maturity-next-step-guides",
        "source_review_decision": "support",
        "suggested_path": ".ai/guides/project-context.md",
        "title": "Scope project context guide",
        "rationale": "Candidate is grounded in maturity evidence.",
        "draft_content": "## Candidate Addition\n\nAdd task loading scope.",
        "evidence_sources": [".ai/maturity-evidence.yaml"],
        "acceptance_checks": ["Benchmark content:guides-quality passes."],
        "risk_level": "medium",
        "review_status": "pending_harness_maintainer_review",
    }
    candidate.update(overrides)
    return candidate


def _workflow_policy_candidate(**overrides) -> dict:
    candidate = {
        "id": "workflow-standard-domain-policy",
        "kind": "workflow_policy",
        "source_candidate_id": "maturity-next-step-workflow",
        "source_review_decision": "support",
        "suggested_path": ".ai/harness-config.yaml",
        "title": "Escalate domain policy changes",
        "rationale": "Domain policy changes should use the standard workflow.",
        "draft_content": "Structured workflow policy patch.",
        "workflow_policy_patch": {
            "schema_version": "1.0",
            "operation": "upsert_routing_rule",
            "target": "workflow_routing.rules",
            "rule": {
                "id": "standard-escalation",
                "selected_workflow": "standard",
                "rationale": "Escalate high-risk and domain policy changes to the standard workflow.",
                "task_type_hints": ["feature", "policy"],
                "triggers": [
                    "unclear_impact_scope",
                    "high_risk_module",
                    "cross_module_design",
                    "security_or_permission",
                    "insufficient_sensor_coverage",
                    "domain_policy_change",
                ],
                "required_guides": [".ai/guides/project-context.md", ".ai/guides/architecture.md"],
                "required_sensors": [".ai/sensors/verification.md"],
                "human_confirmation_required": True,
            },
        },
        "evidence_sources": [".ai/maturity-evidence.yaml"],
        "acceptance_checks": ["Benchmark content:workflow-routing-policy passes."],
        "risk_level": "medium",
        "review_status": "pending_harness_maintainer_review",
    }
    candidate.update(overrides)
    return candidate


def _write_base_harness(ai: Path) -> None:
    ai.mkdir(parents=True, exist_ok=True)
    (ai / "project-inventory.json").write_text(
        '{"schema_version":"1.0","repo_name":"repo","root_path":"/tmp/repo","primary_stack":"java-spring","modules":[],"evidence":[]}',
        encoding="utf-8",
    )
    (ai / "command-catalog.yaml").write_text(
        "schema_version: '1.0'\n"
        "commands:\n"
        "  - id: unit_test\n"
        "    command: mvn test\n"
        "    type: test\n"
        "    gate: hard\n"
        "    source: pom.xml\n"
        "    confidence: high\n",
        encoding="utf-8",
    )
    (ai / "harness-config.yaml").write_text(
        yaml.safe_dump(HarnessConfig.default().model_dump(mode="json"), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    for rel in [
        "guides/project-context.md",
        "guides/architecture.md",
        "guides/coding-rules.md",
        "sensors/verification.md",
        "sensors/test-strategy.md",
    ]:
        path = ai / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n", encoding="utf-8")


def test_review_candidate_applies_markdown_candidate_and_records_governance(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    target = ai / "guides" / "project-context.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Project Context\n\n## 当前项目事实\n\nExisting facts.\n", encoding="utf-8")
    _write_asset_candidates(ai, _guide_candidate())

    output_dir = review_candidate(
        repo,
        candidate_id="guide-project-context-scope",
        decision="applied",
        rationale="Maintainer accepted the guide update.",
        reviewer="harness-maintainer",
    )

    assert output_dir == ai
    updated = target.read_text(encoding="utf-8")
    assert "<!-- harness-builder:candidate-applied id=guide-project-context-scope -->" in updated
    assert "## Applied Candidate: Scope project context guide" in updated
    assert "## Candidate Addition" in updated
    log = CandidateGovernanceLog.model_validate(
        yaml.safe_load((ai / "review" / "candidate-governance.yaml").read_text(encoding="utf-8"))
    )
    assert log.decisions[0].candidate_id == "guide-project-context-scope"
    assert log.decisions[0].decision == "applied"
    assert log.decisions[0].applied_paths == [".ai/guides/project-context.md"]
    markdown = (ai / "review" / "candidate-governance.md").read_text(encoding="utf-8")
    assert "# Candidate Governance" in markdown
    assert "## Decisions" in markdown
    assert "guide-project-context-scope" in markdown
    index = build_experience_index(ai)
    assert index.candidate_governance_decision_count == 1
    source = next(item for item in index.sources if item.kind == "candidate_governance")
    assert source.path == ".ai/review/candidate-governance.yaml"


def test_review_candidate_applies_workflow_policy_patch_and_refreshes_maturity_evidence(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    _write_base_harness(ai)
    _write_asset_candidates(ai, _workflow_policy_candidate())

    output_dir = review_candidate(
        repo,
        candidate_id="workflow-standard-domain-policy",
        decision="applied",
        rationale="Maintainer accepted the routing policy patch.",
        reviewer="harness-maintainer",
    )

    assert output_dir == ai
    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    standard = next(rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation")
    assert "domain_policy_change" in standard.triggers
    evidence = yaml.safe_load((ai / "maturity-evidence.yaml").read_text(encoding="utf-8"))
    evidence_rule = next(rule for rule in evidence["harness_assets"]["workflow_routing_rules"] if rule["id"] == "standard-escalation")
    assert "domain_policy_change" in evidence_rule["triggers"]
    log = CandidateGovernanceLog.model_validate(
        yaml.safe_load((ai / "review" / "candidate-governance.yaml").read_text(encoding="utf-8"))
    )
    assert log.decisions[0].decision == "applied"
    assert log.decisions[0].applied_paths == [".ai/harness-config.yaml"]


def test_review_candidate_rejects_workflow_policy_without_structured_patch(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    _write_base_harness(ai)
    candidate = _workflow_policy_candidate()
    candidate.pop("workflow_policy_patch")
    _write_asset_candidates(ai, candidate)

    with pytest.raises(ValueError, match="workflow_policy_patch is required"):
        review_candidate(
            repo,
            candidate_id="workflow-standard-domain-policy",
            decision="applied",
            rationale="Apply workflow policy.",
            reviewer="harness-maintainer",
        )

    assert not (ai / "review" / "candidate-governance.yaml").exists()


def test_review_candidate_rejects_workflow_policy_with_missing_guide_reference(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    _write_base_harness(ai)
    candidate = _workflow_policy_candidate()
    candidate["workflow_policy_patch"]["rule"]["required_guides"] = [".ai/guides/missing.md"]
    _write_asset_candidates(ai, candidate)

    with pytest.raises(ValueError, match="required guide does not exist"):
        review_candidate(
            repo,
            candidate_id="workflow-standard-domain-policy",
            decision="applied",
            rationale="Apply workflow policy.",
            reviewer="harness-maintainer",
        )

    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    standard = next(rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation")
    assert "domain_policy_change" not in standard.triggers


def test_review_candidate_rejects_standard_escalation_patch_without_required_trigger(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    _write_base_harness(ai)
    candidate = _workflow_policy_candidate()
    candidate["workflow_policy_patch"]["rule"]["triggers"] = ["domain_policy_change"]
    _write_asset_candidates(ai, candidate)

    with pytest.raises(ValueError, match="standard-escalation must keep required triggers"):
        review_candidate(
            repo,
            candidate_id="workflow-standard-domain-policy",
            decision="applied",
            rationale="Apply workflow policy.",
            reviewer="harness-maintainer",
        )


def test_review_candidate_rejects_outside_ai_suggested_path(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    _write_asset_candidates(ai, _guide_candidate(suggested_path="README.md"))

    with pytest.raises(ValueError, match="suggested_path must stay under .ai/"):
        review_candidate(
            repo,
            candidate_id="guide-project-context-scope",
            decision="applied",
            rationale="Invalid path.",
            reviewer="harness-maintainer",
        )
