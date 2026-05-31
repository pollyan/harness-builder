from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.schemas.self_improve_package import (
    SelfImproveCandidateCounts,
    SelfImproveGeneratedArtifact,
    SelfImproveMaturitySnapshot,
    SelfImprovePackageManifest,
)
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.generate_asset_candidates import generate_asset_candidates
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.review_maturity import review_maturity


def run_self_improve(repo: Path) -> Path:
    root = repo.resolve()
    ai = root / ".ai"
    assess_maturity(root)
    generate_improvements(root)
    review_maturity(root)
    generate_asset_candidates(root)
    assess_maturity(root)

    score = MaturityReport.model_validate(_read_yaml(ai / "maturity-score.yaml"))
    evidence = MaturityEvidencePack.model_validate(_read_yaml(ai / "maturity-evidence.yaml"))
    improvements = ImprovementCandidateReport.model_validate(_read_yaml(ai / "improvement-candidates.yaml"))
    maturity_review = MaturityReviewReport.model_validate(_read_yaml(ai / "review" / "maturity-review.yaml"))
    asset_candidates = AssetCandidateReport.model_validate(_read_yaml(ai / "review" / "asset-candidates.yaml"))

    manifest = SelfImprovePackageManifest(
        package_id="self-improve-package",
        generated_artifacts=_generated_artifacts(ai),
        candidate_counts=_candidate_counts(improvements, maturity_review, asset_candidates),
        maturity=SelfImproveMaturitySnapshot(
            overall_level=score.overall_level,
            target_next_level=score.target_next_level,
            dimension_scores=score.dimension_scores,
        ),
        next_actions=[
            "Review `.ai/review/maturity-review.yaml` before trusting candidate priority.",
            "Review `.ai/review/asset-candidates.yaml` before applying any formal Harness asset change.",
            "Run `harness-builder-agent benchmark --repo <repo>` after any reviewed Harness change.",
        ],
        warnings=evidence.warnings,
    )

    review_dir = ai / "review"
    _write_yaml(review_dir / "self-improve-package.yaml", manifest.model_dump(mode="json"))
    _write_markdown(review_dir / "self-improve-package.md", manifest)
    return ai


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _generated_artifacts(ai: Path) -> list[SelfImproveGeneratedArtifact]:
    relative_paths = [
        ".ai/maturity-score.yaml",
        ".ai/maturity-evidence.yaml",
        ".ai/improvement-candidates.yaml",
        ".ai/evolution-plan.md",
        ".ai/experience/pending-improvements.md",
        ".ai/experience/experience-index.yaml",
        ".ai/review/maturity-review.yaml",
        ".ai/review/maturity-review.md",
        ".ai/review/asset-candidates.yaml",
        ".ai/review/asset-candidate-guides.md",
        ".ai/review/asset-candidate-sensors.md",
        ".ai/review/asset-candidate-workflows.md",
        ".ai/review/self-improve-package.yaml",
        ".ai/review/self-improve-package.md",
    ]
    artifacts: list[SelfImproveGeneratedArtifact] = []
    for relative_path in relative_paths:
        if (ai.parent / relative_path).exists() or relative_path.endswith("self-improve-package.yaml") or relative_path.endswith(
            "self-improve-package.md"
        ):
            artifacts.append(SelfImproveGeneratedArtifact(path=relative_path, kind=_artifact_kind(relative_path)))
    return artifacts


def _artifact_kind(path: str) -> str:
    if path.endswith("maturity-score.yaml"):
        return "maturity_score"
    if path.endswith("maturity-evidence.yaml"):
        return "maturity_evidence"
    if path.endswith("improvement-candidates.yaml"):
        return "improvement_candidates"
    if path.endswith("maturity-review.yaml"):
        return "maturity_review"
    if path.endswith("asset-candidates.yaml"):
        return "asset_candidates"
    if path.endswith("self-improve-package.yaml"):
        return "self_improve_package"
    if path.endswith(".md"):
        return "review"
    return "experience"


def _candidate_counts(
    improvements: ImprovementCandidateReport,
    maturity_review: MaturityReviewReport,
    asset_candidates: AssetCandidateReport,
) -> SelfImproveCandidateCounts:
    return SelfImproveCandidateCounts(
        improvement_candidates=len(improvements.candidates),
        maturity_reviews=len(maturity_review.candidate_reviews),
        asset_candidates=len(asset_candidates.candidates),
        guide_candidates=sum(1 for candidate in asset_candidates.candidates if candidate.kind == "guide"),
        sensor_candidates=sum(1 for candidate in asset_candidates.candidates if candidate.kind == "sensor"),
        workflow_policy_candidates=sum(1 for candidate in asset_candidates.candidates if candidate.kind == "workflow_policy"),
    )


def _write_markdown(path: Path, manifest: SelfImprovePackageManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    artifacts = "\n".join(f"- `{artifact.path}` ({artifact.kind})" for artifact in manifest.generated_artifacts) or "- None."
    warnings = "\n".join(f"- {warning}" for warning in manifest.warnings) or "- None."
    next_actions = "\n".join(f"- {action}" for action in manifest.next_actions) or "- None."
    dimensions = "\n".join(
        f"- `{name}`: `{level}`" for name, level in sorted(manifest.maturity.dimension_scores.items())
    ) or "- None."
    counts = manifest.candidate_counts
    path.write_text(
        "# Self-Improve Package\n\n"
        "## Maturity Snapshot\n\n"
        f"- overall level: `{manifest.maturity.overall_level}`\n"
        f"- target next level: `{manifest.maturity.target_next_level or 'unknown'}`\n\n"
        f"{dimensions}\n\n"
        "## Generated Artifacts\n\n"
        f"{artifacts}\n\n"
        "## Candidate Counts\n\n"
        f"- improvement candidates: {counts.improvement_candidates}\n"
        f"- maturity reviews: {counts.maturity_reviews}\n"
        f"- asset candidates: {counts.asset_candidates}\n"
        f"- guide candidates: {counts.guide_candidates}\n"
        f"- sensor candidates: {counts.sensor_candidates}\n"
        f"- workflow policy candidates: {counts.workflow_policy_candidates}\n\n"
        "## Next Actions\n\n"
        f"{next_actions}\n\n"
        "## Warnings\n\n"
        f"{warnings}\n\n"
        "## Review Boundary\n\n"
        f"- review status: `{manifest.review_status}`\n"
        "- This package is review-only and does not apply formal Guide, Sensor, Workflow Skill, or routing policy changes.\n"
        "- Harness Builder does not execute Runtime workflows and does not create `.ai/task-runs`.\n",
        encoding="utf-8",
    )
