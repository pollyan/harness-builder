from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.tools.existing_harness_signals import (
    benchmark_signal_lines,
    experience_status_lines,
    read_benchmark_status,
    workflow_routing_status_lines,
)


def _write_benchmark_report(ai: Path) -> None:
    (ai / "benchmark-report.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "profile": "java-spring",
                "status": "failed",
                "quality_status": "degraded",
                "checks": [
                    {
                        "id": "content:hard-gate-command-evidence",
                        "passed": False,
                        "weak_commands": [
                            {
                                "id": "unit_test",
                                "command": "mvn test",
                                "source": "",
                                "confidence": "low",
                                "reason": "missing_source",
                            }
                        ],
                    },
                    {"id": "schema:project-inventory", "passed": True},
                ],
                "quality_scores": {},
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_existing_harness_benchmark_signals_explain_missing_and_failed_report(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()

    assert read_benchmark_status(ai) == "未发现 benchmark-report.yaml"
    assert benchmark_signal_lines(ai) == ["benchmark_failed_checks=not_available"]

    _write_benchmark_report(ai)

    assert read_benchmark_status(ai) == "failed，quality=degraded"
    lines = benchmark_signal_lines(ai)
    assert "benchmark_failed_checks=1" in lines
    assert "benchmark_failed_check=content:hard-gate-command-evidence" in lines
    assert "benchmark_failed_check_detail=content:hard-gate-command-evidence|hard gate 命令证据不足" in lines
    assert "benchmark_failed_check_error=content:hard-gate-command-evidence|unit_test:missing_source:missing_source" in lines


def test_existing_harness_workflow_routing_signals_include_standard_risks():
    config = HarnessConfig.default()
    standard = next(rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation")
    standard.triggers.extend(["risk_area:src/main/resources/application.yml", "missing_hard_gate"])

    lines = workflow_routing_status_lines(config)

    assert "routing_default=lightweight" in lines
    assert "routing_rule_count=3" in lines
    assert "standard_escalation=present" in lines
    assert "standard_human_confirmation=true" in lines
    assert "missing_hard_gate_trigger=present" in lines
    assert "risk_trigger=risk_area:src/main/resources/application.yml" in lines


def test_existing_harness_experience_signals_include_review_history_and_human_input(tmp_path: Path):
    ai = tmp_path / ".ai"
    (ai / "experience").mkdir(parents=True)
    (ai / "review" / "workflow-routing-recommendations").mkdir(parents=True)
    (ai / "human-input-needed.md").write_text("# Human Input\n", encoding="utf-8")
    (ai / "questionnaire.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "questions": [
                    {
                        "interaction_type": "scan_followup_confirmation",
                        "interaction_id": "confirm:scan-followup:test-evidence",
                        "question": "测试入口是否正确？",
                        "options": ["resolved", "reopened"],
                        "confidence": "medium",
                        "reason": "需要人工复核。",
                        "response_status": "partially_addressed_by_current_scan_supplement",
                    }
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (ai / "experience" / "experience-index.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "experience_files": {},
                "pending_improvement_count": 1,
                "asset_candidate_count": 2,
                "candidate_governance_decision_count": 1,
                "maturity_review_count": 1,
                "workflow_recommendation_count": 1,
                "runtime_task_run_count": 0,
                "sources": [],
                "warnings": [],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (ai / "review" / "workflow-routing-recommendations" / "index.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "latest_recommendation_id": "workflow-rec-1",
                "recommendations": [
                    {
                        "recommendation_id": "workflow-rec-1",
                        "task_id": "task-1",
                        "created_at": "2026-06-01T00:00:00Z",
                        "yaml_path": ".ai/review/workflow-routing-recommendations/workflow-rec-1.yaml",
                        "markdown_path": ".ai/review/workflow-routing-recommendations/workflow-rec-1.md",
                        "recommended_workflow": "standard",
                        "risk_level": "high",
                        "confidence": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    lines = experience_status_lines(ai)

    assert "experience_index=present" in lines
    assert "pending_improvements=1" in lines
    assert "asset_candidates=2" in lines
    assert "candidate_governance=1" in lines
    assert "maturity_reviews=1" in lines
    assert "workflow_recommendations=1" in lines
    assert (
        "latest_workflow_recommendation=workflow-rec-1 "
        "task=task-1 workflow=standard risk=high status=pending_harness_maintainer_review "
        "source=.ai/review/workflow-routing-recommendations/index.yaml"
    ) in lines
    assert "human_input_needed=present" in lines
    assert "human_input_questionnaire=present" in lines
    assert "human_input_scan_followups_partially_addressed=1" in lines
    assert "human_input_action_entry=.ai/human-input-needed.md#处理方式" in lines
