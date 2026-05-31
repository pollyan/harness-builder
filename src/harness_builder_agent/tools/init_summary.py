from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.maturity_report import MaturityReport


def build_init_summary_markdown(score: MaturityReport) -> str:
    blockers = _bullet_lines(score.blocking_reasons[:5])
    next_steps = _bullet_lines(score.recommended_next_steps[:5])
    dimensions = "\n".join(
        f"- {name}: `{level}`"
        for name, level in sorted(score.dimension_scores.items())
    ) or "- 暂无维度评分。"
    return (
        "# Init Summary\n\n"
        "## 当前成熟度\n\n"
        f"- 当前等级：`{score.overall_level}`\n"
        f"- 下一目标等级：`{score.target_next_level or score.overall_level}`\n\n"
        "### 维度概览\n\n"
        f"{dimensions}\n\n"
        "## 主要阻断项\n\n"
        f"{blockers}\n\n"
        "## 建议下一步\n\n"
        f"{next_steps}\n\n"
        "## 推荐入口文件\n\n"
        "- `.ai/maturity-report.md`：查看完整成熟度评分、证据和下一等级要求。\n"
        "- `.ai/human-input-needed.md`：补充团队规则、风险边界和待确认项。\n"
        "- `.ai/sensors/verification.md`：确认验证命令和 hard gate 策略。\n"
        "- `.ai/evolution-plan.md`：查看第一版 Harness 的后续演进建议。\n\n"
        "## 本次未执行的事项\n\n"
        "- `init` 不默认执行 `self-improve`、LLM maturity review 或深度 asset candidate generation。\n"
        "- `init` 不执行宿主 AI Coding Runtime，不生成 `.ai/task-runs`。\n"
        "- 高风险或低置信度内容仍应通过 candidate / review-only 流程处理。\n"
    )


def render_init_completion_message(ai: Path) -> str:
    score = MaturityReport.model_validate(
        yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8"))
    )
    blockers = _numbered_lines(score.blocking_reasons[:3])
    next_steps = _numbered_lines(score.recommended_next_steps[:3])
    return (
        f"Harness assets are available in {ai}\n\n"
        f"当前成熟度：{score.overall_level}"
        f"{f' -> {score.target_next_level}' if score.target_next_level else ''}\n\n"
        "主要阻断项：\n"
        f"{blockers}\n\n"
        "建议下一步：\n"
        f"{next_steps}\n\n"
        "推荐入口：\n"
        "- `.ai/init-summary.md`\n"
        "- `.ai/maturity-report.md`\n"
        "- `.ai/human-input-needed.md`"
    )


def _bullet_lines(items: list[str]) -> str:
    if not items:
        return "- 暂无明确阻断项。"
    return "\n".join(f"- {item}" for item in items)


def _numbered_lines(items: list[str]) -> str:
    if not items:
        return "1. 暂无明确事项。"
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))
