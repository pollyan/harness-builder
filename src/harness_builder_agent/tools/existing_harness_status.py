from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.human_confirmation import Questionnaire
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.existing_harness_actions import existing_harness_action_number
from harness_builder_agent.tools.maintenance_triage import MaintenanceAction
from harness_builder_agent.tools.weapon_candidate_status import read_weapon_candidate_status


def render_existing_harness_status_overview_lines(
    ai: Path,
    config: HarnessConfig,
    score: MaturityReport | None,
    actions: list[MaintenanceAction],
) -> list[str]:
    lines = [
        _maturity_overview(score),
        _benchmark_overview(ai),
        _workflow_routing_overview(config),
        _experience_review_overview(ai),
    ]
    if actions:
        lines.append(_top_action_overview(actions[0]))
    return lines


def _maturity_overview(score: MaturityReport | None) -> str:
    if score is None:
        return "成熟度：未发现 `.ai/maturity-score.yaml`；建议先运行菜单 `2` 的 `assess` 刷新状态。"
    return f"成熟度：当前 {score.overall_level}，下一目标 {score.target_next_level or score.overall_level}。"


def _benchmark_overview(ai: Path) -> str:
    path = ai / "benchmark-report.yaml"
    if not path.exists():
        return "质量门禁：尚未运行 benchmark；建议先运行菜单 `4` 的 `benchmark` 建立质量基线。"
    report = BenchmarkReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    failed_checks = sum(1 for check in report.checks if not check.passed)
    if failed_checks:
        return f"质量门禁：未通过，failed checks={failed_checks}；先查看 `.ai/benchmark-report.yaml`。"
    return f"质量门禁：已通过，quality={report.quality_status}。"


def _workflow_routing_overview(config: HarnessConfig) -> str:
    standard = next((rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation"), None)
    if standard is None:
        return "Workflow 路由：缺少 standard-escalation；高风险任务升级规则需要复核。"
    risk_trigger_count = sum(1 for trigger in standard.triggers if trigger.startswith("risk_area:"))
    missing_hard_gate = "present" if "missing_hard_gate" in standard.triggers else "absent"
    return (
        f"Workflow 路由：default=`{config.workflow_routing.default_workflow}`，"
        f"standard escalation 已启用，risk triggers={risk_trigger_count}，"
        f"missing_hard_gate={missing_hard_gate}。"
    )


def _experience_review_overview(ai: Path) -> str:
    path = ai / "experience" / "experience-index.yaml"
    if not path.exists():
        return "Experience / review：experience-index 缺失；建议运行 `assess` 或 `improve` 刷新维护证据。"

    index = ExperienceIndex.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    pending_asset_candidates = max(index.asset_candidate_count - index.candidate_governance_decision_count, 0)
    weapon_candidates = read_weapon_candidate_status(ai)
    human_input_pending = _human_input_pending_count(ai)
    parts: list[str] = []
    if pending_asset_candidates:
        parts.append(f"{pending_asset_candidates} 个 asset candidates 待治理")
    if weapon_candidates and weapon_candidates.pending_count:
        parts.append(f"{weapon_candidates.pending_count} 个初始 LLM Guide/Sensor 候选待确认")
    if index.pending_improvement_count:
        parts.append(f"{index.pending_improvement_count} 个 pending improvement")
    if index.workflow_recommendation_count:
        parts.append(f"{index.workflow_recommendation_count} 条 workflow recommendation")
    if human_input_pending:
        parts.append(f"human-input 待确认 {human_input_pending} 项")
    if index.runtime_task_run_count:
        parts.append(f"runtime task-run 证据 {index.runtime_task_run_count} 条")
    if not parts:
        return "Experience / review：暂无待治理候选或 pending improvement；可按任务运行 `recommend-workflow` 收集路由证据。"
    return f"Experience / review：{'；'.join(parts)}。"


def _human_input_pending_count(ai: Path) -> int:
    questionnaire_path = ai / "questionnaire.yaml"
    if not questionnaire_path.exists():
        return 0
    questionnaire = Questionnaire.model_validate(yaml.safe_load(questionnaire_path.read_text(encoding="utf-8")) or {})
    count = 0
    for question in questionnaire.questions:
        if question.response_status != "reviewed_resolved_by_harness_maintainer":
            count += 1
    return count


def _top_action_overview(action: MaintenanceAction) -> str:
    number = existing_harness_action_number(action.next_action)
    count = f"，count={action.count}" if action.count is not None else ""
    detail = f"，detail={action.detail}" if action.detail else ""
    if number is None:
        return (
            f"优先动作：`{action.next_action}` 暂无维护菜单编号；"
            f"请用专家命令处理 reason={action.reason}，source={action.source}{count}{detail}。"
        )
    return (
        f"优先动作：输入 `{number}` 运行 `{action.next_action}`"
        f"（reason={action.reason}，source={action.source}{count}{detail}）。"
    )
