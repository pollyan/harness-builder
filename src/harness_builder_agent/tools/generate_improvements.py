from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidate, ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.assess_maturity import assess_maturity


def generate_improvements(repo: Path) -> Path:
    root = repo.resolve()
    ai = root / ".ai"
    if not (ai / "maturity-score.yaml").exists():
        assess_maturity(root)

    score = MaturityReport.model_validate(yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8")))
    candidates = ImprovementCandidateReport(candidates=_candidates(score))
    _write_yaml(ai / "improvement-candidates.yaml", candidates.model_dump(mode="json"))
    _write_evolution_plan(ai / "evolution-plan.md", candidates)
    _write_pending_improvements(ai / "experience" / "pending-improvements.md", candidates)
    return ai


def _candidates(score: MaturityReport) -> list[ImprovementCandidate]:
    candidates: list[ImprovementCandidate] = []
    if score.dimension_scores.get("guides") in {"L0", "L1", "L2"}:
        candidates.append(
            ImprovementCandidate(
                id="guide-confirm-candidates",
                candidate_type="guide_update",
                suggested_target=".ai/guides/coding-rules.md",
                rationale="当前 Guides 仍是候选态，需要维护者确认后才能作为正式规则使用。",
                evidence=score.evidence,
                priority="high",
            )
        )
    if score.dimension_scores.get("sensors") != "L3":
        candidates.append(
            ImprovementCandidate(
                id="sensor-add-quality-gates",
                candidate_type="sensor_update",
                suggested_target=".ai/sensors/verification.md",
                rationale="当前 Sensor 主要来自构建和测试命令，仍需补齐 lint、typecheck 或安全检查。",
                evidence=score.blocking_reasons,
                priority="high",
            )
        )
    candidates.append(
        ImprovementCandidate(
            id="workflow-bind-sensor-failures",
            candidate_type="workflow_policy_update",
            suggested_target=".ai/skills/bugfix/SKILL.md",
            rationale="Sensor 失败后的修复循环仍是 POC 策略，需要继续固化到 Workflow Skill。",
            evidence=score.recommended_next_steps,
            priority="medium",
        )
    )
    return candidates


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_evolution_plan(path: Path, report: ImprovementCandidateReport) -> None:
    lines = "\n".join(f"- `{item.id}`：{item.rationale}（目标：`{item.suggested_target}`）" for item in report.candidates)
    path.write_text(
        "# 演进计划\n\n"
        "## 优先级路线图\n\n"
        f"{lines}\n\n"
        "## 生效规则\n\n"
        "- 这些候选项只进入待确认状态，不自动修改正式 Guides / Sensors / Workflow。\n",
        encoding="utf-8",
    )


def _write_pending_improvements(path: Path, report: ImprovementCandidateReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = "\n".join(f"- `{item.id}`：{item.rationale}" for item in report.candidates)
    path.write_text(
        "# Pending Improvements\n\n"
        "## 待确认改进候选\n\n"
        f"{lines}\n",
        encoding="utf-8",
    )
