from pathlib import Path

import yaml

from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.tools.maturity_evidence import collect_maturity_evidence


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_base_ai(ai: Path) -> None:
    ai.mkdir(parents=True, exist_ok=True)
    (ai / "project-inventory.json").write_text(
        '{"schema_version":"1.0","repo_name":"demo","root_path":"/tmp/demo","primary_stack":"java-spring","modules":[],"evidence":[]}',
        encoding="utf-8",
    )
    _write_yaml(ai / "command-catalog.yaml", {"schema_version": "1.0", "commands": []})
    _write_yaml(ai / "harness-config.yaml", HarnessConfig.default().model_dump(mode="json"))
    _write_yaml(
        ai / "weapon-library-selection.yaml",
        {
            "schema_version": "1.0",
            "primary_stack": "java-spring",
            "selected_stacks": ["common"],
            "guide_weapon_ids": [],
            "sensor_weapon_ids": [],
            "guide_weapons": [],
            "sensor_weapons": [],
        },
    )


def test_collect_maturity_evidence_uses_experience_index(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_base_ai(ai)
    _write_yaml(
        ai / "experience" / "experience-index.yaml",
        {
            "schema_version": "1.0",
            "experience_files": {
                "project-experience.md": True,
                "repair-patterns.md": True,
                "sensor-feedback.md": True,
                "team-preferences.md": True,
                "pending-improvements.md": True,
                "deprecated-experience.md": False,
            },
            "pending_improvement_count": 2,
            "asset_candidate_count": 3,
            "maturity_review_count": 1,
            "runtime_task_run_count": 4,
            "warnings": [],
        },
    )
    _write_yaml(
        ai / "experience" / "experience-summary.yaml",
        {
            "summary": "Sensor coverage is the main signal.",
            "findings": [
                {
                    "id": "sensor-coverage-gap",
                    "kind": "sensor_feedback",
                    "title": "Sensor coverage gap",
                    "summary": "Pending improvements point to missing coverage.",
                    "evidence_sources": [".ai/experience/pending-improvements.md"],
                }
            ],
        },
    )

    pack = collect_maturity_evidence(ai)

    assert ".ai/experience/experience-index.yaml" in pack.maturity_inputs
    assert ".ai/experience/experience-summary.yaml" in pack.maturity_inputs
    assert pack.experience.has_experience_index is True
    assert pack.experience.has_pending_improvements is True
    assert pack.experience.pending_improvement_count == 2
    assert pack.experience.asset_candidate_count == 3
    assert pack.experience.maturity_review_count == 1
    assert pack.experience.runtime_task_run_count == 4
    assert pack.experience.experience_file_count == 5
    assert pack.experience.has_experience_summary is True
    assert pack.experience.experience_summary_finding_count == 1
    assert pack.harness_assets.workflow_routing_rule_count == 3
    assert pack.harness_assets.has_standard_escalation_rule is True
    standard_rule = next(rule for rule in pack.harness_assets.workflow_routing_rules if rule.id == "standard-escalation")
    assert standard_rule.selected_workflow == "standard"
    assert "cross_module_design" in standard_rule.triggers
    assert standard_rule.human_confirmation_required is True


def test_collect_maturity_evidence_keeps_pending_only_legacy_path(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_base_ai(ai)
    (ai / "experience").mkdir(parents=True)
    (ai / "experience" / "pending-improvements.md").write_text(
        "# Pending Improvements\n\n- first\n- second\n",
        encoding="utf-8",
    )

    pack = collect_maturity_evidence(ai)

    assert pack.experience.has_experience_index is False
    assert pack.experience.has_pending_improvements is True
    assert pack.experience.pending_improvement_count == 2
    assert pack.experience.asset_candidate_count == 0
