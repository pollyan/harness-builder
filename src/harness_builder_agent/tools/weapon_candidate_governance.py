from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from harness_builder_agent.schemas.weapon_candidate_governance import (
    WeaponCandidateGovernanceDecision,
    WeaponCandidateGovernanceLog,
    WeaponCandidateDecision,
)
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidate, WeaponLibraryCandidateReport
from harness_builder_agent.tools.asset_writers.shared import write_text, write_yaml
from harness_builder_agent.tools.llm_enhancement_candidates import (
    candidate_guides_markdown,
    candidate_sensors_markdown,
    enhancement_summary_markdown,
)


def review_weapon_candidate(
    repo: Path,
    candidate_id: str,
    decision: WeaponCandidateDecision | str,
    rationale: str,
    reviewer: str = "harness-maintainer",
) -> Path:
    if decision not in {"accepted", "rejected", "kept"}:
        raise ValueError(f"Unsupported weapon candidate governance decision: {decision}")
    if not rationale.strip():
        raise ValueError("rationale is required for weapon candidate governance decisions")

    root = repo.resolve()
    ai = root / ".ai"
    report_path = ai / "experience" / "weapon-library-candidates.yaml"
    if not report_path.exists():
        raise FileNotFoundError("missing .ai/experience/weapon-library-candidates.yaml")

    report = WeaponLibraryCandidateReport.model_validate(yaml.safe_load(report_path.read_text(encoding="utf-8")))
    candidate = _find_candidate(report, candidate_id)
    previous_status = candidate.status
    new_status = _new_status_for_decision(str(decision))

    candidate.status = new_status
    candidate.human_confirmation_required = decision == "kept"
    candidate.decision_notes = rationale.strip()

    write_yaml(report_path, report.model_dump(mode="json"))
    _write_candidate_review_markdown(ai, report)

    log_path = ai / "review" / "weapon-candidate-governance.yaml"
    log = _load_log(log_path)
    log.decisions.append(
        WeaponCandidateGovernanceDecision(
            candidate_id=candidate.id,
            candidate_type=candidate.candidate_type,
            decision=decision,
            rationale=rationale.strip(),
            reviewer=reviewer,
            decided_at=_utc_now(),
            previous_status=previous_status,
            new_status=new_status,
            maturity_dimensions=candidate.maturity_dimensions,
            review_boundary=candidate.review_boundary,
        )
    )
    _write_governance(ai, log)
    return ai


def show_weapon_candidate_summary(path: Path) -> WeaponLibraryCandidateReport:
    report = WeaponLibraryCandidateReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    return report


def _find_candidate(report: WeaponLibraryCandidateReport, candidate_id: str) -> WeaponLibraryCandidate:
    for candidate in report.candidates:
        if candidate.id == candidate_id:
            return candidate
    raise ValueError(f"unknown weapon candidate id: {candidate_id}")


def _new_status_for_decision(decision: str):
    if decision == "accepted":
        return "confirmed"
    if decision == "rejected":
        return "rejected"
    return "candidate"


def _load_log(path: Path) -> WeaponCandidateGovernanceLog:
    if not path.exists():
        return WeaponCandidateGovernanceLog()
    return WeaponCandidateGovernanceLog.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _write_candidate_review_markdown(ai: Path, report: WeaponLibraryCandidateReport) -> None:
    payload = report.model_dump(mode="json")
    write_text(ai / "review" / "llm-enhancement-candidates.md", enhancement_summary_markdown(payload))
    write_text(ai / "review" / "candidate-guides.md", candidate_guides_markdown(payload))
    write_text(ai / "review" / "candidate-sensors.md", candidate_sensors_markdown(payload))


def _write_governance(ai: Path, log: WeaponCandidateGovernanceLog) -> None:
    write_yaml(ai / "review" / "weapon-candidate-governance.yaml", log.model_dump(mode="json"))
    write_text(ai / "review" / "weapon-candidate-governance.md", _governance_markdown(log))


def _governance_markdown(log: WeaponCandidateGovernanceLog) -> str:
    decisions = "\n\n".join(_decision_markdown(item) for item in log.decisions) or "No decisions recorded."
    return (
        "# Weapon Candidate Governance\n\n"
        "## Decisions\n\n"
        f"{decisions}\n\n"
        "## Review Boundary\n\n"
        "- Initial LLM Guide / Sensor candidates stay review-only.\n"
        "- `accepted` confirms the candidate direction but does not write formal Guides or Sensors.\n"
        "- `rejected` closes the candidate without applying it.\n"
        "- `kept` leaves the candidate pending for later Harness Maintainer review.\n"
    )


def _decision_markdown(decision: WeaponCandidateGovernanceDecision) -> str:
    dimensions = ", ".join(f"`{item}`" for item in decision.maturity_dimensions) or "None."
    return (
        f"### {decision.candidate_id}\n\n"
        f"- type: `{decision.candidate_type}`\n"
        f"- decision: `{decision.decision}`\n"
        f"- previous status: `{decision.previous_status}`\n"
        f"- new status: `{decision.new_status}`\n"
        f"- reviewer: `{decision.reviewer}`\n"
        f"- decided at: `{decision.decided_at}`\n"
        f"- source report: `{decision.source_report}`\n"
        f"- maturity dimensions: {dimensions}\n\n"
        "#### Rationale\n\n"
        f"{decision.rationale}"
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
