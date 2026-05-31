from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateDraft, AssetCandidateReport
from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceDecision, CandidateGovernanceLog
from harness_builder_agent.schemas.harness_config import HarnessConfig, WorkflowRoutingRule
from harness_builder_agent.tools.asset_writers.shared import write_text, write_yaml
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.experience_index import write_experience_index

CandidateDecision = Literal["accepted", "deferred", "rejected", "applied"]


def review_candidate(
    repo: Path,
    candidate_id: str,
    decision: CandidateDecision | str,
    rationale: str,
    reviewer: str = "harness-maintainer",
) -> Path:
    if decision not in {"accepted", "deferred", "rejected", "applied"}:
        raise ValueError(f"Unsupported candidate governance decision: {decision}")
    if not rationale.strip():
        raise ValueError("rationale is required for candidate governance decisions")

    root = repo.resolve()
    ai = root / ".ai"
    report_path = ai / "review" / "asset-candidates.yaml"
    if not report_path.exists():
        raise FileNotFoundError("missing .ai/review/asset-candidates.yaml")

    report = AssetCandidateReport.model_validate(yaml.safe_load(report_path.read_text(encoding="utf-8")))
    candidate = _find_candidate(report, candidate_id)
    target_path = _resolve_ai_path(root, candidate.suggested_path)
    log_path = ai / "review" / "candidate-governance.yaml"
    log = _load_log(log_path)

    applied_paths: list[str] = []
    if decision == "applied":
        _ensure_not_already_applied(log, candidate_id)
        if candidate.kind == "workflow_policy":
            _apply_workflow_policy_candidate(root, candidate)
        else:
            _apply_markdown_candidate(candidate, target_path)
        applied_paths = [candidate.suggested_path]

    log.decisions.append(
        CandidateGovernanceDecision(
            candidate_id=candidate.id,
            candidate_kind=candidate.kind,
            source_report=".ai/review/asset-candidates.yaml",
            source_candidate_id=candidate.source_candidate_id,
            suggested_path=candidate.suggested_path,
            decision=decision,
            rationale=rationale.strip(),
            reviewer=reviewer,
            decided_at=_utc_now(),
            applied_paths=applied_paths,
            acceptance_checks=candidate.acceptance_checks,
            evidence_sources=candidate.evidence_sources,
        )
    )
    _write_governance(ai, log)
    write_experience_index(ai)
    if decision == "applied" and candidate.kind == "workflow_policy":
        assess_maturity(root)
    return ai


def _find_candidate(report: AssetCandidateReport, candidate_id: str) -> AssetCandidateDraft:
    for candidate in report.candidates:
        if candidate.id == candidate_id:
            return candidate
    raise ValueError(f"unknown asset candidate id: {candidate_id}")


def _load_log(path: Path) -> CandidateGovernanceLog:
    if not path.exists():
        return CandidateGovernanceLog()
    return CandidateGovernanceLog.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _ensure_not_already_applied(log: CandidateGovernanceLog, candidate_id: str) -> None:
    if any(item.candidate_id == candidate_id and item.decision == "applied" for item in log.decisions):
        raise ValueError(f"candidate already applied: {candidate_id}")


def _resolve_ai_path(root: Path, suggested_path: str) -> Path:
    if not suggested_path.startswith(".ai/"):
        raise ValueError("suggested_path must stay under .ai/")
    target = (root / suggested_path).resolve()
    ai = (root / ".ai").resolve()
    if target != ai and ai not in target.parents:
        raise ValueError("suggested_path must stay under .ai/")
    return target


def _apply_markdown_candidate(candidate: AssetCandidateDraft, target_path: Path) -> None:
    if candidate.kind not in {"guide", "sensor"} or target_path.suffix != ".md":
        raise ValueError("applied only supports guide or sensor Markdown candidates")
    marker = f"<!-- harness-builder:candidate-applied id={candidate.id} -->"
    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    if marker in existing:
        raise ValueError(f"candidate already applied: {candidate.id}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    block = (
        f"{marker}\n"
        f"## Applied Candidate: {candidate.title}\n\n"
        f"Rationale: {candidate.rationale}\n\n"
        f"{candidate.draft_content.rstrip()}\n"
        f"<!-- /harness-builder:candidate-applied -->\n"
    )
    separator = "\n\n" if existing.strip() else ""
    target_path.write_text(f"{existing.rstrip()}{separator}{block}", encoding="utf-8")


def _apply_workflow_policy_candidate(root: Path, candidate: AssetCandidateDraft) -> None:
    if candidate.suggested_path != ".ai/harness-config.yaml":
        raise ValueError("workflow_policy candidates can only target .ai/harness-config.yaml")
    if candidate.workflow_policy_patch is None:
        raise ValueError("workflow_policy_patch is required for workflow_policy candidates")

    ai = root / ".ai"
    config_path = ai / "harness-config.yaml"
    config = HarnessConfig.model_validate(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    updated = config.model_copy(deep=True)
    rule = candidate.workflow_policy_patch.rule
    _validate_workflow_rule(root, updated, rule)
    rules = [existing for existing in updated.workflow_routing.rules if existing.id != rule.id]
    rules.append(rule)
    updated.workflow_routing.rules = rules
    _validate_routing_policy_invariants(updated)
    write_yaml(config_path, updated.model_dump(mode="json"))


def _validate_workflow_rule(root: Path, config: HarnessConfig, rule: WorkflowRoutingRule) -> None:
    if rule.selected_workflow not in config.workflows:
        raise ValueError(f"selected workflow does not exist: {rule.selected_workflow}")
    for guide in rule.required_guides:
        _require_ai_file(root, guide, "required guide")
    for sensor in rule.required_sensors:
        _require_ai_file(root, sensor, "required sensor")


def _require_ai_file(root: Path, rel_path: str, label: str) -> None:
    if not rel_path.startswith(".ai/"):
        raise ValueError(f"{label} must stay under .ai/: {rel_path}")
    path = (root / rel_path).resolve()
    ai = (root / ".ai").resolve()
    if path != ai and ai not in path.parents:
        raise ValueError(f"{label} must stay under .ai/: {rel_path}")
    if not path.is_file():
        raise ValueError(f"{label} does not exist: {rel_path}")


def _validate_routing_policy_invariants(config: HarnessConfig) -> None:
    errors: list[str] = []
    if config.workflow_routing.default_workflow != "lightweight":
        errors.append("default workflow must remain lightweight")
    rule_ids = [rule.id for rule in config.workflow_routing.rules]
    if len(rule_ids) != len(set(rule_ids)):
        errors.append("workflow routing rule ids must be unique")
    required_rule_ids = {"bugfix-intent", "low-risk-lightweight", "standard-escalation"}
    if not required_rule_ids.issubset(set(rule_ids)):
        errors.append("workflow routing must keep required baseline rules")
    standard = next((rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation"), None)
    if standard is None:
        errors.append("standard-escalation rule is required")
    else:
        required_triggers = {"high_risk_module", "cross_module_design", "security_or_permission", "insufficient_sensor_coverage"}
        if not required_triggers.issubset(set(standard.triggers)):
            errors.append("standard-escalation must keep required triggers")
        if not standard.human_confirmation_required:
            errors.append("standard-escalation must require human confirmation")
    if errors:
        raise ValueError("; ".join(errors))


def _write_governance(ai: Path, log: CandidateGovernanceLog) -> None:
    write_yaml(ai / "review" / "candidate-governance.yaml", log.model_dump(mode="json"))
    write_text(ai / "review" / "candidate-governance.md", _governance_markdown(log))


def _governance_markdown(log: CandidateGovernanceLog) -> str:
    decisions = "\n\n".join(_decision_markdown(item) for item in log.decisions) or "No decisions recorded."
    return (
        "# Candidate Governance\n\n"
        "## Decisions\n\n"
        f"{decisions}\n\n"
        "## Review Boundary\n\n"
        "- LLM asset candidates remain review-only unless an explicit governance decision applies them.\n"
        "- Guide and Sensor candidates are appended to Markdown assets; workflow policy candidates require a structured patch.\n"
    )


def _decision_markdown(decision: CandidateGovernanceDecision) -> str:
    applied = "\n".join(f"- `{path}`" for path in decision.applied_paths) or "- None."
    checks = "\n".join(f"- {item}" for item in decision.acceptance_checks) or "- None."
    evidence = "\n".join(f"- `{item}`" for item in decision.evidence_sources) or "- None."
    return (
        f"### {decision.candidate_id}\n\n"
        f"- kind: `{decision.candidate_kind}`\n"
        f"- decision: `{decision.decision}`\n"
        f"- suggested path: `{decision.suggested_path}`\n"
        f"- reviewer: `{decision.reviewer}`\n"
        f"- decided at: `{decision.decided_at}`\n\n"
        "#### Rationale\n\n"
        f"{decision.rationale}\n\n"
        "#### Applied Paths\n\n"
        f"{applied}\n\n"
        "#### Acceptance Checks\n\n"
        f"{checks}\n\n"
        "#### Evidence Sources\n\n"
        f"{evidence}"
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
