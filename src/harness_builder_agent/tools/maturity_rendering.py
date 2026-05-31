from __future__ import annotations

from harness_builder_agent.schemas.maturity_report import MaturityReport

DIMENSION_LABELS = {
    "guides": "Guides 上下文",
    "sensors": "Sensors 验证",
    "workflow": "Workflow 执行协议",
    "risk_control": "Risk Control 风险控制",
    "repair_loop": "Repair Loop 修复闭环",
    "observability": "Observability 可观测性",
    "experience": "Experience 经验沉淀",
    "verification_sophistication": "Verification 验证成熟度",
    "governance_auditability": "Governance / Auditability 治理审计",
}


def dimension_label(key: str) -> str:
    label = DIMENSION_LABELS.get(key)
    return f"{label}（`{key}`）" if label else f"`{key}`"


def render_maturity_report_markdown(score: MaturityReport) -> str:
    dimensions = "\n".join(
        f"- {dimension_label(name)}：{level}" for name, level in score.dimension_scores.items()
    )
    evidence = "\n".join(f"- {item}" for item in score.evidence)
    blockers = "\n".join(f"- {item}" for item in score.blocking_reasons)
    next_steps = "\n".join(f"- {item}" for item in score.recommended_next_steps)
    dimension_details = "\n".join(_dimension_detail(name, report) for name, report in score.dimensions.items())
    next_level_requirements = "\n".join(
        f"- {dimension_label(name)}：{requirement}"
        for name, report in score.dimensions.items()
        for requirement in report.next_level_requirements
    )
    return (
        "# 成熟度评估报告\n\n"
        f"整体等级：`{score.overall_level}`\n\n"
        f"下一目标等级：`{score.target_next_level or score.overall_level}`\n\n"
        "## 评分维度\n\n"
        f"{dimensions}\n\n"
        "## 证据\n\n"
        f"{evidence}\n\n"
        "## 阻断原因\n\n"
        f"{blockers}\n\n"
        "## 维度详情\n\n"
        f"{dimension_details}\n\n"
        "## 下一等级要求\n\n"
        f"{next_level_requirements}\n\n"
        "## 推荐下一步\n\n"
        f"{next_steps}\n"
    )


def _dimension_detail(name: str, report) -> str:
    evidence = "；".join(f"{item.source}：{item.summary}" for item in report.evidence) or "无"
    blockers = "；".join(item.reason for item in report.blockers) or "无"
    return f"- {dimension_label(name)}：{report.level}\n  - 证据：{evidence}\n  - 阻断：{blockers}"
