from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateDraft, AssetCandidateReport
from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceDecision, CandidateGovernanceLog
from harness_builder_agent.tools.asset_writers.shared import write_text, write_yaml
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
        "- `applied` decisions only support Guide and Sensor Markdown candidates in this MVP.\n"
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
