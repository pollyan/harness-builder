from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from harness_builder_agent.schemas.human_confirmation import Questionnaire
from harness_builder_agent.schemas.human_input_governance import HumanInputGovernanceLog
from harness_builder_agent.tools.human_input_governance import review_human_input


def _write_human_input_fixture(ai: Path, *, interaction_type: str = "scan_followup_confirmation") -> None:
    ai.mkdir(parents=True)
    (ai / "context-inputs.yaml").write_text("schema_version: '1.0'\ncontexts: []\n", encoding="utf-8")
    (ai / "interaction-decisions.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "mode": "interactive",
                "repo": {"path": str(ai.parent), "confirmed": True},
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (ai / "questionnaire.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "questions": [
                    {
                        "interaction_type": interaction_type,
                        "interaction_id": "confirm:scan-followup:test-evidence",
                        "question": "真实测试入口是什么？",
                        "options": ["补充或修正相关信息"],
                        "confidence": "low",
                        "reason": "缺少测试 evidence。",
                        "response_status": "partially_addressed_by_current_scan_supplement",
                        "response_sources": ["command=unit_test:mvn test"],
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (ai / "human-input-needed.md").write_text("# Human Input Needed\n\n## 处理方式\n", encoding="utf-8")


def test_review_human_input_marks_scan_followup_resolved_and_writes_governance(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    _write_human_input_fixture(ai)

    output_dir = review_human_input(
        repo,
        "confirm:scan-followup:test-evidence",
        "resolved",
        "Maintainer verified mvn test is the real gate.",
        reviewer="maintainer",
    )

    assert output_dir == ai
    questionnaire = Questionnaire.model_validate(yaml.safe_load((ai / "questionnaire.yaml").read_text(encoding="utf-8")))
    question = questionnaire.questions[0]
    assert question.response_status == "reviewed_resolved_by_harness_maintainer"
    assert question.response_sources == ["command=unit_test:mvn test"]
    markdown = (ai / "human-input-needed.md").read_text(encoding="utf-8")
    assert "response_status=reviewed_resolved_by_harness_maintainer" in markdown
    assert "已由 Harness Maintainer 标记为 resolved" in markdown
    log = HumanInputGovernanceLog.model_validate(
        yaml.safe_load((ai / "review" / "human-input-governance.yaml").read_text(encoding="utf-8"))
    )
    assert log.decisions[0].interaction_id == "confirm:scan-followup:test-evidence"
    assert log.decisions[0].decision == "resolved"
    assert log.decisions[0].previous_response_status == "partially_addressed_by_current_scan_supplement"
    assert log.decisions[0].new_response_status == "reviewed_resolved_by_harness_maintainer"
    governance_md = (ai / "review" / "human-input-governance.md").read_text(encoding="utf-8")
    assert "Maintainer verified mvn test is the real gate." in governance_md


def test_review_human_input_reopens_resolved_followup_to_partial_when_sources_remain(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    _write_human_input_fixture(ai)
    review_human_input(repo, "confirm:scan-followup:test-evidence", "resolved", "Reviewed.", reviewer="maintainer")

    review_human_input(repo, "confirm:scan-followup:test-evidence", "reopened", "Need another review.", reviewer="maintainer")

    questionnaire = Questionnaire.model_validate(yaml.safe_load((ai / "questionnaire.yaml").read_text(encoding="utf-8")))
    assert questionnaire.questions[0].response_status == "partially_addressed_by_current_scan_supplement"
    log = HumanInputGovernanceLog.model_validate(
        yaml.safe_load((ai / "review" / "human-input-governance.yaml").read_text(encoding="utf-8"))
    )
    assert [item.decision for item in log.decisions] == ["resolved", "reopened"]


def test_review_human_input_rejects_invalid_targets(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    _write_human_input_fixture(ai, interaction_type="context_confirmation")

    with pytest.raises(ValueError, match="only supports scan_followup_confirmation"):
        review_human_input(repo, "confirm:scan-followup:test-evidence", "resolved", "Reviewed.")

    with pytest.raises(ValueError, match="rationale is required"):
        review_human_input(repo, "confirm:scan-followup:test-evidence", "resolved", "")

    with pytest.raises(ValueError, match="unknown human input interaction id"):
        review_human_input(repo, "confirm:missing", "resolved", "Reviewed.")
