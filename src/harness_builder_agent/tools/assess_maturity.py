from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.maturity_evidence import build_maturity_evidence_pack
from harness_builder_agent.tools.maturity_model import build_maturity_report
from harness_builder_agent.tools.scan_repo import scan_repository
from harness_builder_agent.tools.write_assets import write_initial_assets


def assess_maturity(repo: Path) -> Path:
    root = repo.resolve()
    ai = _ensure_harness(root)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
    commands = CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text(encoding="utf-8")))
    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))

    score = build_maturity_report(
        ai=ai,
        inventory=inventory,
        commands=commands,
        config=config,
        assessed_at=datetime.now(UTC).isoformat(),
    )
    _write_yaml(ai / "maturity-score.yaml", score.model_dump(mode="json"))
    _write_report(ai / "maturity-report.md", score)
    evidence = build_maturity_evidence_pack(ai=ai, inventory=inventory, commands=commands, config=config)
    _write_yaml(ai / "maturity-evidence.yaml", evidence.model_dump(mode="json"))
    return ai


def _ensure_harness(root: Path) -> Path:
    ai = root / ".ai"
    if not (ai / "project-inventory.json").exists():
        inventory, commands = scan_repository(root)
        write_initial_assets(root, inventory, commands)
    return ai


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_report(path: Path, score: MaturityReport) -> None:
    dimensions = "\n".join(f"- {name}: {level}" for name, level in score.dimension_scores.items())
    evidence = "\n".join(f"- {item}" for item in score.evidence)
    blockers = "\n".join(f"- {item}" for item in score.blocking_reasons)
    next_steps = "\n".join(f"- {item}" for item in score.recommended_next_steps)
    dimension_details = "\n".join(_dimension_detail(name, report) for name, report in score.dimensions.items())
    next_level_requirements = "\n".join(
        f"- {name}: {requirement}"
        for name, report in score.dimensions.items()
        for requirement in report.next_level_requirements
    )
    path.write_text(
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
        f"{next_steps}\n",
        encoding="utf-8",
    )


def _dimension_detail(name: str, report) -> str:
    evidence = "; ".join(f"{item.source}: {item.summary}" for item in report.evidence) or "无"
    blockers = "; ".join(item.reason for item in report.blockers) or "无"
    return f"- {name}: {report.level}\n  - evidence: {evidence}\n  - blockers: {blockers}"
