from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateDraft, AssetCandidateReport
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.llm_asset_candidate_generator import generate_asset_candidates_with_llm
from harness_builder_agent.tools.review_maturity import review_maturity


def generate_asset_candidates(repo: Path) -> Path:
    root = repo.resolve()
    ai = root / ".ai"
    if not (ai / "maturity-score.yaml").exists() or not (ai / "maturity-evidence.yaml").exists():
        assess_maturity(root)
    if not (ai / "improvement-candidates.yaml").exists():
        generate_improvements(root)
    if not (ai / "review" / "maturity-review.yaml").exists():
        review_maturity(root)

    score = MaturityReport.model_validate(yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8")))
    evidence_pack = MaturityEvidencePack.model_validate(yaml.safe_load((ai / "maturity-evidence.yaml").read_text(encoding="utf-8")))
    improvement_candidates = ImprovementCandidateReport.model_validate(
        yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    )
    maturity_review = MaturityReviewReport.model_validate(
        yaml.safe_load((ai / "review" / "maturity-review.yaml").read_text(encoding="utf-8"))
    )
    report = generate_asset_candidates_with_llm(score, evidence_pack, improvement_candidates, maturity_review)
    review_dir = ai / "review"
    _write_yaml(review_dir / "asset-candidates.yaml", report.model_dump(mode="json"))
    _write_kind_markdown(review_dir / "asset-candidate-guides.md", "Asset Candidate Guides", report, "guide")
    _write_kind_markdown(review_dir / "asset-candidate-sensors.md", "Asset Candidate Sensors", report, "sensor")
    _write_kind_markdown(review_dir / "asset-candidate-workflows.md", "Asset Candidate Workflows", report, "workflow_policy")
    return ai


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_kind_markdown(path: Path, title: str, report: AssetCandidateReport, kind: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    items = [candidate for candidate in report.candidates if candidate.kind == kind]
    body = "\n\n".join(_candidate_markdown(candidate) for candidate in items) or "No candidates."
    path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")


def _candidate_markdown(candidate: AssetCandidateDraft) -> str:
    evidence = "\n".join(f"- {item}" for item in candidate.evidence_sources) or "- None."
    checks = "\n".join(f"- {item}" for item in candidate.acceptance_checks) or "- None."
    return (
        f"## {candidate.title}\n\n"
        f"- id: `{candidate.id}`\n"
        f"- source candidate: `{candidate.source_candidate_id or 'missing'}`\n"
        f"- suggested path: `{candidate.suggested_path}`\n"
        f"- review status: `{candidate.review_status}`\n"
        f"- risk level: `{candidate.risk_level}`\n\n"
        "### Rationale\n\n"
        f"{candidate.rationale}\n\n"
        "### Draft Content\n\n"
        f"{candidate.draft_content}\n\n"
        "### Evidence Sources\n\n"
        f"{evidence}\n\n"
        "### Acceptance Checks\n\n"
        f"{checks}"
    )
