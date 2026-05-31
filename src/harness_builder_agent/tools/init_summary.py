from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.maturity_report import MaturityReport


def write_init_summary(ai: Path, score: MaturityReport) -> Path:
    path = ai / "init-summary.md"
    path.write_text(build_init_summary_markdown(score, ai=ai), encoding="utf-8")
    return path


def build_init_summary_markdown(score: MaturityReport, ai: Path | None = None) -> str:
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
        "## Benchmark 健康度\n\n"
        f"{_benchmark_readiness(ai)}\n\n"
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
        "Benchmark 健康度：\n"
        f"{_benchmark_readiness(ai)}\n\n"
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


def _benchmark_readiness(ai: Path | None) -> str:
    benchmark_command = "harness-builder-agent benchmark --repo <repo>"
    if ai is not None:
        benchmark_command = f"harness-builder-agent benchmark --repo {ai.parent}"
        report_path = ai / "benchmark-report.yaml"
        if report_path.exists():
            report = BenchmarkReport.model_validate(yaml.safe_load(report_path.read_text(encoding="utf-8")))
            failed_checks = sum(1 for check in report.checks if not check.passed)
            return "\n".join(
                [
                    f"- benchmark_status={report.status}",
                    f"- quality_status={report.quality_status}",
                    f"- failed_checks={failed_checks}",
                    "- source=.ai/benchmark-report.yaml",
                    "- status 表示硬验收结果，quality_status 表示质量评分结果。",
                ]
            )

    return "\n".join(
        [
            "- benchmark_status=not_run",
            "- quality_status=not_available",
            f"- next_command=`{benchmark_command}`",
            "- status 表示硬验收结果，quality_status 表示质量评分结果。",
            "- 初次 init 生成资产不等同于 benchmark passed; not equivalent to benchmark passed.",
        ]
    )
