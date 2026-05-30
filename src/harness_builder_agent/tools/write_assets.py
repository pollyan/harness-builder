from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def write_initial_assets(repo: Path, inventory: ProjectInventory, commands: CommandCatalog) -> Path:
    ai = repo / ".ai"
    config = HarnessConfig.default()

    _write_json(ai / "project-inventory.json", inventory.model_dump(mode="json"))
    _write_yaml(ai / "command-catalog.yaml", commands.model_dump(mode="json"))
    _write_yaml(ai / "harness-config.yaml", config.model_dump(mode="json"))

    _write_text(ai / "scan-report.md", _scan_report(inventory, commands))
    _write_text(ai / "maturity-report.md", _maturity_report(inventory, commands))
    _write_yaml(ai / "maturity-score.yaml", _maturity_score(inventory, commands, config))
    _write_text(ai / "evolution-plan.md", _evolution_plan())

    _write_text(ai / "guides" / "project-context.md", _guide("project-context", inventory))
    _write_text(ai / "guides" / "coding-rules.md", _guide("coding-rules", inventory))
    _write_text(ai / "guides" / "architecture.md", _guide("architecture", inventory))
    _write_text(ai / "guides" / "task-templates" / "bugfix.md", _task_template("bugfix"))
    _write_text(ai / "guides" / "task-templates" / "lightweight-feature.md", _task_template("lightweight"))

    _write_text(ai / "sensors" / "verification.md", _sensor_doc(commands))
    _write_text(ai / "sensors" / "test-strategy.md", _test_strategy(commands))
    _copy_workflow_skills(ai)
    _write_text(ai / "experience" / "pending-improvements.md", "# Pending Improvements\n\nNo reviewed improvements yet.\n")
    return ai


def _frontmatter(asset_type: str) -> str:
    return (
        "---\n"
        f"asset_type: {asset_type}\n"
        "status: candidate\n"
        "source: inferred_from_codebase\n"
        "confidence: medium\n"
        "needs_human_confirmation: true\n"
        "---\n\n"
    )


def _scan_report(inventory: ProjectInventory, commands: CommandCatalog) -> str:
    command_lines = "\n".join(f"- `{command.command}` from `{command.source}`" for command in commands.commands) or "- No commands detected"
    evidence_lines = "\n".join(f"- `{item['path']}`: {item['reason']}" for item in inventory.evidence) or "- No evidence detected"
    return (
        "# Scan Report\n\n"
        f"Repository: `{inventory.repo_name}`\n\n"
        f"Primary stack: `{inventory.primary_stack}`\n\n"
        "## Evidence\n\n"
        f"{evidence_lines}\n\n"
        "## Command Candidates\n\n"
        f"{command_lines}\n"
    )


def _maturity_report(inventory: ProjectInventory, commands: CommandCatalog) -> str:
    level = "L2" if commands.commands else "L1"
    return (
        "# 成熟度评估报告\n\n"
        f"整体等级：`{level}`\n\n"
        "## 评分维度\n\n"
        "- Guides: L1\n"
        f"- Sensors: {'L2' if commands.commands else 'L0'}\n"
        "- Workflow: L2\n"
        "- Risk Control: L0\n"
        "- Observability: L1\n"
        "- Experience: L0\n\n"
        "## 证据\n\n"
        f"- 已识别技术栈：`{inventory.primary_stack}`。\n"
        f"- 已识别验证命令数量：{len(commands.commands)}。\n"
        "- 已生成项目级 Workflow Skill，但尚未接入完整 IDE Runtime。\n\n"
        "## 阻断原因\n\n"
        "- 风险目录和团队规则仍需要人工确认。\n"
        "- Sensor 失败后的自动修复闭环仍处于 POC 状态。\n\n"
        "## 推荐下一步\n\n"
        "- 由维护者确认核心风险目录和候选规则。\n"
        "- 将稳定的测试命令提升为 hard gate。\n"
        "- 根据真实任务结果审查 experience candidates。\n"
    )


def _maturity_score(inventory: ProjectInventory, commands: CommandCatalog, config: HarnessConfig) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "overall_level": "L2" if commands.commands else "L1",
        "dimension_scores": {
            "guides": "L1",
            "sensors": "L2" if commands.commands else "L0",
            "workflow": "L2" if config.workflows else "L0",
            "risk_control": "L0",
            "observability": "L1",
            "experience": "L0",
        },
        "evidence": [
            f"识别到主技术栈：{inventory.primary_stack}",
            f"识别到模块数量：{len(inventory.modules)}",
            f"识别到验证命令数量：{len(commands.commands)}",
            "已生成 lightweight 与 bugfix Workflow Skill",
        ],
        "blocking_reasons": [
            "候选 Guides / Sensors 尚未经过维护者确认",
            "Sensor 结果尚未形成长期趋势数据",
        ],
        "recommended_next_steps": [
            "审查并确认候选规则",
            "补齐缺失的 lint / typecheck / 安全检查",
            "基于真实任务记录运行 improve",
        ],
    }


def _evolution_plan() -> str:
    return (
        "# 演进计划\n\n"
        "1. 确认生成的项目上下文、架构说明和编码规则。\n"
        "2. 在开发机验证命令候选，并将稳定命令提升为 hard gate。\n"
        "3. 为重复出现的任务模式补充任务特定 Sensor。\n"
    )


def _guide(name: str, inventory: ProjectInventory) -> str:
    module_lines = "\n".join(f"- `{module['path']}` ({module['kind']})" for module in inventory.modules) or "- No modules detected"
    evidence_lines = "\n".join(f"- `{item['path']}`：{item['reason']}" for item in inventory.evidence) or "- 暂未发现直接证据"
    recommended_lines = "\n".join(f"- {item}" for item in _guide_recommendations(inventory.primary_stack))
    return (
        _frontmatter("guide")
        + f"# {name}\n\n"
        + f"仓库 `{inventory.repo_name}` 被识别为 `{inventory.primary_stack}`。\n\n"
        + "## 适用范围\n\n"
        + "当前覆盖整个仓库，正式生效前需要维护者审查。\n\n"
        + "## 当前项目事实\n\n"
        + f"- 主技术栈：`{inventory.primary_stack}`。\n"
        + f"- 技术栈线索：{', '.join(inventory.stacks) if inventory.stacks else '未知'}。\n"
        + "- 模块识别：\n"
        + f"{module_lines}\n\n"
        + "## 来源证据\n\n"
        + f"{evidence_lines}\n\n"
        + "## 候选规则\n\n"
        + f"{_candidate_rules(inventory.primary_stack)}\n\n"
        + "## Harness Builder 推荐补齐项\n\n"
        + f"{recommended_lines}\n\n"
        + "## 人工确认点\n\n"
        + "- 请确认模块边界是否符合团队真实架构。\n"
        + "- 请确认候选规则是否可以提升为正式 Guide。\n"
    )


def _task_template(kind: str) -> str:
    title = "缺陷修复任务模板" if kind == "bugfix" else "轻量级任务模板"
    return (
        _frontmatter("task_template")
        + f"# {title}\n\n"
        + "1. 复述任务和期望结果。\n"
        + "2. 映射影响模块、必读 Guides 和 Workflow Skill。\n"
        + "3. 执行选定的 hard gate Sensors。\n"
        + "4. 输出 decision log、sensor report 和 handoff summary。\n"
    )


def _sensor_doc(commands: CommandCatalog) -> str:
    command_lines = "\n".join(
        f"- `{command.id}`：`{command.command}`，gate=`{command.gate}`，来源 `{command.source}`，verified={command.verified}"
        for command in commands.commands
    ) or "- 暂未发现可执行验证命令"
    missing = _missing_sensor_lines(commands)
    return (
        "# 验证 Sensors\n\n"
        "## 已发现的验证命令\n\n"
        f"{command_lines}\n\n"
        "## 缺失验证能力\n\n"
        f"{missing}\n\n"
        "## 推荐验证活动\n\n"
        "- 为核心后端模块补齐 unit test / integration test。\n"
        "- 为配置、权限、接口和数据访问路径补充人工确认或 soft signal Sensor。\n"
        "- 将稳定、快速、可重复的命令提升为 hard gate。\n\n"
        "## 失败处理策略\n\n"
        "- hard gate 失败时任务保持未完成状态，并记录摘要和人工下一步。\n"
        "- soft signal 失败时进入 handoff summary，不直接阻断 POC 链路。\n"
        "- 本机缺少执行环境时记录 skipped，不编造通过结果。\n"
    )


def _test_strategy(commands: CommandCatalog) -> str:
    hard_gates = [command for command in commands.commands if command.gate == "hard"]
    lines = "\n".join(f"- `{command.command}`" for command in hard_gates) or "- Confirm test strategy with maintainer"
    return "# 测试策略\n\n## Hard Gates\n\n" + lines + "\n\n## 人工确认点\n\n- 请确认这些命令在团队开发机和 CI 中是否稳定。\n"


def _copy_workflow_skills(ai: Path) -> None:
    template_root = files("harness_builder_agent").joinpath("templates", "skills")
    for name in ("lightweight", "bugfix"):
        content = template_root.joinpath(name, "SKILL.md").read_text(encoding="utf-8")
        _write_text(ai / "skills" / name / "SKILL.md", content)


def _guide_recommendations(primary_stack: str) -> list[str]:
    if primary_stack == "java-spring":
        return [
            "确认 Maven 多模块之间的依赖边界，避免跨层直接调用。",
            "补充登录、权限、SQL 和配置变更的风险说明。",
            "为前端目录和后端接口建立对应关系说明。",
        ]
    if primary_stack == "dotnet-aspnet":
        return [
            "确认 solution / project 边界与 Clean Architecture 分层是否一致。",
            "补充 PublicApi、Web、Infrastructure 和测试项目之间的协作说明。",
            "确认 appsettings 和集成测试依赖的运行环境要求。",
        ]
    return ["请维护者补充团队约定、风险区域和测试策略。"]


def _candidate_rules(primary_stack: str) -> str:
    if primary_stack == "java-spring":
        return (
            "- Controller 层只处理接口入口和参数映射，业务逻辑应下沉到 Service。\n"
            "- Mapper / Repository 相关变更需要配套测试或人工确认。\n"
            "- 登录、权限、SQL 和配置变更默认需要更严格 Sensor。"
        )
    if primary_stack == "dotnet-aspnet":
        return (
            "- ApplicationCore 应保持领域和业务规则的中心位置。\n"
            "- Infrastructure 相关变更需要关注外部依赖和集成测试。\n"
            "- PublicApi / Web 文案或配置变更应至少运行 dotnet test 或记录跳过原因。"
        )
    return "- 当前技术栈置信度不足，所有规则先保持 candidate 状态。"


def _missing_sensor_lines(commands: CommandCatalog) -> str:
    present_types = {command.type for command in commands.commands}
    missing = []
    for sensor_type in ("lint", "typecheck", "security"):
        if sensor_type not in present_types:
            missing.append(f"- `{sensor_type}`：当前未发现稳定命令，建议人工确认后补齐。")
    return "\n".join(missing) if missing else "- 暂未发现明显缺失项。"
