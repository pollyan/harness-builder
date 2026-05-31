from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.interaction_decision import InteractionDecisions
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.human_confirmation import Questionnaire
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory


def write_init_summary(
    ai: Path,
    score: MaturityReport,
    *,
    inventory: ProjectInventory | None = None,
    commands: CommandCatalog | None = None,
    interaction_decisions: InteractionDecisions | None = None,
) -> Path:
    path = ai / "init-summary.md"
    path.write_text(
        build_init_summary_markdown(
            score,
            ai=ai,
            inventory=inventory,
            commands=commands,
            interaction_decisions=interaction_decisions,
        ),
        encoding="utf-8",
    )
    return path


def build_init_summary_markdown(
    score: MaturityReport,
    ai: Path | None = None,
    *,
    inventory: ProjectInventory | None = None,
    commands: CommandCatalog | None = None,
    interaction_decisions: InteractionDecisions | None = None,
) -> str:
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
        "## 本仓库关键事实\n\n"
        f"{_repository_fact_lines(inventory, commands)}\n\n"
        "## 主要阻断项\n\n"
        f"{blockers}\n\n"
        "## 建议下一步\n\n"
        f"{next_steps}\n\n"
        "## 本次吸收的用户补充\n\n"
        f"{_user_supplement_lines(interaction_decisions)}\n\n"
        "## 资产如何补齐缺口\n\n"
        f"{_asset_gap_link_lines(score, inventory, commands, interaction_decisions)}\n\n"
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
    evidence_or_gaps = _completion_evidence_gap_lines(score)
    next_steps = _numbered_lines(score.recommended_next_steps[:3])
    return (
        "== 初始化完成 ==\n"
        f"- 输出目录：{ai}\n"
        "- 本终端摘要是本次 init 的主要交付说明；Markdown 文件用于持久化审查、团队协作和后续 Runtime 上下文。\n\n"
        "本次已生成：\n"
        f"{_generated_asset_summary(ai)}\n\n"
        "当前成熟度：\n"
        f"- 当前等级：{score.overall_level}\n"
        f"- 下一目标：{score.target_next_level or score.overall_level}\n\n"
        "主要证据 / 缺口：\n"
        f"{evidence_or_gaps}\n\n"
        "建议下一步：\n"
        f"{next_steps}\n\n"
        "Benchmark 健康度：\n"
        f"{_benchmark_readiness(ai)}\n\n"
        "优先查看：\n"
        f"{_priority_entry_lines(ai)}\n\n"
        "仍需人工确认：\n"
        f"{_pending_confirmation_lines(ai)}"
    )


def _bullet_lines(items: list[str]) -> str:
    if not items:
        return "- 暂无明确阻断项。"
    return "\n".join(f"- {item}" for item in items)


def _numbered_lines(items: list[str]) -> str:
    if not items:
        return "1. 暂无明确事项。"
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def _completion_evidence_gap_lines(score: MaturityReport) -> str:
    lines: list[str] = []
    for item in score.evidence[:2]:
        lines.append(f"- 证据：{item}")
    for item in score.blocking_reasons[:3]:
        lines.append(f"- 缺口：{item}")
    return "\n".join(lines) or "- 暂无明确证据或缺口；建议先运行 benchmark 做质量验收。"


def _generated_asset_summary(ai: Path) -> str:
    checks = [
        ("项目清单", ai / "project-inventory.json"),
        ("命令目录", ai / "command-catalog.yaml"),
        ("Guides", ai / "guides"),
        ("Sensors", ai / "sensors"),
        ("Workflow Skills", ai / "skills"),
        ("成熟度报告", ai / "maturity-report.md"),
        ("待确认项", ai / "human-input-needed.md"),
        ("生成 trace", ai / "runs"),
    ]
    return "\n".join(
        f"- {label}：{'已生成' if path.exists() else 'missing'}"
        for label, path in checks
    )


def _priority_entry_lines(ai: Path) -> str:
    entries = [
        (".ai/init-summary.md", "完整阅读本次初始化交付、成熟度缺口和未执行边界。"),
        (".ai/maturity-report.md", "查看 L0-L4 评分证据、阻断项和下一等级要求。"),
        (".ai/sensors/verification.md", "确认验证命令、hard gate 和失败处理策略。"),
        (".ai/human-input-needed.md", "处理团队规则、风险边界和候选项的待确认问题。"),
        (".ai/evolution-plan.md", "查看后续 Harness 演进建议。"),
    ]
    return "\n".join(
        f"{index}. `{path}`：{reason}{'' if (ai.parent / path).exists() else '（当前缺失，需检查生成过程）'}"
        for index, (path, reason) in enumerate(entries, start=1)
    )


def _pending_confirmation_lines(ai: Path) -> str:
    path = ai / "questionnaire.yaml"
    if not path.exists():
        return "1. 未找到 `.ai/questionnaire.yaml`；请查看 `.ai/human-input-needed.md`。"
    questionnaire = Questionnaire.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    lines = [
        f"{index}. `{item.interaction_id}`：{item.question}（confidence={item.confidence}）"
        for index, item in enumerate(questionnaire.questions[:3], start=1)
    ]
    if len(questionnaire.questions) > 3:
        lines.append(f"{len(lines) + 1}. 还有 {len(questionnaire.questions) - 3} 个问题，详见 `.ai/human-input-needed.md`。")
    return "\n".join(lines) or "1. 暂无待确认问题。"


def _repository_fact_lines(inventory: ProjectInventory | None, commands: CommandCatalog | None) -> str:
    if inventory is None:
        return "- 当前命令未提供 project inventory 上下文；请查看 `.ai/project-inventory.json`。"
    module_lines = [
        f"- 模块：`{module.get('path')}` ({module.get('kind', 'unknown')})"
        for module in inventory.modules[:8]
    ] or ["- 模块：当前扫描未确认模块边界。"]
    risk_lines = [
        f"- 风险区域：`{path}`：{reason}"
        for path, reason in _risk_areas(inventory)[:8]
    ] or ["- 风险区域：当前扫描未确认具体风险区域。"]
    command_lines = [
        f"- 验证入口：`{command.command}`，gate=`{command.gate}`，source=`{command.source}`"
        for command in (commands.commands if commands else [])[:8]
    ] or ["- 验证入口：当前扫描未确认可执行验证命令。"]
    return "\n".join([f"- 主技术栈：`{inventory.primary_stack}`。", *module_lines, *risk_lines, *command_lines])


def _user_supplement_lines(interaction_decisions: InteractionDecisions | None) -> str:
    if interaction_decisions is None:
        return "- 当前没有 interaction decisions 上下文。"
    lines: list[str] = []
    for note in interaction_decisions.scan_confirmation.notes:
        lines.append(f"- 扫描补充：{note}")
    for item in interaction_decisions.context_confirmation.inline_contexts:
        lines.append(f"- 团队规则：{item}")
    for note in interaction_decisions.workflow_confirmation.notes:
        lines.append(f"- Workflow 补充：{note}")
    if interaction_decisions.workflow_confirmation.shown_workflows:
        lines.append(
            "- 已展示 Workflow："
            + ", ".join(f"`{item}`" for item in interaction_decisions.workflow_confirmation.shown_workflows)
        )
    return "\n".join(lines) or "- 本次未提供人工补充；后续可在维护入口继续补齐团队规则、风险边界和 workflow 约束。"


def _asset_gap_link_lines(
    score: MaturityReport,
    inventory: ProjectInventory | None,
    commands: CommandCatalog | None,
    interaction_decisions: InteractionDecisions | None,
) -> str:
    lines = [
        "- `.ai/guides/project-context.md` 负责承接模块、风险、证据和团队上下文，支撑 Guides 维度从模板化走向仓库特异化。",
        "- `.ai/sensors/verification.md` 负责承接验证入口、缺失能力和风险验证映射，支撑 Sensors 与风险控制维度的初始基线。",
        "- `.ai/init-summary.md` 负责把成熟度阻断项、下一步动作和本次未执行边界集中给 Harness Maintainer。",
    ]
    if commands and commands.commands:
        lines.append(f"- 本次 `{len(commands.commands)}` 个命令进入 Sensor 资产；仍需通过 benchmark 或人工验证确认稳定性。")
    else:
        lines.append("- 当前缺少命令目录证据，验证能力仍是下一轮优先缺口。")
    if inventory and _risk_areas(inventory):
        lines.append("- 风险区域已经进入 Guide/Sensor 叙事，后续可继续绑定 workflow escalation。")
    if interaction_decisions and (
        interaction_decisions.scan_confirmation.notes
        or interaction_decisions.context_confirmation.inline_contexts
        or interaction_decisions.workflow_confirmation.notes
    ):
        lines.append("- 用户补充已经进入正式语义资产和 human-input 记录，后续 maturity/improve 可基于这些事实继续演进。")
    if score.blocking_reasons:
        lines.append(f"- 当前最优先阻断项：{score.blocking_reasons[0]}")
    return "\n".join(lines)


def _risk_areas(inventory: ProjectInventory) -> list[tuple[str, str]]:
    raw_items = inventory.stack_extensions.get("risk_areas", [])
    if not isinstance(raw_items, list):
        return []
    items: list[tuple[str, str]] = []
    for item in raw_items:
        if isinstance(item, dict):
            items.append((str(item.get("path") or "unknown"), str(item.get("reason") or "当前扫描提示需要人工确认。")))
    return items


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
