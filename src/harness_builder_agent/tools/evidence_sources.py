from __future__ import annotations

from collections.abc import Iterable

from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.tools.maturity_evidence import MATURITY_INPUTS

BASELINE_HARNESS_ASSET_SOURCES = {
    ".ai/guides/project-context.md",
    ".ai/guides/coding-rules.md",
    ".ai/guides/architecture.md",
    ".ai/guides/task-templates/bugfix.md",
    ".ai/guides/task-templates/lightweight-feature.md",
    ".ai/sensors/verification.md",
    ".ai/sensors/test-strategy.md",
    ".ai/skills/lightweight/SKILL.md",
    ".ai/skills/bugfix/SKILL.md",
    ".ai/skills/standard/SKILL.md",
}

CORE_EVIDENCE_SOURCES = {
    *MATURITY_INPUTS,
    *BASELINE_HARNESS_ASSET_SOURCES,
    ".ai/project-inventory.json",
    ".ai/command-catalog.yaml",
    ".ai/harness-config.yaml",
    ".ai/maturity-score.yaml",
    ".ai/maturity-evidence.yaml",
    ".ai/improvement-candidates.yaml",
    ".ai/experience/experience-index.yaml",
}

EXPERIENCE_SUMMARY_SOURCE_INPUTS = {
    ".ai/experience/pending-improvements.md",
    ".ai/experience/project-experience.md",
    ".ai/experience/repair-patterns.md",
    ".ai/experience/sensor-feedback.md",
    ".ai/experience/team-preferences.md",
    ".ai/experience/deprecated-experience.md",
    ".ai/review/maturity-review.yaml",
    ".ai/review/asset-candidates.yaml",
    ".ai/review/workflow-routing-recommendation.yaml",
}


def maturity_evidence_source_allowlist(evidence_pack: MaturityEvidencePack) -> set[str]:
    allowed = set(CORE_EVIDENCE_SOURCES)
    allowed.update(evidence_pack.maturity_inputs)
    allowed.update(source.path for source in evidence_pack.experience.sources)
    return allowed


def review_evidence_source_allowlist(
    evidence_pack: MaturityEvidencePack,
    candidates: ImprovementCandidateReport | None = None,
    *,
    maturity_review: MaturityReviewReport | None = None,
    experience_summary: ExperienceSummaryReport | None = None,
) -> set[str]:
    allowed = maturity_evidence_source_allowlist(evidence_pack)
    if candidates is not None:
        allowed.update(source for candidate in candidates.candidates for source in candidate.evidence_sources)
    if maturity_review is not None:
        allowed.add(".ai/review/maturity-review.yaml")
        allowed.update(source for review in maturity_review.candidate_reviews for source in review.evidence_sources)
    if experience_summary is not None:
        allowed.add(".ai/experience/experience-summary.yaml")
        allowed.update(source for finding in experience_summary.findings for source in finding.evidence_sources)
    return allowed


def validate_evidence_sources(label: str, sources: Iterable[str], allowed_evidence_sources: set[str]) -> None:
    unique_sources = sorted(set(sources))
    bad_prefixes = [source for source in unique_sources if not source.startswith(".ai/")]
    if bad_prefixes:
        raise ValueError(f"{label} evidence_sources must be under .ai/: {', '.join(bad_prefixes)}")
    unknown = [source for source in unique_sources if source not in allowed_evidence_sources]
    if unknown:
        raise ValueError(f"{label} referenced unknown evidence_sources: {', '.join(unknown)}")


def unknown_evidence_sources(sources: Iterable[str], allowed_evidence_sources: set[str]) -> list[str]:
    return sorted({source for source in sources if source.startswith(".ai/") and source not in allowed_evidence_sources})
