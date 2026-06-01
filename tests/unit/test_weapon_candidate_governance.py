from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from harness_builder_agent.schemas.weapon_candidate_governance import WeaponCandidateGovernanceLog
from harness_builder_agent.tools.weapon_candidate_governance import review_weapon_candidate


def _write_report(ai: Path) -> None:
    (ai / "experience").mkdir(parents=True, exist_ok=True)
    (ai / "review").mkdir(parents=True, exist_ok=True)
    (ai / "experience" / "weapon-library-candidates.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_scan_proposal",
                "candidates": [
                    {
                        "id": "llm-guide-risk-001",
                        "candidate_type": "guide",
                        "status": "candidate",
                        "title": "风险区域候选规则",
                        "rationale": "支付模块需要额外规则。",
                        "evidence": ["src/payments/CheckoutService.java"],
                        "source": "llm_scan_proposal",
                        "human_confirmation_required": True,
                        "maturity_dimensions": ["guides", "risk_control"],
                        "maturity_impact_summary": "补齐 Guides 上下文、Risk Control 风险控制。",
                        "next_stage_contribution": "把风险区域留给 Maintainer 审查。",
                        "review_boundary": "review_only_no_formal_asset_change",
                    },
                    {
                        "id": "llm-sensor-command-001",
                        "candidate_type": "sensor",
                        "status": "candidate",
                        "title": "验证命令候选",
                        "rationale": "需要确认测试命令。",
                        "evidence": ["mvn test", "pom.xml"],
                        "source": "llm_scan_proposal",
                        "human_confirmation_required": True,
                        "maturity_dimensions": ["sensors", "verification_sophistication"],
                        "maturity_impact_summary": "补齐 Sensors 验证。",
                        "next_stage_contribution": "保留验证审查线索。",
                        "review_boundary": "review_only_no_formal_asset_change",
                    },
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def test_review_weapon_candidate_records_accepted_decision_and_refreshes_markdown(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    ai.mkdir(parents=True)
    _write_report(ai)

    output_dir = review_weapon_candidate(
        repo,
        candidate_id="llm-guide-risk-001",
        decision="accepted",
        rationale="风险规则已经人工确认。",
        reviewer="alice",
    )

    assert output_dir == ai
    report = yaml.safe_load((ai / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in report["candidates"]}
    assert by_id["llm-guide-risk-001"]["status"] == "confirmed"
    assert by_id["llm-guide-risk-001"]["human_confirmation_required"] is False
    assert by_id["llm-guide-risk-001"]["decision_notes"] == "风险规则已经人工确认。"
    assert by_id["llm-sensor-command-001"]["status"] == "candidate"

    governance = WeaponCandidateGovernanceLog.model_validate(
        yaml.safe_load((ai / "review" / "weapon-candidate-governance.yaml").read_text(encoding="utf-8"))
    )
    latest = governance.decisions[-1]
    assert latest.candidate_id == "llm-guide-risk-001"
    assert latest.candidate_type == "guide"
    assert latest.decision == "accepted"
    assert latest.previous_status == "candidate"
    assert latest.new_status == "confirmed"
    assert latest.maturity_dimensions == ["guides", "risk_control"]

    summary = (ai / "review" / "llm-enhancement-candidates.md").read_text(encoding="utf-8")
    guides = (ai / "review" / "candidate-guides.md").read_text(encoding="utf-8")
    assert "llm-guide-risk-001" in summary
    assert "status=`confirmed`" in summary
    assert "status=`confirmed`" in guides
    governance_markdown = (ai / "review" / "weapon-candidate-governance.md").read_text(encoding="utf-8")
    assert "## Review Boundary" in governance_markdown
    assert "review_only_no_formal_asset_change" in governance_markdown


@pytest.mark.parametrize(
    ("decision", "expected_status", "expected_required"),
    [
        ("rejected", "rejected", False),
        ("kept", "candidate", True),
    ],
)
def test_review_weapon_candidate_records_rejected_or_kept(tmp_path: Path, decision: str, expected_status: str, expected_required: bool):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    ai.mkdir(parents=True)
    _write_report(ai)

    review_weapon_candidate(
        repo,
        candidate_id="llm-sensor-command-001",
        decision=decision,
        rationale=f"{decision} by maintainer.",
        reviewer="alice",
    )

    report = yaml.safe_load((ai / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    candidate = next(item for item in report["candidates"] if item["id"] == "llm-sensor-command-001")
    assert candidate["status"] == expected_status
    assert candidate["human_confirmation_required"] is expected_required


def test_review_weapon_candidate_fails_explicitly_for_invalid_inputs(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    ai.mkdir(parents=True)
    _write_report(ai)

    with pytest.raises(ValueError, match="rationale is required"):
        review_weapon_candidate(repo, "llm-guide-risk-001", "accepted", "", "alice")
    with pytest.raises(ValueError, match="Unsupported weapon candidate governance decision"):
        review_weapon_candidate(repo, "llm-guide-risk-001", "applied", "No.", "alice")
    with pytest.raises(ValueError, match="unknown weapon candidate id"):
        review_weapon_candidate(repo, "missing", "accepted", "No.", "alice")

    (ai / "experience" / "weapon-library-candidates.yaml").unlink()
    with pytest.raises(FileNotFoundError, match="missing .ai/experience/weapon-library-candidates.yaml"):
        review_weapon_candidate(repo, "llm-guide-risk-001", "accepted", "No.", "alice")
