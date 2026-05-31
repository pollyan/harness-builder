import json

import pytest

from harness_builder_agent.schemas.experience_index import ExperienceIndex, ExperienceSource
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
