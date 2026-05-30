from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.scan_repo import scan_repository
from harness_builder_agent.tools.write_assets import write_initial_assets


def assess_maturity(repo: Path) -> Path:
    root = repo.resolve()
    ai = _ensure_harness(root)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
    commands = CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text(encoding="utf-8")))
    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))

    score = MaturityReport(
        overall_level=_overall_level(ai, commands, config),
        dimension_scores={
            "guides": "L2" if _contains_section(ai / "guides" / "project-context.md", "## 当前项目事实") else "L1",
            "sensors": "L2" if commands.commands else "L0",
            "workflow": "L2" if _skills_exist(ai) else "L1",
            "risk_control": "L0",
            "observability": "L1" if _has_generation_runs(ai) else "L0",
            "experience": "L1" if (ai / "experience" / "pending-improvements.md").exists() else "L0",
        },
        evidence=[
            f"主技术栈：{inventory.primary_stack}",
            f"模块数量：{len(inventory.modules)}",
            f"验证命令数量：{len(commands.commands)}",
            f"Workflow Skill 完整：{_skills_exist(ai)}",
        ],
        blocking_reasons=[
            "候选 Guides / Sensors 仍需人工确认",
            "尚未接入完整自动修复循环和 IDE Runtime",
        ],
        recommended_next_steps=[
            "确认候选规则和风险区域",
            "补齐缺失的 lint / typecheck / 安全检查",
            "运行 improve 生成可审查改进候选",
        ],
        last_assessed_at=datetime.now(UTC).isoformat(),
    )
    _write_yaml(ai / "maturity-score.yaml", score.model_dump(mode="json"))
    _write_report(ai / "maturity-report.md", score)
    return ai


def _ensure_harness(root: Path) -> Path:
    ai = root / ".ai"
    if not (ai / "project-inventory.json").exists():
        inventory, commands = scan_repository(root)
        write_initial_assets(root, inventory, commands)
    return ai


def _skills_exist(ai: Path) -> bool:
    return (ai / "skills" / "lightweight" / "SKILL.md").exists() and (ai / "skills" / "bugfix" / "SKILL.md").exists()


def _contains_section(path: Path, section: str) -> bool:
    return path.exists() and section in path.read_text(encoding="utf-8")


def _has_generation_runs(ai: Path) -> bool:
    runs = ai / "runs"
    return runs.exists() and any(path.is_dir() for path in runs.iterdir())


def _overall_level(ai: Path, commands: CommandCatalog, config: HarnessConfig) -> str:
    if _skills_exist(ai) and commands.commands and config.workflows:
        return "L2"
    if commands.commands:
        return "L1"
    return "L0"


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_report(path: Path, score: MaturityReport) -> None:
    dimensions = "\n".join(f"- {name}: {level}" for name, level in score.dimension_scores.items())
    evidence = "\n".join(f"- {item}" for item in score.evidence)
    blockers = "\n".join(f"- {item}" for item in score.blocking_reasons)
    next_steps = "\n".join(f"- {item}" for item in score.recommended_next_steps)
    path.write_text(
        "# 成熟度评估报告\n\n"
        f"整体等级：`{score.overall_level}`\n\n"
        "## 评分维度\n\n"
        f"{dimensions}\n\n"
        "## 证据\n\n"
        f"{evidence}\n\n"
        "## 阻断原因\n\n"
        f"{blockers}\n\n"
        "## 推荐下一步\n\n"
        f"{next_steps}\n",
        encoding="utf-8",
    )
