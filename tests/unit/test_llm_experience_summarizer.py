import json
from pathlib import Path

import pytest
import yaml

from harness_builder_agent.schemas.experience_index import ExperienceIndex, ExperienceSource
from harness_builder_agent.tools.summarize_experience import _collect_sources
from harness_builder_agent.tools.llm_experience_summarizer import (
    build_experience_summary_messages,
    parse_experience_summary_response,
    summarize_experience_with_llm,
)


def _index() -> ExperienceIndex:
    return ExperienceIndex(
        experience_files={"pending-improvements.md": True},
        sources=[
            ExperienceSource(path=".ai/experience/pending-improvements.md", kind="pending_improvements", item_count=1),
            ExperienceSource(path=".ai/review/maturity-review.yaml", kind="maturity_review", item_count=1),
            ExperienceSource(path=".ai/review/asset-candidates.yaml", kind="asset_candidates", item_count=1),
            ExperienceSource(
                path=".ai/review/workflow-routing-recommendation.yaml",
                kind="workflow_recommendation",
                item_count=1,
            ),
        ],
        pending_improvement_count=1,
        asset_candidate_count=1,
        maturity_review_count=1,
        workflow_recommendation_count=1,
        runtime_task_run_count=0,
    )


def _sources() -> dict[str, str]:
    return {
        ".ai/experience/pending-improvements.md": "- missing sensor coverage",
        ".ai/review/maturity-review.yaml": "summary: revise sensor candidate",
        ".ai/review/workflow-routing-recommendation.yaml": "recommended_workflow: bugfix",
    }


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_runtime_task_run(ai: Path) -> None:
    run = ai / "task-runs" / "task-1"
    _write_yaml(
        run / "harness-map.yaml",
        {"schema_version": "1.0", "task_id": "task-1", "task_type": "bugfix", "selected_workflow": "bugfix"},
    )
    _write_yaml(
        run / "sensor-report.yaml",
        {
            "schema_version": "1.0",
            "task_id": "task-1",
            "task": "Fix checkout bug",
            "sensor_results": [
                {
                    "id": "pytest",
                    "command": "pytest",
                    "status": "failed",
                    "exit_code": 1,
                    "duration_seconds": 2.5,
                    "summary": "pytest failed",
                }
            ],
        },
    )
    _write_yaml(
        run / "runtime-summary.yaml",
        {
            "schema_version": "1.0",
            "task_id": "task-1",
            "selected_workflow": "bugfix",
            "status": "completed_with_sensor_failures",
            "sensor_status": "failed",
            "repair_attempts": 1,
            "unresolved_sensor_count": 1,
            "risk_count": 1,
            "summary": "Runtime captured a failed sensor.",
        },
    )
    (run / "decision-log.md").write_text("# Decision Log\n\nRetried pytest once.\n", encoding="utf-8")
    (run / "handoff-summary.md").write_text("# Handoff Summary\n\nPytest still fails.\n", encoding="utf-8")


def test_collect_sources_includes_runtime_sensor_and_handoff_details(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_runtime_task_run(ai)

    sources = _collect_sources(tmp_path)

    runtime_source = sources[".ai/task-runs/task-1/"]
    assert "sensor failed" in runtime_source
    assert "pytest failed" in runtime_source
    assert "Pytest still fails." in runtime_source


def test_summarize_experience_with_llm_returns_schema_valid_summary():
    def caller(messages):
        assert "experience_index" in messages[-1]["content"]
        return json.dumps(
            {
                "summary": "Sensor coverage is the main repeated issue.",
                "findings": [
                    {
                        "id": "sensor-coverage-gap",
                        "kind": "sensor_feedback",
                        "title": "Sensor coverage gap",
                        "summary": "Pending improvements and review both mention sensor coverage.",
                        "evidence_sources": [".ai/experience/pending-improvements.md"],
                        "confidence": "high",
                        "suggested_follow_up": "Draft a reviewed sensor candidate.",
                    }
                ],
            }
        )

    report = summarize_experience_with_llm(_index(), _sources(), caller=caller)

    assert report.review_status == "pending_harness_maintainer_review"
    assert report.findings[0].kind == "sensor_feedback"


def test_parse_experience_summary_response_rejects_invalid_json():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_experience_summary_response("not json", set(_sources()))


def test_parse_experience_summary_response_rejects_non_ai_evidence_path():
    with pytest.raises(ValueError, match="under .ai/"):
        parse_experience_summary_response(
            json.dumps(
                {
                    "summary": "Bad path.",
                    "findings": [
                        {
                            "id": "bad",
                            "kind": "risk_signal",
                            "title": "Bad",
                            "summary": "Bad.",
                            "evidence_sources": ["README.md"],
                        }
                    ],
                }
            ),
            set(_sources()),
        )


def test_parse_experience_summary_response_rejects_unknown_evidence_source():
    with pytest.raises(ValueError, match="unknown evidence_sources"):
        parse_experience_summary_response(
            json.dumps(
                {
                    "summary": "Unknown source.",
                    "findings": [
                        {
                            "id": "unknown",
                            "kind": "risk_signal",
                            "title": "Unknown",
                            "summary": "Unknown.",
                            "evidence_sources": [".ai/experience/missing.md"],
                        }
                    ],
                }
            ),
            set(_sources()),
        )


def test_build_experience_summary_messages_includes_review_only_boundary():
    messages = build_experience_summary_messages(_index(), _sources())
    content = messages[-1]["content"]
    assert "Return one JSON object only" in content
    assert "Do not modify formal Guides" in content
    assert "workflow-routing-recommendation.yaml" in content


def test_build_experience_summary_messages_guides_source_index_details():
    messages = build_experience_summary_messages(_index(), _sources())

    content = messages[-1]["content"]
    assert "experience_index.sources" in content
    assert "path, kind, and item_count" in content
    assert ".ai/review/workflow-routing-recommendation.yaml" in content
    assert "review-only source index" in content
    assert "Do not invent missing source paths" in content
