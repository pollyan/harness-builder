from __future__ import annotations

from pathlib import Path

import typer

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.maturity_model import build_maturity_report
from harness_builder_agent.tools.prewrite_preview import has_existing_partial_harness
from harness_builder_agent.tools.risk_signals import classify_risk_area, high_impact_risk_areas
from harness_builder_agent.tools.scan_repo import ScanProgressEvent
from harness_builder_agent.tools.scan_followup_guidance import (
    scan_followup_answer_guidance_lines as scan_followup_answer_guidance_lines_for_questions,
)
from harness_builder_agent.tools.scan_self_check_actions import scan_self_check_action_hint
from harness_builder_agent.tools.weapon_library import select_weapon_library


SCAN_PROGRESS_LABELS = {
    "collect-evidence": "收集仓库 evidence",
    "plan-evidence-expansion": "请求 LLM 规划补充 evidence",
    "expand-evidence": "读取 LLM 请求的补充 evidence",
    "llm-scan": "请求 LLM 做最终结构化扫描",
    "reconcile-scan": "调和扫描结果",
    "scan-self-check": "请求 LLM 二次自检深度追问",
}


def show_scan_progress_start(repo: Path) -> None:
    typer.echo("\n扫描仓库")
    typer.echo(f"- 目标仓库：{repo}")
    typer.echo("- 正在收集仓库文件、构建配置、CI、测试和文档证据。")
    typer.echo("- 正在识别构建、测试、验证命令、源码入口、模块线索和风险区域。")
    typer.echo("- 正在请求 LLM 做结构化扫描，并校验返回 schema。")
    typer.echo("- 正在调和 LLM 判断与 evidence；这个阶段可能需要一些时间。")


def guided_scan_progress(event: ScanProgressEvent) -> None:
    label = SCAN_PROGRESS_LABELS.get(event.phase, event.message)
    if event.status == "started":
        typer.echo(f"- 当前阶段：{label}")
        return
    typer.echo(f"  已完成：{label}")


def show_scan_progress_completed(inventory: ProjectInventory, commands: CommandCatalog) -> None:
    typer.echo("\n扫描完成")
    typer.echo("- 已完成 evidence 收集、LLM 结构化分析和扫描调和。")
    typer.echo(f"- 初步识别技术栈：{stack_summary_label(inventory)}。")
    typer.echo(f"- 初步识别验证命令数量：{len(commands.commands)}。")


def show_scan_progress_failed(exc: Exception, error_message: str | None = None) -> None:
    reason = error_message if error_message is not None else str(exc)
    typer.echo("\n扫描阶段失败")
    typer.echo(f"- 原因：{type(exc).__name__}: {reason}")
    typer.echo("- 未写入正式 Harness 资产。")
    typer.echo("- 请检查 LLM 配置、网络或扫描错误后重试。")


def show_scan_findings(inventory: ProjectInventory, commands: CommandCatalog) -> None:
    typer.echo("\n扫描发现")
    typer.echo("我先根据仓库文件、构建配置、源码样本和 LLM 结构化分析做了一个初步判断。")
    typer.echo(f"- 主要技术栈：{stack_summary_label(inventory)}")
    if inventory.stacks:
        typer.echo(f"- 技术线索：{', '.join(inventory.stacks)}")

    evidence = inventory.evidence or inventory.configs or inventory.documents
    typer.echo("\n判断依据")
    for item in evidence[:6]:
        typer.echo(f"- `{item.get('path', 'unknown')}`：{item.get('reason') or item.get('kind') or '扫描证据'}")
    if not evidence:
        typer.echo("- 暂时没有足够直接证据，建议人工补充。")

    typer.echo("\n识别到的模块")
    if inventory.modules:
        for module in inventory.modules:
            typer.echo(f"- {module.get('kind', '模块')}：`{module.get('path', '.')}`（{module.get('name', '未命名')}）")
    else:
        typer.echo("- 暂未识别出稳定模块边界，建议人工补充。")

    typer.echo("\n识别到的验证命令")
    if commands.commands:
        for command in commands.commands:
            gate = "阻断式 hard gate" if command.gate == "hard" else "提示式 soft gate"
            typer.echo(f"- `{command.command}`：{gate}，来源 `{command.source}`，置信度 {command.confidence}")
    else:
        typer.echo("- 暂未发现稳定验证命令，后续会作为待补齐 Sensor。")

    show_scan_attention_summary(inventory, commands)


def show_scan_attention_summary(inventory: ProjectInventory, commands: CommandCatalog) -> None:
    show_llm_evidence_expansion(inventory)
    show_scan_followup_questions(inventory)
    show_scan_self_check(inventory)
    show_scan_followup_answer_guidance(inventory)

    typer.echo("\n风险区域")
    for line in risk_attention_lines(inventory):
        typer.echo(f"- {line}")

    typer.echo("\n不确定性")
    for line in uncertainty_attention_lines(inventory, commands):
        typer.echo(f"- {line}")

    typer.echo("\n验证缺口")
    for line in verification_gap_lines(commands):
        typer.echo(f"- {line}")

    typer.echo("\n建议补充")
    for line in human_followup_lines(inventory, commands):
        typer.echo(f"- {line}")


def show_llm_evidence_expansion(inventory: ProjectInventory) -> None:
    expansion = evidence_expansion(inventory)
    if expansion is None:
        return

    typer.echo("\nLLM 深度补充")
    requested = format_cli_items(expansion.get("requested_paths"))
    focus = format_cli_items(expansion.get("risk_focus"))
    read_paths = format_cli_items(expansion.get("read_paths"))
    rationale = str(expansion.get("rationale") or "未提供规划说明。")
    confidence = str(expansion.get("confidence") or "unknown")

    typer.echo(f"- LLM 规划补读：{requested}")
    typer.echo(f"- 关注原因：{focus}")
    typer.echo(f"- 规划说明：{rationale}")
    if list_items(expansion.get("read_paths")):
        typer.echo(f"- 实际读取：{read_paths}")
    else:
        typer.echo("- 实际读取：未读取到补充文件；请确认关键路径是否被遗漏或需要人工补充。")
    if confidence == "low":
        typer.echo(f"- 置信度：{confidence}，需要人工确认这些文件是否代表真实关键路径或风险边界。")
    else:
        typer.echo(f"- 置信度：{confidence}")


def show_scan_followup_questions(inventory: ProjectInventory) -> None:
    questions = scan_followup_questions(inventory)
    if not questions:
        return

    typer.echo("\n深度追问")
    for question in questions[:5]:
        text = str(question.get("question") or "是否需要补充扫描不确定性？")
        reason = str(question.get("reason") or "扫描阶段存在需要补救的不确定性。")
        affects = format_affect_labels(question.get("affects"))
        typer.echo(f"- {text}（原因：{reason}；影响：{affects}）")
    remaining = len(questions) - 5
    if remaining > 0:
        typer.echo(f"- 还有 {remaining} 个深度追问，详见 `.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md`。")


def scan_followup_questions(inventory: ProjectInventory) -> list[dict[str, object]]:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    scan_metadata = extensions.get("scan_metadata")
    if not isinstance(scan_metadata, dict):
        return []
    questions = scan_metadata.get("followup_questions")
    return [item for item in questions if isinstance(item, dict)] if isinstance(questions, list) else []


def show_scan_self_check(inventory: ProjectInventory) -> None:
    self_check = scan_self_check(inventory)
    if self_check is None:
        return

    typer.echo("\nLLM 二次自检")
    typer.echo("- 结论边界：pending_harness_maintainer_review；这只是 review-only 结论，不会自动修正正式扫描结果。")
    typer.echo(f"- 整体风险：{self_check.get('overall_risk', 'medium')}")
    typer.echo(f"- 摘要：{self_check.get('summary') or 'LLM 已对深度追问进行二次审查。'}")
    resolutions = self_check.get("resolutions")
    items = [item for item in resolutions if isinstance(item, dict)] if isinstance(resolutions, list) else []
    for item in items[:5]:
        status = str(item.get("status") or "needs_human_confirmation")
        action_type = str(item.get("suggested_action_type") or "maintainer_review")
        action_hint = scan_self_check_action_hint(action_type)
        action = str(item.get("suggested_next_action") or "请人工确认该追问。")
        rationale = str(item.get("rationale") or "当前 evidence 不足以完成确认。")
        interaction_id = str(item.get("interaction_id") or "unknown")
        typer.echo(f"- `{interaction_id}`：{status}；动作={action_type}；提示：{action_hint}；建议：{action}；理由：{rationale}")
    remaining = len(items) - 5
    if remaining > 0:
        typer.echo(f"- 还有 {remaining} 条二次自检结论，详见 `.ai/scan-metadata.yaml`。")


def scan_self_check(inventory: ProjectInventory) -> dict[str, object] | None:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    scan_metadata = extensions.get("scan_metadata")
    if not isinstance(scan_metadata, dict):
        return None
    self_check = scan_metadata.get("self_check")
    return self_check if isinstance(self_check, dict) else None


def show_scan_followup_answer_guidance(inventory: ProjectInventory) -> None:
    lines = scan_followup_answer_guidance_lines(inventory)
    if not lines:
        return

    typer.echo("\n深度追问回答建议")
    for line in lines:
        typer.echo(f"- {line}")


def scan_followup_answer_guidance_lines(inventory: ProjectInventory) -> list[str]:
    questions = scan_followup_questions(inventory)
    return scan_followup_answer_guidance_lines_for_questions(questions)


def evidence_expansion(inventory: ProjectInventory) -> dict[str, object] | None:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    scan_metadata = extensions.get("scan_metadata")
    if not isinstance(scan_metadata, dict):
        return None
    expansion = scan_metadata.get("evidence_expansion")
    return expansion if isinstance(expansion, dict) else None


def format_cli_items(value: object) -> str:
    items = list_items(value)
    if not items:
        return "无"
    return "、".join(f"`{item}`" for item in items[:5])


def format_plain_cli_items(value: object) -> str:
    items = list_items(value)
    if not items:
        return "无"
    return ", ".join(items[:5])


def format_affect_labels(value: object) -> str:
    labels = {
        "maturity": "成熟度",
        "guides": "Guides",
        "sensors": "Sensors",
        "workflow": "Workflow",
        "config": "配置",
    }
    items = list_items(value)
    if not items:
        return "无"
    return "、".join(labels.get(item, item) for item in items[:5])


def list_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def show_scan_maturity_snapshot(repo: Path, inventory: ProjectInventory, commands: CommandCatalog) -> None:
    planned = build_maturity_report(
        ai=None,
        inventory=inventory,
        commands=commands,
        config=HarnessConfig.default(),
        weapon_selection=select_weapon_library(inventory, commands),
    )

    typer.echo("\n扫描后的成熟度初评")
    if has_existing_partial_harness(repo):
        typer.echo("- 当前从 L1 起步：已发现部分 `.ai` 资产，但还不足以构成完整项目级 Harness。")
    else:
        typer.echo("- 当前从 L0 起步：尚未发现项目级 `.ai` Harness，后续 AI Coding 仍主要依赖临时 prompt 和个人经验。")
    typer.echo(f"- 按当前扫描写入后预计建立：{planned.overall_level} 基线。")
    typer.echo(f"- 下一目标：{planned.target_next_level or planned.overall_level}。")
    typer.echo("- 说明：这是基于当前扫描结果的写入前预测，不代表正式 Harness 已经写入或 benchmark 已经通过。")

    typer.echo("\n主要差距")
    blockers = planned.blocking_reasons[:3] or ["暂无明确阻断项；仍建议通过 benchmark 和真实任务运行验证。"]
    for blocker in blockers:
        typer.echo(f"- {blocker}")

    typer.echo("\n建议优先补充")
    for line in scan_maturity_followup_lines(planned):
        typer.echo(f"- {line}")


def scan_maturity_followup_lines(planned: MaturityReport) -> list[str]:
    return [
        "真实可执行的 hard gate 命令，以及哪些命令只能作为 soft signal。",
        "主要模块边界、入口目录和职责，避免 Guides 过于泛化。",
        "高风险区域，例如权限、数据迁移、配置、支付或核心状态变更路径。",
        "团队规则、架构边界或测试策略，这些会影响成熟度判断和后续 Harness 推荐。",
    ]


def risk_attention_lines(inventory: ProjectInventory) -> list[str]:
    risk_areas = stack_extensions_list(inventory, "risk_areas")
    if not risk_areas:
        return ["当前扫描暂未识别明确高风险区域；如存在支付、权限、数据迁移或配置目录，请在下一步补充。"]
    lines: list[str] = []
    for risk in risk_areas[:5]:
        signal = classify_risk_area(risk)
        if signal.is_high_impact:
            lines.append(
                f"【高风险，需人工确认】`{signal.path}`：{signal.reason}；"
                f"{signal.confirmation_reason} 命中后建议进入 standard workflow / Workflow 升级或人工确认。"
            )
        else:
            lines.append(f"`{signal.path}`：{signal.reason}")
    return lines


def uncertainty_attention_lines(inventory: ProjectInventory, commands: CommandCatalog) -> list[str]:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    lines: list[str] = []
    if extensions.get("needs_human_confirmation"):
        lines.append("LLM 扫描标记需要人工确认，请检查技术栈、模块边界、风险区域和验证命令是否符合真实项目。")
    llm_proposal = extensions.get("llm_scan_proposal")
    if isinstance(llm_proposal, dict):
        confidence = llm_proposal.get("confidence")
        if confidence and confidence != "high":
            lines.append(f"LLM 扫描置信度为 {confidence}，建议补充关键目录、测试入口或团队规则。")
    if inventory.primary_stack == "unknown":
        lines.append("主要技术栈仍不明确，需要人工补充真实技术栈或入口目录。")
    if not inventory.modules:
        lines.append("暂未识别稳定模块边界，需要人工确认主要模块、入口文件或职责分工。")
    for warning in stack_extensions_list(inventory, "scan_warnings")[:5]:
        lines.append(format_scan_warning_for_cli(inventory, warning))
    low_confidence_commands = [command for command in commands.commands if command.confidence == "low"]
    if low_confidence_commands:
        labels = ", ".join(f"`{command.command}`" for command in low_confidence_commands[:3])
        lines.append(f"低置信度验证命令：{labels}，需要确认是否稳定可执行。")
    return lines or ["当前扫描没有发现必须立即处理的不确定性；仍建议确认关键模块和验证命令。"]


def format_scan_warning_for_cli(inventory: ProjectInventory, warning: dict[str, object]) -> str:
    code = str(warning.get("code") or "unknown")
    if code == "source_sampling_truncated":
        bucket = warning_bucket(warning)
        stats = coverage_bucket_stats(inventory, bucket)
        label = source_bucket_label(bucket)
        if stats:
            selected = stats.get("selected_count", 0)
            total = stats.get("total_count", 0)
            skipped = stats.get("skipped_count", 0)
            return (
                f"{label} 源码文件较多，本次已抽样 {selected}/{total} 个文件，"
                f"还有 {skipped} 个未进入初始摘要；这可能影响技术栈、模块边界或风险判断，"
                "建议补充关键目录、入口文件或高风险路径。"
            )
        return (
            f"{label} 源码文件较多，本次只抽样读取了部分文件；"
            "可能遗漏核心模块或风险路径，建议补充关键目录、入口文件或高风险路径。"
        )
    if code == "test_evidence_not_found":
        return "当前扫描未找到明确测试证据；建议补充真实 test / integration / lint / typecheck 入口或说明只能先使用 soft gate。"
    message = str(warning.get("message") or code or "扫描存在未分类 warning")
    return f"扫描 warning（{code}）：{message}"


def warning_bucket(warning: dict[str, object]) -> str:
    bucket = warning.get("bucket")
    if bucket:
        return str(bucket)
    evidence = warning.get("evidence")
    if isinstance(evidence, list) and evidence:
        return str(evidence[0])
    return ""


def coverage_bucket_stats(inventory: ProjectInventory, bucket: str) -> dict[str, object] | None:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    scan_metadata = extensions.get("scan_metadata")
    if not isinstance(scan_metadata, dict):
        return None
    coverage = scan_metadata.get("coverage")
    if not isinstance(coverage, dict):
        return None
    bucket_coverage = coverage.get("bucket_coverage")
    if not isinstance(bucket_coverage, list):
        return None
    for item in bucket_coverage:
        if isinstance(item, dict) and item.get("bucket") == bucket:
            return item
    return None


def source_bucket_label(bucket: str) -> str:
    if bucket.startswith("source:") and len(bucket) > len("source:"):
        return f"`{bucket.removeprefix('source:')}`"
    return "源码"


def verification_gap_lines(commands: CommandCatalog) -> list[str]:
    if not commands.commands:
        return ["暂未发现验证命令；后续 Sensors 需要人工补充 build / test / lint / typecheck 入口。"]
    lines: list[str] = []
    hard_commands = [command for command in commands.commands if command.gate == "hard"]
    if not hard_commands:
        lines.append("暂未确认 hard gate；当前命令都不能直接作为阻断式完成门禁。")
    weak_hard_commands = [command for command in hard_commands if not command.source or command.confidence == "low"]
    if weak_hard_commands:
        labels = ", ".join(f"`{command.command}`" for command in weak_hard_commands[:3])
        lines.append(f"hard gate 证据不足或置信度低：{labels}，需要补充来源或降级为 soft gate。")
    soft_commands = [command for command in commands.commands if command.gate == "soft"]
    if soft_commands:
        labels = ", ".join(f"`{command.command}`" for command in soft_commands[:3])
        lines.append(f"soft gate 只能作为风险提示：{labels}，不能单独证明任务完成。")
    present_types = {command.type for command in commands.commands}
    missing_types = [label for label in ["build", "test", "lint", "typecheck"] if label not in present_types]
    if missing_types:
        lines.append(f"当前扫描未确认这些验证类型：{', '.join(missing_types)}。")
    return lines or ["已发现 hard gate 候选；仍建议确认其在本地和 CI 中稳定可重复。"]


def human_followup_lines(inventory: ProjectInventory, commands: CommandCatalog) -> list[str]:
    lines: list[str] = []
    risk_areas = stack_extensions_list(inventory, "risk_areas")
    if high_impact_risk_areas(risk_areas):
        lines.append("请确认高风险线索是否确认为风险边界，命中后是否需要 standard workflow / Workflow 升级或人工确认。")
    elif risk_areas:
        lines.append("请确认上述风险路径是否需要进入 Guides、Workflow 升级条件或人工确认项。")
    else:
        lines.append("如存在高风险目录、权限逻辑、配置变更或数据迁移，请在下一步补充。")
    if not any(command.gate == "hard" for command in commands.commands):
        lines.append("请补充真实可执行的 hard gate 命令，或确认当前项目只能先使用 soft gate。")
    if any(command.confidence == "low" for command in commands.commands):
        lines.append("请确认低置信度命令是否可在开发机或 CI 中稳定运行。")
    if not inventory.modules:
        lines.append("请补充主要模块路径、职责和入口文件，避免后续 Guide 过于泛化。")
    return lines


def stack_extensions_list(inventory: ProjectInventory, key: str) -> list[dict[str, object]]:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    value = extensions.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def stack_label(stack: str) -> str:
    labels = {
        "java-spring": "Java 后端项目，使用 Spring / Spring Boot 相关框架",
        "dotnet-aspnet": ".NET 后端项目，使用 ASP.NET Core 相关框架",
        "node": "Node.js / 前端或服务端 JavaScript 项目",
        "python-flask": "Python Flask 后端项目",
        "unknown": "暂时无法可靠判断，需要人工确认",
    }
    return labels.get(stack, stack)


def stack_summary_label(inventory: ProjectInventory) -> str:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    profile = extensions.get("stack_profile")
    if isinstance(profile, dict):
        composition = profile.get("composition_label")
        if isinstance(composition, str) and composition.strip():
            return composition.strip()
    return stack_label(inventory.primary_stack)
