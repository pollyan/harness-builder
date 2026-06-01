from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateDraft
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools.existing_harness_action_summaries import (
    asset_candidate_apply_preview,
    asset_candidate_detail,
    benchmark_summary,
    candidate_governance_summary,
    human_input_governance_summary,
    self_improve_summary,
    top_improvement_candidate,
    workflow_recommendation_summary,
)


def test_existing_harness_action_summaries_render_benchmark_and_workflow_results():
    benchmark = BenchmarkReport.model_validate(
        {
            "repo_name": "demo",
            "profile": "java-spring",
            "status": "failed",
            "quality_status": "degraded",
            "checks": [
                {"id": "schema:project-inventory", "passed": True},
                {"id": "content:hard-gate-command-evidence", "passed": False},
            ],
        }
    )
    recommendation = WorkflowRecommendationReport(
        task_id="task-1",
        task_brief="Fix checkout permission bug.",
        recommended_workflow="bugfix",
        risk_level="medium",
        confidence="high",
        rationale="Bugfix intent matches routing.",
        human_confirmation_required=False,
    )

    benchmark_text = benchmark_summary(benchmark)
    workflow_text = workflow_recommendation_summary(recommendation)

    assert "Benchmark 未通过。" in benchmark_text
    assert "- checks=1/2" in benchmark_text
    assert "- failed_checks=1" in benchmark_text
    assert "- `content:hard-gate-command-evidence`" in benchmark_text
    assert "工作流推荐已生成。" in workflow_text
    assert "- recommended_workflow=bugfix" in workflow_text
    assert "- review_status=pending_harness_maintainer_review" in workflow_text


def test_existing_harness_action_summaries_render_candidate_preview(tmp_path: Path):
    repo = tmp_path / "repo"
    target = repo / ".ai" / "guides" / "project-context.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Project Context\n", encoding="utf-8")
    candidate = AssetCandidateDraft(
        id="guide-project-context-scope",
        kind="guide",
        source_review_decision="support",
        suggested_path=".ai/guides/project-context.md",
        title="Scope project context guide",
        rationale="Candidate is grounded in maturity evidence.",
        draft_content="## Candidate Addition\n\nAdd task loading scope.",
        evidence_sources=[".ai/maturity-evidence.yaml"],
        acceptance_checks=["Benchmark content:guides-quality passes."],
        risk_level="medium",
    )

    detail = asset_candidate_detail(candidate)
    preview = asset_candidate_apply_preview(repo, candidate)

    assert "候选详情" in detail
    assert "- id=guide-project-context-scope" in detail
    assert "- evidence_sources=`.ai/maturity-evidence.yaml`" in detail
    assert "- apply_boundary=single_candidate_only" in detail
    assert "应用预览" in preview
    assert "- apply_preview=available" in preview
    assert "- target_exists=true" in preview
    assert "- duplicate_marker=absent" in preview
    assert "+<!-- harness-builder:candidate-applied id=guide-project-context-scope -->" in preview
    assert "+## Applied Candidate: Scope project context guide" in preview
    assert "+Add task loading scope." in preview


def test_existing_harness_action_summaries_render_governance_and_self_improve():
    manifest = SelfImprovePackageManifest.model_validate(
        {
            "package_id": "self-improve-package",
            "maturity": {"overall_level": "L2", "target_next_level": "L3"},
            "candidate_counts": {
                "improvement_candidates": 2,
                "maturity_reviews": 1,
                "asset_candidates": 3,
            },
        }
    )

    candidate_text = candidate_governance_summary(
        "guide-project-context-scope",
        "applied",
        "lead-reviewer",
        1,
    )
    human_input_text = human_input_governance_summary(
        "confirm:scan-followup:test-evidence",
        "resolved",
        "lead-reviewer",
        "reviewed_resolved_by_harness_maintainer",
    )
    self_improve_text = self_improve_summary(manifest)

    assert "候选治理决策已记录。" in candidate_text
    assert "- applied_paths=1" in candidate_text
    assert "human-input 治理决策已记录。" in human_input_text
    assert "- new_response_status=reviewed_resolved_by_harness_maintainer" in human_input_text
    assert "自改进审查包已生成。" in self_improve_text
    assert "- overall_level=L2" in self_improve_text
    assert "- asset_candidates=3" in self_improve_text


def test_existing_harness_action_summaries_render_top_improvement_candidate(tmp_path: Path):
    path = tmp_path / "improvement-candidates.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "candidates": [
                    {
                        "id": "low-priority",
                        "candidate_type": "guide_update",
                        "suggested_target": ".ai/guides/project-context.md",
                        "rationale": "Low priority.",
                        "priority": "low",
                        "target_dimension": "Guides",
                    },
                    {
                        "id": "high-priority",
                        "candidate_type": "sensor_update",
                        "suggested_target": ".ai/sensors/verification.md",
                        "rationale": "High priority.",
                        "priority": "high",
                        "target_dimension": "Sensors",
                    },
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    assert (
        top_improvement_candidate(path)
        == "优先候选：`high-priority`（priority=high，dimension=Sensors，target=`.ai/sensors/verification.md`）"
    )
