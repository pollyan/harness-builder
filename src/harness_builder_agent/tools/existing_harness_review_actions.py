from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceLog
from harness_builder_agent.schemas.human_input_governance import HumanInputGovernanceLog
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_candidate_governance import WeaponCandidateGovernanceLog
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
from harness_builder_agent.tools.candidate_governance import review_candidate
from harness_builder_agent.tools.existing_harness_action_failures import fail_existing_harness_action
from harness_builder_agent.tools.existing_harness_action_summaries import (
    asset_candidate_apply_preview,
    asset_candidate_detail,
    candidate_governance_summary,
    human_input_governance_summary,
    weapon_candidate_governance_summary,
)
from harness_builder_agent.tools.human_input_governance import review_human_input
from harness_builder_agent.tools.maintenance_triage import MaintenanceAction
from harness_builder_agent.tools.weapon_candidate_governance import review_weapon_candidate


def run_review_candidate_action(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
) -> Path:
    trace.event(
        "existing-harness",
        "started",
        "Existing Harness detected; user chose candidate governance.",
        {"primary_stack": inventory.primary_stack, "action": "review-candidate"},
    )
    candidate_id = ""
    try:
        candidate_report = show_asset_candidate_summary(ai / "review" / "asset-candidates.yaml")
        candidate_id = typer.prompt("候选 ID", default="", show_default=False).strip()
        candidate = find_asset_candidate(candidate_report, candidate_id)
    except Exception as exc:
        fail_existing_harness_action(
            trace,
            inventory,
            "review-candidate",
            "Existing Harness candidate governance precheck failed.",
            str(exc),
            {"candidate_id": candidate_id},
        )
    typer.echo(asset_candidate_detail(candidate))
    typer.echo(asset_candidate_apply_preview(repo, candidate))
    decision = typer.prompt("决策 accepted/deferred/rejected/applied", default="deferred").strip().lower()
    if decision == "applied" and candidate.kind == "workflow_policy":
        fail_existing_harness_action(
            trace,
            inventory,
            "review-candidate",
            "Guided candidate governance does not apply workflow policy candidates.",
            "workflow_policy_applied_requires_expert_command",
            {"candidate_id": candidate_id},
        )
    if decision not in {"accepted", "deferred", "rejected", "applied"}:
        fail_existing_harness_action(
            trace,
            inventory,
            "review-candidate",
            "Unsupported guided candidate governance decision.",
            "unsupported_decision",
            {"candidate_id": candidate_id, "decision": decision},
        )
    rationale = typer.prompt("决策理由", default="", show_default=False).strip()
    reviewer = typer.prompt("Reviewer", default="harness-maintainer").strip() or "harness-maintainer"
    typer.echo("正在记录候选治理决策...")
    trace.event(
        "existing-harness",
        "started",
        "Existing Harness candidate governance decision started.",
        {"primary_stack": inventory.primary_stack, "action": "review-candidate", "candidate_id": candidate_id, "decision": decision},
    )
    try:
        output_dir = review_candidate(repo, candidate_id, decision, rationale, reviewer)
    except (FileNotFoundError, ValueError) as exc:
        fail_existing_harness_action(
            trace,
            inventory,
            "review-candidate",
            "Existing Harness candidate governance failed.",
            str(exc),
            {"candidate_id": candidate_id, "decision": decision},
        )
    governance = CandidateGovernanceLog.model_validate(
        yaml.safe_load((output_dir / "review" / "candidate-governance.yaml").read_text(encoding="utf-8"))
    )
    latest = governance.decisions[-1]
    trace.artifact(output_dir / "review" / "candidate-governance.yaml", "candidate_governance")
    trace.artifact(output_dir / "review" / "candidate-governance.md", "review")
    trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
    trace.event(
        "existing-harness",
        "completed",
        "Existing Harness candidate governance decision recorded.",
        {
            "primary_stack": inventory.primary_stack,
            "action": "review-candidate",
            "candidate_id": latest.candidate_id,
            "decision": latest.decision,
            "reviewer": latest.reviewer,
        },
    )
    trace.finish(
        "completed",
        {
            "primary_stack": inventory.primary_stack,
            "existing_harness_action": "review-candidate",
            "candidate_id": latest.candidate_id,
            "decision": latest.decision,
            "reviewer": latest.reviewer,
            "applied_path_count": len(latest.applied_paths),
        },
    )
    typer.echo(candidate_governance_summary(latest.candidate_id, latest.decision, latest.reviewer, len(latest.applied_paths)))
    return output_dir


def run_review_human_input_action(
    repo: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path:
    default_interaction_id = review_human_input_default_interaction_id(maintenance_actions)
    interaction_id = typer.prompt(
        "Human input interaction ID",
        default=default_interaction_id or "",
        show_default=default_interaction_id is not None,
    ).strip()
    decision = typer.prompt("决策 resolved/reopened", default="resolved").strip().lower()
    rationale = typer.prompt("决策理由", default="", show_default=False).strip()
    reviewer = typer.prompt("Reviewer", default="harness-maintainer").strip() or "harness-maintainer"
    typer.echo("正在记录 human-input 治理决策...")
    trace.event(
        "existing-harness",
        "started",
        "Existing Harness detected; user chose human input governance.",
        {"primary_stack": inventory.primary_stack, "action": "review-human-input", "interaction_id": interaction_id, "decision": decision},
    )
    try:
        output_dir = review_human_input(repo, interaction_id, decision, rationale, reviewer)
    except (FileNotFoundError, ValueError) as exc:
        fail_existing_harness_action(
            trace,
            inventory,
            "review-human-input",
            "Existing Harness human input governance failed.",
            str(exc),
            {"interaction_id": interaction_id, "decision": decision},
        )
    governance = HumanInputGovernanceLog.model_validate(
        yaml.safe_load((output_dir / "review" / "human-input-governance.yaml").read_text(encoding="utf-8"))
    )
    latest = governance.decisions[-1]
    trace.artifact(output_dir / "questionnaire.yaml", "questionnaire")
    trace.artifact(output_dir / "human-input-needed.md", "human_confirmation")
    trace.artifact(output_dir / "review" / "human-input-governance.yaml", "human_input_governance")
    trace.artifact(output_dir / "review" / "human-input-governance.md", "review")
    trace.event(
        "existing-harness",
        "completed",
        "Existing Harness human input governance decision recorded.",
        {
            "primary_stack": inventory.primary_stack,
            "action": "review-human-input",
            "interaction_id": latest.interaction_id,
            "decision": latest.decision,
            "reviewer": latest.reviewer,
        },
    )
    trace.finish(
        "completed",
        {
            "primary_stack": inventory.primary_stack,
            "existing_harness_action": "review-human-input",
            "interaction_id": latest.interaction_id,
            "decision": latest.decision,
            "reviewer": latest.reviewer,
            "new_response_status": latest.new_response_status,
        },
    )
    typer.echo(human_input_governance_summary(latest.interaction_id, latest.decision, latest.reviewer, latest.new_response_status))
    return output_dir


def run_review_initial_candidate_action(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
) -> Path:
    try:
        show_weapon_candidate_summary(ai / "experience" / "weapon-library-candidates.yaml")
    except (FileNotFoundError, ValueError) as exc:
        fail_existing_harness_action(
            trace,
            inventory,
            "review-initial-candidate",
            "Initial LLM candidate report is unavailable.",
            str(exc),
        )
    candidate_id = typer.prompt("初始候选 ID", default="", show_default=False).strip()
    decision = typer.prompt("决策 accepted/rejected/kept", default="kept").strip().lower()
    rationale = typer.prompt("决策理由", default="", show_default=False).strip()
    reviewer = typer.prompt("Reviewer", default="harness-maintainer").strip() or "harness-maintainer"
    typer.echo("正在记录初始 LLM candidate 治理决策...")
    trace.event(
        "existing-harness",
        "started",
        "Existing Harness detected; user chose initial LLM candidate governance.",
        {
            "primary_stack": inventory.primary_stack,
            "action": "review-initial-candidate",
            "candidate_id": candidate_id,
            "decision": decision,
        },
    )
    try:
        output_dir = review_weapon_candidate(repo, candidate_id, decision, rationale, reviewer)
    except (FileNotFoundError, ValueError) as exc:
        fail_existing_harness_action(
            trace,
            inventory,
            "review-initial-candidate",
            "Existing Harness initial LLM candidate governance failed.",
            str(exc),
            {"candidate_id": candidate_id, "decision": decision},
        )
    governance = WeaponCandidateGovernanceLog.model_validate(
        yaml.safe_load((output_dir / "review" / "weapon-candidate-governance.yaml").read_text(encoding="utf-8"))
    )
    latest = governance.decisions[-1]
    trace.artifact(output_dir / "experience" / "weapon-library-candidates.yaml", "weapon_library_candidates")
    trace.artifact(output_dir / "review" / "weapon-candidate-governance.yaml", "weapon_candidate_governance")
    trace.artifact(output_dir / "review" / "weapon-candidate-governance.md", "review")
    trace.artifact(output_dir / "review" / "llm-enhancement-candidates.md", "review")
    trace.artifact(output_dir / "review" / "candidate-guides.md", "review")
    trace.artifact(output_dir / "review" / "candidate-sensors.md", "review")
    trace.event(
        "existing-harness",
        "completed",
        "Existing Harness initial LLM candidate governance decision recorded.",
        {
            "primary_stack": inventory.primary_stack,
            "action": "review-initial-candidate",
            "candidate_id": latest.candidate_id,
            "decision": latest.decision,
            "reviewer": latest.reviewer,
            "new_status": latest.new_status,
        },
    )
    trace.finish(
        "completed",
        {
            "primary_stack": inventory.primary_stack,
            "existing_harness_action": "review-initial-candidate",
            "candidate_id": latest.candidate_id,
            "decision": latest.decision,
            "reviewer": latest.reviewer,
            "new_status": latest.new_status,
        },
    )
    typer.echo(weapon_candidate_governance_summary(latest.candidate_id, latest.decision, latest.reviewer, latest.new_status))
    return output_dir


def review_human_input_default_interaction_id(maintenance_actions: list[MaintenanceAction]) -> str | None:
    for action in maintenance_actions:
        if action.action == "review-human-input" and action.reason == "human_input_scan_followups_pending":
            return action.detail
    return None


def show_asset_candidate_summary(path: Path) -> AssetCandidateReport:
    report = AssetCandidateReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    typer.echo("\n待治理候选")
    for candidate in report.candidates[:10]:
        typer.echo(
            f"- `{candidate.id}`：{candidate.title}，kind={candidate.kind}，"
            f"target=`{candidate.suggested_path}`，risk={candidate.risk_level}"
        )
    if len(report.candidates) > 10:
        typer.echo(f"- 还有 {len(report.candidates) - 10} 个候选，请查看 `.ai/review/asset-candidates.yaml`。")
    typer.echo("guided review-candidate 可记录 accepted/deferred/rejected；Guide/Sensor 候选可显式 applied。")
    typer.echo("workflow_policy 候选应用仍需使用专家命令。")
    return report


def find_asset_candidate(report: AssetCandidateReport, candidate_id: str):
    for candidate in report.candidates:
        if candidate.id == candidate_id:
            return candidate
    raise typer.BadParameter(f"unknown asset candidate id: {candidate_id}")


def show_weapon_candidate_summary(path: Path) -> WeaponLibraryCandidateReport:
    report = WeaponLibraryCandidateReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    typer.echo("\n初始 LLM Guide/Sensor 候选")
    for candidate in report.candidates[:10]:
        dimensions = ",".join(candidate.maturity_dimensions) or "none"
        typer.echo(
            f"- `{candidate.id}`：{candidate.title}，type={candidate.candidate_type}，"
            f"status={candidate.status}，human_confirmation_required={str(candidate.human_confirmation_required).lower()}，"
            f"maturity={dimensions}"
        )
    if len(report.candidates) > 10:
        typer.echo(f"- 还有 {len(report.candidates) - 10} 个候选，请查看 `.ai/experience/weapon-library-candidates.yaml`。")
    typer.echo("guided review-initial-candidate 只记录 accepted/rejected/kept，不写正式 Guide / Sensor。")
    return report
