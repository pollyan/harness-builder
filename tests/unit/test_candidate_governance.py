from pathlib import Path

import pytest
import yaml

from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceLog
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


def test_review_candidate_rejects_workflow_policy_apply_without_mutating_config(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    config = ai / "harness-config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("workflows: {}\n", encoding="utf-8")
    _write_asset_candidates(
        ai,
        _guide_candidate(
            id="workflow-routing-policy-review",
            kind="workflow_policy",
            suggested_path=".ai/harness-config.yaml",
            title="Review workflow routing policy",
            draft_content="workflow_routing:\n  rules: []",
        ),
    )

    with pytest.raises(ValueError, match="applied only supports guide or sensor Markdown candidates"):
        review_candidate(
            repo,
            candidate_id="workflow-routing-policy-review",
            decision="applied",
            rationale="Apply workflow policy.",
            reviewer="harness-maintainer",
        )

    assert config.read_text(encoding="utf-8") == "workflows: {}\n"
    assert not (ai / "review" / "candidate-governance.yaml").exists()


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
