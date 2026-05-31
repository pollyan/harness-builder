from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.maturity_model import build_maturity_report


def _inventory() -> ProjectInventory:
    return ProjectInventory(repo_name="demo", root_path="/tmp/demo", primary_stack="java-spring", modules=[], evidence=[])


def _commands() -> CommandCatalog:
    return CommandCatalog(commands=[])


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_experience_dimension_uses_workflow_recommendation_review_count(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_yaml(
        ai / "experience" / "experience-index.yaml",
        {
            "schema_version": "1.0",
            "experience_files": {"pending-improvements.md": True},
            "sources": [
                {"path": ".ai/review/workflow-routing-recommendation.yaml", "kind": "workflow_recommendation", "item_count": 1}
            ],
            "pending_improvement_count": 0,
            "asset_candidate_count": 0,
            "maturity_review_count": 0,
            "workflow_recommendation_count": 1,
            "runtime_task_run_count": 0,
            "warnings": [],
        },
    )

    report = build_maturity_report(ai=ai, inventory=_inventory(), commands=_commands(), config=HarnessConfig.default())

    experience = report.dimensions["experience"]
    assert experience.level == "L2"
    assert any("Workflow recommendation reviews: 1" in item.summary for item in experience.evidence)
    assert any(blocker.id == "experience-not-runtime-derived" for blocker in experience.blockers)


def test_experience_dimension_keeps_legacy_pending_file_behavior(tmp_path: Path):
    ai = tmp_path / ".ai"
    (ai / "experience").mkdir(parents=True)
    (ai / "experience" / "pending-improvements.md").write_text("# Pending Improvements\n", encoding="utf-8")

    report = build_maturity_report(ai=ai, inventory=_inventory(), commands=_commands(), config=HarnessConfig.default())

    assert report.dimensions["experience"].level == "L1"
