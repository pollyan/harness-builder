from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.llm_maturity_reviewer import review_maturity_with_llm


def review_maturity(repo: Path) -> Path:
    root = repo.resolve()
    ai = root / ".ai"
    if not (ai / "maturity-score.yaml").exists() or not (ai / "maturity-evidence.yaml").exists():
        assess_maturity(root)
    if not (ai / "improvement-candidates.yaml").exists():
        generate_improvements(root)

    score = MaturityReport.model_validate(yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8")))
    evidence_pack = MaturityEvidencePack.model_validate(yaml.safe_load((ai / "maturity-evidence.yaml").read_text(encoding="utf-8")))
    candidates = ImprovementCandidateReport.model_validate(
        yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    )
    review = review_maturity_with_llm(score, evidence_pack, candidates)
    _write_yaml(ai / "review" / "maturity-review.yaml", review.model_dump(mode="json"))
    _write_markdown(ai / "review" / "maturity-review.md", review)
    return ai


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_markdown(path: Path, review: MaturityReviewReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate_lines = "\n".join(
        f"- `{item.candidate_id}`: `{item.decision}` - {item.rationale}\n"
        f"  - risks: {'; '.join(item.risks) or 'none'}\n"
        f"  - acceptance: {'; '.join(item.suggested_acceptance_checks) or 'none'}"
        for item in review.candidate_reviews
    ) or "- No candidate reviews returned."
    missing = "\n".join(f"- {item}" for item in review.missing_candidates) or "- None."
    risks = "\n".join(f"- {item}" for item in review.global_risks) or "- None."
    path.write_text(
        "# Maturity Review\n\n"
        "## Summary\n\n"
        f"{review.summary}\n\n"
        "## Candidate Reviews\n\n"
        f"{candidate_lines}\n\n"
        "## Missing Candidates\n\n"
        f"{missing}\n\n"
        "## Global Risks\n\n"
        f"{risks}\n",
        encoding="utf-8",
    )
