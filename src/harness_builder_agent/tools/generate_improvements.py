from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidate, ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.experience_index import write_experience_index


def generate_improvements(repo: Path) -> Path:
    root = repo.resolve()
    ai = root / ".ai"
    if not (ai / "maturity-score.yaml").exists() or not (ai / "maturity-evidence.yaml").exists():
        assess_maturity(root)

    score = MaturityReport.model_validate(yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8")))
    evidence_pack = MaturityEvidencePack.model_validate(yaml.safe_load((ai / "maturity-evidence.yaml").read_text(encoding="utf-8")))
    candidates = ImprovementCandidateReport(candidates=_candidates(score, evidence_pack))
    _write_yaml(ai / "improvement-candidates.yaml", candidates.model_dump(mode="json"))
    _write_evolution_plan(ai / "evolution-plan.md", candidates)
    _write_pending_improvements(ai / "experience" / "pending-improvements.md", candidates)
    write_experience_index(ai)
    return ai


def _candidates(score: MaturityReport, evidence_pack: MaturityEvidencePack) -> list[ImprovementCandidate]:
    candidates: list[ImprovementCandidate] = []
    seen: set[str] = set()
    for step in sorted(score.next_steps, key=_priority_rank):
        _append_unique(candidates, seen, _candidate_from_next_step(step, score, evidence_pack))
    for cap in score.blocking_caps:
        if cap.active:
            _append_unique(candidates, seen, _candidate_from_cap(cap, evidence_pack))
    for warning in evidence_pack.warnings:
        if "task-runs" in warning:
            _append_unique(candidates, seen, _runtime_evidence_candidate(warning, evidence_pack))
    if evidence_pack.experience.workflow_recommendation_count > 0:
        _append_unique(candidates, seen, _workflow_recommendation_review_candidate(evidence_pack))
    return candidates


def _priority_rank(step) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(step.priority, 3)


def _candidate_priority(priority: str) -> str:
    return "high" if priority in {"critical", "high"} else priority


def _append_unique(candidates: list[ImprovementCandidate], seen: set[str], candidate: ImprovementCandidate) -> None:
    if candidate.id not in seen:
        candidates.append(candidate)
        seen.add(candidate.id)


def _candidate_from_next_step(step, score: MaturityReport, evidence_pack: MaturityEvidencePack) -> ImprovementCandidate:
    dimension = step.target_dimension
    return ImprovementCandidate(
        id=f"maturity-next-step-{step.id}",
        candidate_type=_candidate_type_for_dimension(dimension),
        suggested_target=_target_for_dimension(dimension),
        rationale=f"{step.action} Expected maturity lift: {step.expected_lift or 'not specified'}.",
        evidence=_dimension_evidence(score, dimension) + evidence_pack.warnings,
        confidence="medium",
        priority=_candidate_priority(step.priority),
        target_dimension=dimension,
        source_next_step=step.id,
        acceptance_checks=_acceptance_checks(dimension),
        evidence_sources=_evidence_sources(evidence_pack),
    )


def _candidate_from_cap(cap, evidence_pack: MaturityEvidencePack) -> ImprovementCandidate:
    dimension = _dimension_for_cap(cap.id)
    return ImprovementCandidate(
        id=f"maturity-blocking-cap-{cap.id}",
        candidate_type=_candidate_type_for_dimension(dimension),
        suggested_target=_target_for_dimension(dimension),
        rationale=f"Active maturity cap `{cap.id}` limits the harness to {cap.max_level}: {cap.reason}",
        evidence=cap.evidence or evidence_pack.warnings,
        confidence="medium",
        priority="high",
        target_dimension=dimension,
        source_blocking_cap=cap.id,
        acceptance_checks=_acceptance_checks(dimension),
        evidence_sources=_evidence_sources(evidence_pack),
    )


def _runtime_evidence_candidate(warning: str, evidence_pack: MaturityEvidencePack) -> ImprovementCandidate:
    return ImprovementCandidate(
        id="maturity-evidence-runtime-task-runs",
        candidate_type="maturity_action",
        suggested_target=".ai/task-runs/",
        rationale="Runtime task-run evidence is absent, so maturity cannot use task execution outcomes yet.",
        evidence=[warning],
        confidence="medium",
        priority="medium",
        target_dimension="observability",
        source_blocking_cap="runtime-audit-not-owned-by-builder",
        acceptance_checks=_acceptance_checks("observability"),
        evidence_sources=_evidence_sources(evidence_pack),
    )


def _workflow_recommendation_review_candidate(evidence_pack: MaturityEvidencePack) -> ImprovementCandidate:
    count = evidence_pack.experience.workflow_recommendation_count
    return ImprovementCandidate(
        id="experience-workflow-recommendation-review",
        candidate_type="workflow_policy_update",
        suggested_target=".ai/harness-config.yaml",
        rationale=(
            "Workflow recommendation review evidence exists; inspect whether routing policy should be adjusted "
            "or whether current rules already cover the recommendation."
        ),
        evidence=[
            f"Workflow recommendation reviews: {count}.",
            "Recommendation artifacts are review-only and must not be treated as applied routing changes.",
        ],
        confidence="medium",
        priority="medium",
        target_dimension="workflow",
        acceptance_checks=[
            "Candidate remains pending review before formal workflow assets are changed.",
            "Benchmark content:workflow-recommendation-review passes when recommendation artifacts are present.",
            "Benchmark content:workflow-routing-policy passes after any reviewed routing policy change.",
        ],
        evidence_sources=_evidence_sources(evidence_pack),
    )


def _candidate_type_for_dimension(dimension: str) -> str:
    if dimension == "guides":
        return "guide_update"
    if dimension in {"sensors", "verification_sophistication"}:
        return "sensor_update"
    if dimension in {"workflow", "repair_loop", "risk_control"}:
        return "workflow_policy_update"
    return "maturity_action"


def _target_for_dimension(dimension: str) -> str:
    return {
        "guides": ".ai/guides/project-context.md",
        "sensors": ".ai/sensors/verification.md",
        "verification_sophistication": ".ai/sensors/verification.md",
        "workflow": ".ai/harness-config.yaml",
        "repair_loop": ".ai/skills/bugfix/SKILL.md",
        "risk_control": ".ai/harness-config.yaml",
        "experience": ".ai/experience/pending-improvements.md",
        "observability": ".ai/runs/",
        "governance_auditability": ".ai/runs/",
    }.get(dimension, ".ai/maturity-report.md")


def _acceptance_checks(dimension: str) -> list[str]:
    base = [f"Candidate remains pending review before formal {dimension} assets are changed."]
    if dimension == "guides":
        return base + ["Benchmark content:guides-quality passes."]
    if dimension in {"sensors", "verification_sophistication"}:
        return base + ["Benchmark content:sensors-quality and content:hard-gate-command-evidence pass."]
    if dimension in {"workflow", "repair_loop", "risk_control"}:
        return base + ["Benchmark content:workflow-skill-config-reference passes."]
    if dimension in {"observability", "governance_auditability"}:
        return base + ["Generation trace and maturity evidence remain schema-valid."]
    return base + ["maturity-score.yaml and maturity-evidence.yaml remain schema-valid."]


def _dimension_evidence(score: MaturityReport, dimension: str) -> list[str]:
    report = score.dimensions.get(dimension)
    if not report:
        return score.evidence
    evidence = [f"{item.source}: {item.summary}" for item in report.evidence]
    blockers = [blocker.reason for blocker in report.blockers]
    return evidence + blockers


def _dimension_for_cap(cap_id: str) -> str:
    if "sensor" in cap_id or "executable" in cap_id:
        return "sensors"
    if "runtime" in cap_id or "audit" in cap_id or "trace" in cap_id:
        return "observability"
    if "experience" in cap_id:
        return "experience"
    return "workflow"


def _evidence_sources(evidence_pack: MaturityEvidencePack) -> list[str]:
    return [".ai/maturity-evidence.yaml", *evidence_pack.maturity_inputs]


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_evolution_plan(path: Path, report: ImprovementCandidateReport) -> None:
    lines = "\n".join(
        f"- `{item.id}`：{item.rationale}（目标：`{item.suggested_target}`）\n"
        f"  - Maturity dimension: `{item.target_dimension or 'unknown'}`\n"
        f"  - Acceptance checks: {'; '.join(item.acceptance_checks) or 'none'}"
        for item in report.candidates
    )
    path.write_text(
        "# 演进计划\n\n"
        "## 优先级路线图\n\n"
        f"{lines}\n\n"
        "## 生效规则\n\n"
        "- 这些候选项只进入待确认状态，不自动修改正式 Guides / Sensors / Workflow。\n",
        encoding="utf-8",
    )


def _write_pending_improvements(path: Path, report: ImprovementCandidateReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = "\n".join(
        f"- `{item.id}`：{item.rationale}\n"
        f"  - Maturity dimension: `{item.target_dimension or 'unknown'}`\n"
        f"  - Acceptance checks: {'; '.join(item.acceptance_checks) or 'none'}"
        for item in report.candidates
    )
    path.write_text(
        "# Pending Improvements\n\n"
        "## 待确认改进候选\n\n"
        f"{lines}\n",
        encoding="utf-8",
    )
