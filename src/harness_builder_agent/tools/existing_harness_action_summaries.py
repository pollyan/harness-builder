from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport


def benchmark_summary(report: BenchmarkReport) -> str:
    failed_checks = [check for check in report.checks if not check.passed]
    passed_count = len(report.checks) - len(failed_checks)
    status_label = "已通过" if report.status == "passed" else "未通过"
    lines = [
        f"Benchmark {status_label}。",
        f"- status={report.status}",
        f"- quality={report.quality_status}",
        f"- checks={passed_count}/{len(report.checks)}",
        f"- failed_checks={len(failed_checks)}",
    ]
    if failed_checks:
        lines.append("- 失败项：")
        for check in failed_checks[:5]:
            lines.append(f"  - `{check.id}`")
        if len(failed_checks) > 5:
            lines.append(f"  - 还有 {len(failed_checks) - 5} 项，查看 `.ai/benchmark-report.yaml`。")
    lines.append("- `.ai/benchmark-report.yaml`")
    return "\n".join(lines)


def workflow_recommendation_summary(recommendation: WorkflowRecommendationReport) -> str:
    return "\n".join(
        [
            "工作流推荐已生成。",
            f"- recommended_workflow={recommendation.recommended_workflow}",
            f"- risk={recommendation.risk_level}",
            f"- confidence={recommendation.confidence}",
            f"- human_confirmation_required={recommendation.human_confirmation_required}",
            "- review_status=pending_harness_maintainer_review",
            "- `.ai/review/workflow-routing-recommendation.yaml`",
            "- `.ai/review/workflow-routing-recommendation.md`",
            "- `.ai/review/workflow-routing-recommendations/index.yaml`",
            "- `.ai/review/workflow-routing-recommendations.md`",
        ]
    )


def candidate_governance_summary(candidate_id: str, decision: str, reviewer: str, applied_path_count: int) -> str:
    return "\n".join(
        [
            "候选治理决策已记录。",
            f"- candidate_id={candidate_id}",
            f"- decision={decision}",
            f"- reviewer={reviewer}",
            f"- applied_paths={applied_path_count}",
            "- `.ai/review/candidate-governance.yaml`",
            "- `.ai/review/candidate-governance.md`",
            "- `.ai/experience/experience-index.yaml`",
        ]
    )


def human_input_governance_summary(interaction_id: str, decision: str, reviewer: str, new_response_status: str) -> str:
    return "\n".join(
        [
            "human-input 治理决策已记录。",
            f"- interaction_id={interaction_id}",
            f"- decision={decision}",
            f"- reviewer={reviewer}",
            f"- new_response_status={new_response_status}",
            "- `.ai/questionnaire.yaml`",
            "- `.ai/human-input-needed.md`",
            "- `.ai/review/human-input-governance.yaml`",
            "- `.ai/review/human-input-governance.md`",
        ]
    )


def weapon_candidate_governance_summary(candidate_id: str, decision: str, reviewer: str, new_status: str) -> str:
    return "\n".join(
        [
            "初始候选治理决策已记录。",
            f"- candidate_id={candidate_id}",
            f"- decision={decision}",
            f"- reviewer={reviewer}",
            f"- new_status={new_status}",
            "- formal_asset_changes=0",
            "- review_boundary=review_only_no_formal_asset_change",
            "- `.ai/experience/weapon-library-candidates.yaml`",
            "- `.ai/review/weapon-candidate-governance.yaml`",
            "- `.ai/review/weapon-candidate-governance.md`",
            "- `.ai/review/llm-enhancement-candidates.md`",
        ]
    )


def asset_candidate_detail(candidate) -> str:
    evidence = ", ".join(f"`{source}`" for source in candidate.evidence_sources) or "None."
    checks = "\n".join(f"  - {item}" for item in candidate.acceptance_checks) or "  - None."
    return "\n".join(
        [
            "\n候选详情",
            f"- id={candidate.id}",
            f"- kind={candidate.kind}",
            f"- title={candidate.title}",
            f"- target={candidate.suggested_path}",
            f"- risk={candidate.risk_level}",
            f"- review_status={candidate.review_status}",
            f"- evidence_sources={evidence}",
            "- acceptance_checks:",
            checks,
            "- apply_boundary=single_candidate_only",
        ]
    )


def asset_candidate_apply_preview(repo: Path, candidate) -> str:
    if candidate.kind == "workflow_policy":
        return "\n".join(
            [
                "\n应用预览",
                "- apply_preview=expert_command_required",
                f"- target={candidate.suggested_path}",
                "- guided_workflow_policy_apply=false",
                "- reason=workflow_policy candidates require the expert command with structured patch review.",
                "- source_report=.ai/review/asset-candidates.yaml",
            ]
        )

    if candidate.kind not in {"guide", "sensor"} or not candidate.suggested_path.startswith(".ai/"):
        return "\n".join(
            [
                "\n应用预览",
                "- apply_preview=unavailable",
                f"- target={candidate.suggested_path}",
                "- reason=guided apply only supports Guide / Sensor Markdown candidates under .ai/.",
                "- source_report=.ai/review/asset-candidates.yaml",
            ]
        )

    target = repo / candidate.suggested_path
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    marker = f"<!-- harness-builder:candidate-applied id={candidate.id} -->"
    heading = f"## Applied Candidate: {candidate.title}"
    diff_lines = candidate_append_diff_lines(candidate, marker, heading)
    return "\n".join(
        [
            "\n应用预览",
            "- apply_preview=available",
            f"- target={candidate.suggested_path}",
            "- apply_mode=append_markdown_candidate_block",
            f"- target_exists={str(target.exists()).lower()}",
            f"- duplicate_marker={'present' if marker in existing else 'absent'}",
            f"- block_heading={heading}",
            "- source_report=.ai/review/asset-candidates.yaml",
            "- diff_preview=unified_append",
            *diff_lines,
        ]
    )


def candidate_append_diff_lines(candidate, marker: str, heading: str) -> list[str]:
    block_lines = [
        marker,
        heading,
        "",
        f"Rationale: {candidate.rationale}",
        "",
        *candidate.draft_content.rstrip().splitlines(),
        "<!-- /harness-builder:candidate-applied -->",
    ]
    return [f"+{line}" if line else "+" for line in block_lines[:24]]


def self_improve_summary(manifest: SelfImprovePackageManifest) -> str:
    return "\n".join(
        [
            "自改进审查包已生成。",
            f"- overall_level={manifest.maturity.overall_level}",
            f"- target_next_level={manifest.maturity.target_next_level or 'unknown'}",
            f"- improvement_candidates={manifest.candidate_counts.improvement_candidates}",
            f"- maturity_reviews={manifest.candidate_counts.maturity_reviews}",
            f"- asset_candidates={manifest.candidate_counts.asset_candidates}",
            "- review_status=pending_harness_maintainer_review",
            "- `.ai/review/self-improve-package.yaml`",
            "- `.ai/review/self-improve-package.md`",
        ]
    )


def top_improvement_candidate(path: Path) -> str:
    report = ImprovementCandidateReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if not report.candidates:
        return "优先候选：暂无候选。"
    priority_order = {"high": 0, "medium": 1, "low": 2}
    candidate = sorted(report.candidates, key=lambda item: (priority_order.get(item.priority, 3), item.id))[0]
    return (
        f"优先候选：`{candidate.id}`"
        f"（priority={candidate.priority}，dimension={candidate.target_dimension or 'unknown'}，"
        f"target=`{candidate.suggested_target}`）"
    )
