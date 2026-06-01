from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidate, WeaponLibraryCandidateReport


@dataclass(frozen=True)
class WeaponCandidateStatus:
    total_count: int
    pending_count: int
    pending_dimensions: tuple[str, ...]
    top_candidate_id: str | None
    top_candidate_type: str | None
    top_candidate_dimensions: tuple[str, ...]
    top_review_boundary: str | None


def read_weapon_candidate_status(ai: Path) -> WeaponCandidateStatus | None:
    path = ai / "experience" / "weapon-library-candidates.yaml"
    if not path.exists():
        return None
    report = WeaponLibraryCandidateReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    pending = [candidate for candidate in report.candidates if _candidate_is_pending(candidate)]
    dimensions = _ordered_dimensions(item for candidate in pending for item in candidate.maturity_dimensions)
    top = pending[0] if pending else None
    return WeaponCandidateStatus(
        total_count=len(report.candidates),
        pending_count=len(pending),
        pending_dimensions=tuple(dimensions),
        top_candidate_id=top.id if top else None,
        top_candidate_type=top.candidate_type if top else None,
        top_candidate_dimensions=tuple(top.maturity_dimensions) if top else (),
        top_review_boundary=top.review_boundary if top else None,
    )


def weapon_candidate_action_detail(status: WeaponCandidateStatus) -> str | None:
    if not status.top_candidate_id:
        return None
    dimensions = ",".join(status.top_candidate_dimensions) or "none"
    return f"{status.top_candidate_id}:{dimensions}"


def _candidate_is_pending(candidate: WeaponLibraryCandidate) -> bool:
    return candidate.status == "candidate" or candidate.human_confirmation_required is True


def _ordered_dimensions(values) -> list[str]:
    ordered: list[str] = []
    for value in values:
        if value not in ordered:
            ordered.append(str(value))
    return ordered
