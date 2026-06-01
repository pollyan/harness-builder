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


def _write_weapon_library_candidates(ai: Path) -> None:
    (ai / "experience").mkdir(parents=True, exist_ok=True)
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
                        "title": "支付风险 Guide",
                        "rationale": "支付模块需要额外上下文。",
                        "evidence": ["src/payments/CheckoutService.java"],
                        "human_confirmation_required": True,
                        "maturity_dimensions": ["guides", "risk_control"],
                        "maturity_impact_summary": "补齐 Guides 上下文、Risk Control 风险控制。",
                        "next_stage_contribution": "把风险区域留给 Maintainer 审查。",
                        "review_boundary": "review_only_no_formal_asset_change",
                    },
                    {
                        "id": "llm-sensor-command-001",
                        "candidate_type": "sensor",
                        "status": "confirmed",
                        "title": "测试命令 Sensor",
                        "rationale": "已有验证命令。",
                        "evidence": ["pom.xml"],
                        "human_confirmation_required": False,
                        "maturity_dimensions": ["sensors", "verification_sophistication"],
                        "maturity_impact_summary": "补齐 Sensors 验证。",
                        "next_stage_contribution": "保留验证审查线索。",
                        "review_boundary": "review_only_no_formal_asset_change",
                    },
                ],
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


def test_existing_harness_experience_signals_include_initial_candidate_maturity_impact(tmp_path: Path):
    ai = tmp_path / ".ai"
    (ai / "experience").mkdir(parents=True)
    (ai / "experience" / "experience-index.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "experience_files": {},
                "pending_improvement_count": 0,
                "asset_candidate_count": 0,
                "candidate_governance_decision_count": 0,
                "maturity_review_count": 0,
                "workflow_recommendation_count": 0,
                "runtime_task_run_count": 0,
                "sources": [],
                "warnings": [],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    _write_weapon_library_candidates(ai)

    lines = experience_status_lines(ai)

    assert "weapon_library_candidates=2" in lines
    assert "weapon_library_candidates_pending=1" in lines
    assert "weapon_candidate_maturity_dimensions=guides,risk_control" in lines
    assert (
        "weapon_candidate_top=llm-guide-risk-001 "
        "type=guide dimensions=guides,risk_control "
        "boundary=review_only_no_formal_asset_change"
    ) in lines
