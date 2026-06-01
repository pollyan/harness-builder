from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError
import typer
import yaml

from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.existing_harness_actions import (
    existing_harness_action_menu_lines,
    is_existing_harness_action,
    normalize_existing_harness_action,
)
from harness_builder_agent.tools.existing_harness_action_runner import run_existing_harness_action
from harness_builder_agent.tools.existing_harness_signals import (
    benchmark_signal_lines,
    experience_status_lines,
    read_benchmark_status,
    workflow_routing_status_lines,
)
from harness_builder_agent.tools.existing_harness_status import render_existing_harness_status_overview_lines
from harness_builder_agent.tools.guided_scan_presentation import stack_summary_label
from harness_builder_agent.tools.maintenance_triage import (
    build_maintenance_triage,
    render_maintenance_triage_guidance_lines,
    render_maintenance_triage_lines,
    render_maintenance_triage_menu_hint_lines,
)


class ExistingHarnessStateLoadError(Exception):
    def __init__(self, source: str, error_type: str, message: str) -> None:
        super().__init__(message)
        self.source = source
        self.error_type = error_type
        self.message = message


def handle_existing_harness_entry(repo: Path, trace) -> Path | None:
    ai = repo / ".ai"
    if not (ai / "project-inventory.json").exists() or not (ai / "harness-config.yaml").exists():
        return None

    try:
        inventory, config, score = load_existing_harness_state(ai)
    except ExistingHarnessStateLoadError as exc:
        show_existing_harness_state_load_failed(exc)
        trace.event(
            "existing-harness",
            "failed",
            "Existing Harness state could not be loaded.",
            {
                "action": "load-state",
                "error": "existing_harness_state_invalid",
                "source": exc.source,
                "error_type": exc.error_type,
                "message": exc.message,
            },
        )
        trace.finish(
            "failed",
            {
                "existing_harness_action": "load-state",
                "error": "existing_harness_state_invalid",
                "source": exc.source,
                "error_type": exc.error_type,
                "message": exc.message,
            },
        )
        raise typer.Exit(code=1)

    benchmark = read_benchmark_status(ai)
    experience_lines = experience_status_lines(ai)
    maintenance_actions = build_maintenance_triage(ai, score)

    typer.echo("\n我发现这个仓库已存在 Harness。")
    typer.echo(f"- 仓库：`{inventory.repo_name}`")
    typer.echo(f"- 技术栈：{stack_summary_label(inventory)}")
    if score:
        typer.echo(f"- 当前成熟度：{score.overall_level}，下一目标：{score.target_next_level or score.overall_level}")
        if score.blocking_reasons:
            typer.echo(f"- 主要阻断项：{score.blocking_reasons[0]}")
    else:
        typer.echo("- 当前成熟度：未发现 `.ai/maturity-score.yaml`，建议先运行 assess。")
    typer.echo(f"- 最近 benchmark：{benchmark}")
    typer.echo("- 维护状态摘要（Maintenance overview）:")
    for line in render_existing_harness_status_overview_lines(ai, config, score, maintenance_actions):
        typer.echo(f"  - {line}")
    typer.echo("- 维护建议（Maintenance triage guidance）:")
    for line in render_maintenance_triage_guidance_lines(maintenance_actions):
        typer.echo(f"  - {line}")
    typer.echo("- 推荐动作快捷选择（Maintenance action shortcuts）:")
    for line in render_maintenance_triage_menu_hint_lines(maintenance_actions):
        typer.echo(f"  - {line}")
    typer.echo("- 审计明细（Audit signals）: 以下字段保留给排查、测试定位和报告溯源；优先按上方维护建议行动。")
    typer.echo("- 质量门禁信号（Benchmark signals）:")
    for line in benchmark_signal_lines(ai):
        typer.echo(f"  - {line}")
    typer.echo("- Workflow 路由信号（Workflow routing signals）:")
    for line in workflow_routing_status_lines(config):
        typer.echo(f"  - {line}")
    typer.echo("- 经验 / 审查信号（Experience / review signals）:")
    for line in experience_lines:
        typer.echo(f"  - {line}")
    typer.echo("- 维护优先级（Maintenance triage）:")
    for line in render_maintenance_triage_lines(maintenance_actions):
        typer.echo(f"  - {line}")
    typer.echo("\n可选动作")
    for line in existing_harness_action_menu_lines():
        typer.echo(line)

    while True:
        raw_action = typer.prompt("你的选择", default="1").strip()
        action = normalize_existing_harness_action(raw_action)
        if is_existing_harness_action(action):
            break
        typer.echo(f"未识别的维护动作：{raw_action}")
        typer.echo("请输入菜单编号、英文命令或中文别名；直接回车等同于 `1` 只读退出。")
    return run_existing_harness_action(repo, ai, inventory, action, trace, maintenance_actions)


def load_existing_harness_state(ai: Path) -> tuple[ProjectInventory, HarnessConfig, MaturityReport | None]:
    inventory = read_existing_harness_json(
        ai,
        "project-inventory.json",
        lambda content: ProjectInventory.model_validate_json(content),
    )
    config = read_existing_harness_yaml(
        ai,
        "harness-config.yaml",
        lambda payload: HarnessConfig.model_validate(payload),
    )
    score = None
    if (ai / "maturity-score.yaml").exists():
        score = read_existing_harness_yaml(
            ai,
            "maturity-score.yaml",
            lambda payload: MaturityReport.model_validate(payload),
        )
    return inventory, config, score


def read_existing_harness_json(ai: Path, filename: str, validator):
    path = ai / filename
    source = f".ai/{filename}"
    try:
        return validator(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, ValidationError) as exc:
        raise ExistingHarnessStateLoadError(source, type(exc).__name__, short_error_message(exc)) from exc


def read_existing_harness_yaml(ai: Path, filename: str, validator):
    path = ai / filename
    source = f".ai/{filename}"
    try:
        return validator(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, TypeError, ValueError, yaml.YAMLError, ValidationError) as exc:
        raise ExistingHarnessStateLoadError(source, type(exc).__name__, short_error_message(exc)) from exc


def short_error_message(exc: Exception, limit: int = 240) -> str:
    message = " ".join(str(exc).split())
    if len(message) <= limit:
        return message
    return f"{message[: limit - 1]}..."


def show_existing_harness_state_load_failed(error: ExistingHarnessStateLoadError) -> None:
    typer.echo("\n已有 Harness 读取失败。")
    typer.echo(f"- 文件：`{error.source}`")
    typer.echo(f"- 原因：{error.error_type}: {error.message}")
    typer.echo("- 未重新扫描，未覆盖正式 Harness 资产，未创建 Runtime 产物。")
    typer.echo("- 请修复该文件后重试；如果需要重新初始化，请先备份 `.ai/` 后再显式选择重新生成。")
