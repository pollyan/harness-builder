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
from harness_builder_agent.tools.maturity_rendering import render_maturity_report_markdown
from harness_builder_agent.tools.init_summary import write_init_summary
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
    write_init_summary(ai, score, inventory=inventory, commands=commands)
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
    path.write_text(render_maturity_report_markdown(score), encoding="utf-8")
