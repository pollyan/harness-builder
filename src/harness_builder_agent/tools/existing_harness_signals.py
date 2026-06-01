from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.human_confirmation import Questionnaire
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.schemas.workflow_recommendation_history import WorkflowRecommendationHistory
from harness_builder_agent.tools.human_confirmation import SCAN_CONFIRMATION_TYPES


def read_benchmark_status(ai: Path) -> str:
    path = ai / "benchmark-report.yaml"
    if not path.exists():
        return "未发现 benchmark-report.yaml"
    report = BenchmarkReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    return f"{report.status}，quality={report.quality_status}"


def benchmark_signal_lines(ai: Path) -> list[str]:
    path = ai / "benchmark-report.yaml"
    if not path.exists():
        return ["benchmark_failed_checks=not_available"]
    report = BenchmarkReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    failed_checks = [check for check in report.checks if not check.passed]
    lines = [f"benchmark_failed_checks={len(failed_checks)}"]
    lines.extend(f"benchmark_failed_check={check.id}" for check in failed_checks[:3])
    lines.extend(
        f"benchmark_failed_check_detail={check.id}|{_benchmark_failed_check_label(check.id)}"
        for check in failed_checks[:3]
    )
    lines.extend(
        f"benchmark_failed_check_error={check.id}|{detail}"
        for check in failed_checks[:3]
        if (detail := _benchmark_check_detail(check))
    )
    return lines


def workflow_routing_status_lines(config: HarnessConfig) -> list[str]:
    rules = config.workflow_routing.rules
    lines = [
        f"routing_default={config.workflow_routing.default_workflow}",
        f"routing_rule_count={len(rules)}",
    ]
    standard_rules = [rule for rule in rules if rule.id == "standard-escalation"]
    if not standard_rules:
        return [*lines, "standard_escalation=missing"]

    standard = standard_rules[0]
    risk_triggers = [trigger for trigger in standard.triggers if trigger.startswith("risk_area:")]
    lines.extend(
        [
            "standard_escalation=present",
            f"standard_human_confirmation={str(standard.human_confirmation_required).lower()}",
            f"standard_risk_triggers={len(risk_triggers)}",
        ]
    )
    lines.extend(f"risk_trigger={trigger}" for trigger in risk_triggers[:3])
    lines.append(f"missing_hard_gate_trigger={'present' if 'missing_hard_gate' in standard.triggers else 'absent'}")
    return lines


def experience_status_lines(ai: Path) -> list[str]:
    path = ai / "experience" / "experience-index.yaml"
    if not path.exists():
        return [
            "experience_index=missing",
            *_workflow_recommendation_status_lines(ai),
            f"self_improve_package={_self_improve_package_status(ai)}",
            *_human_input_needed_status_lines(ai),
            f"schema_content_failed_checks={_benchmark_schema_content_failed_count(ai)}",
        ]
    index = ExperienceIndex.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    return [
        "experience_index=present",
        f"pending_improvements={index.pending_improvement_count}",
        f"asset_candidates={index.asset_candidate_count}",
        f"candidate_governance={index.candidate_governance_decision_count}",
        f"maturity_reviews={index.maturity_review_count}",
        f"workflow_recommendations={index.workflow_recommendation_count}",
        *_workflow_recommendation_status_lines(ai),
        f"runtime_task_runs={index.runtime_task_run_count}",
        f"self_improve_package={_self_improve_package_status(ai)}",
        *_human_input_needed_status_lines(ai),
        f"schema_content_failed_checks={_benchmark_schema_content_failed_count(ai)}",
    ]


def human_input_needed_status_lines(ai: Path) -> list[str]:
    return _human_input_needed_status_lines(ai)


def _benchmark_failed_check_label(check_id: str) -> str:
    labels = {
        "content:risk-context-consistency": "风险上下文在 Guide / Sensor / Routing 之间不一致",
        "content:init-summary-workflow-routing": "init-summary 的 Workflow 与路由摘要缺失或与 harness-config 漂移",
        "content:hard-gate-command-evidence": "hard gate 命令证据不足",
        "content:workflow-routing-policy": "workflow routing policy 缺少必要升级规则",
        "content:guides-quality": "project-context Guide 缺少必需章节或仓库特异性",
        "content:scan-report": "scan-report 缺少扫描证据审计细节",
        "content:init-summary": "init-summary 缺少扫描证据审计摘要",
        "content:project-context-evidence-context": "project-context Guide 缺少 inventory evidence 或 LLM 证据扩展摘要",
        "content:sensors-quality": "verification Sensor 缺少必需章节或验证风险说明",
    }
    if check_id in labels:
        return labels[check_id]
    if check_id.startswith("schema:"):
        return "机器消费产物 schema 校验失败"
    return "查看 benchmark-report.yaml 获取完整失败详情"


def _benchmark_check_detail(check) -> str:
    details: list[str] = []
    if check.error:
        details.append(check.error)
    details.extend(str(error) for error in check.errors[:3])
    details.extend(str(item) for item in check.missing[:3])
    details.extend(_weak_command_details(check.weak_commands[:3]))
    if len(check.errors) > 3:
        details.append(f"还有 {len(check.errors) - 3} 项错误")
    if len(check.missing) > 3:
        details.append(f"还有 {len(check.missing) - 3} 项缺失")
    if len(check.weak_commands) > 3:
        details.append(f"还有 {len(check.weak_commands) - 3} 个弱命令")
    return "；".join(details)


def _weak_command_details(weak_commands) -> list[str]:
    details: list[str] = []
    for item in weak_commands:
        command_id = str(item.id or "unknown")
        reason = _weak_command_reason(item)
        source = str(item.source or "missing_source")
        details.append(f"{command_id}:{reason}:{source}")
    return details


def _weak_command_reason(item) -> str:
    if item.reason:
        return str(item.reason)
    if not item.source:
        return "missing_source"
    if item.confidence == "low":
        return "low_confidence"
    return "weak_command"


def _workflow_recommendation_status_lines(ai: Path) -> list[str]:
    history_path = ai / "review" / "workflow-routing-recommendations" / "index.yaml"
    if history_path.exists():
        history = WorkflowRecommendationHistory.model_validate(yaml.safe_load(history_path.read_text(encoding="utf-8")) or {})
        latest = next(
            (
                item
                for item in history.recommendations
                if item.recommendation_id == history.latest_recommendation_id
            ),
            None,
        )
        if latest is None:
            return ["latest_workflow_recommendation=none source=.ai/review/workflow-routing-recommendations/index.yaml"]
        return [
            "latest_workflow_recommendation="
            f"{latest.recommendation_id} "
            f"task={latest.task_id} "
            f"workflow={latest.recommended_workflow} "
            f"risk={latest.risk_level} "
            f"status={latest.review_status} "
            "source=.ai/review/workflow-routing-recommendations/index.yaml"
        ]

    latest_path = ai / "review" / "workflow-routing-recommendation.yaml"
    if latest_path.exists():
        recommendation = WorkflowRecommendationReport.model_validate(
            yaml.safe_load(latest_path.read_text(encoding="utf-8")) or {}
        )
        return [
            "latest_workflow_recommendation=legacy_latest "
            f"task={recommendation.task_id} "
            f"workflow={recommendation.recommended_workflow} "
            f"risk={recommendation.risk_level} "
            f"status={recommendation.review_status} "
            "source=.ai/review/workflow-routing-recommendation.yaml"
        ]

    return []


def _self_improve_package_status(ai: Path) -> str:
    yaml_path = ai / "review" / "self-improve-package.yaml"
    markdown_path = ai / "review" / "self-improve-package.md"
    if not yaml_path.exists() and not markdown_path.exists():
        return "missing"
    if not yaml_path.exists() or not markdown_path.exists():
        return "incomplete"
    manifest = SelfImprovePackageManifest.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
    return (
        "present"
        f"(maturity_reviews={manifest.candidate_counts.maturity_reviews},"
        f"asset_candidates={manifest.candidate_counts.asset_candidates})"
    )


def _human_input_needed_status_lines(ai: Path) -> list[str]:
    if not (ai / "human-input-needed.md").exists():
        return ["human_input_needed=missing"]
    questionnaire_path = ai / "questionnaire.yaml"
    if not questionnaire_path.exists():
        return [
            "human_input_needed=present",
            "human_input_questionnaire=missing",
            "human_input_action_entry=.ai/human-input-needed.md#处理方式",
        ]
    questionnaire = Questionnaire.model_validate(yaml.safe_load(questionnaire_path.read_text(encoding="utf-8")) or {})
    questions = questionnaire.questions
    scan_confirmation_count = sum(1 for question in questions if question.interaction_type in SCAN_CONFIRMATION_TYPES)
    scan_followups = [question for question in questions if question.interaction_type == "scan_followup_confirmation"]
    scan_followup_partial_count = sum(
        1
        for question in scan_followups
        if question.response_status == "partially_addressed_by_current_scan_supplement"
    )
    scan_followup_resolved_count = sum(
        1
        for question in scan_followups
        if question.response_status == "reviewed_resolved_by_harness_maintainer"
    )
    scan_followup_unaddressed_count = sum(1 for question in scan_followups if question.response_status == "unaddressed")
    lines = [
        "human_input_needed=present",
        "human_input_questionnaire=present",
        f"human_input_confirmations={len(questions)}",
        f"human_input_scan_confirmations={scan_confirmation_count}",
    ]
    if scan_followups:
        lines.extend(
            [
                f"human_input_scan_followups_resolved={scan_followup_resolved_count}",
                f"human_input_scan_followups_partially_addressed={scan_followup_partial_count}",
                f"human_input_scan_followups_unaddressed={scan_followup_unaddressed_count}",
            ]
        )
    for question in questions[:3]:
        lines.append(f"human_input_first={question.interaction_id}")
    omitted = len(questions) - 3
    if omitted > 0:
        lines.append(f"human_input_omitted={omitted}")
    lines.append("human_input_action_entry=.ai/human-input-needed.md#处理方式")
    return lines


def _benchmark_schema_content_failed_count(ai: Path) -> str:
    path = ai / "benchmark-report.yaml"
    if not path.exists():
        return "not_available"
    report = BenchmarkReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    failed = [
        check
        for check in report.checks
        if not check.passed and (check.id.startswith("schema:") or check.id.startswith("content:"))
    ]
    return str(len(failed))
