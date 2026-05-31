from __future__ import annotations

import json

import pytest

from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.tools.llm_workflow_router import (
    build_workflow_recommendation_messages,
    parse_workflow_recommendation_response,
    recommend_workflow_with_llm,
)


def _config() -> HarnessConfig:
    return HarnessConfig.default()


def _evidence_pack() -> MaturityEvidencePack:
    return MaturityEvidencePack(repo_name="demo", primary_stack="java-spring", maturity_inputs=[".ai/harness-config.yaml"])


def _valid_payload() -> dict:
    return {
        "schema_version": "1.0",
        "task_id": "task-1",
        "task_brief": "Fix checkout permission bug.",
        "recommended_workflow": "bugfix",
        "matched_rule_ids": ["bugfix-intent"],
        "risk_level": "medium",
        "confidence": "high",
        "rationale": "Bugfix intent matches the configured bugfix routing rule.",
        "required_guides": [".ai/guides/task-templates/bugfix.md"],
        "required_sensors": [".ai/sensors/verification.md"],
        "human_confirmation_required": False,
        "review_status": "pending_harness_maintainer_review",
        "evidence_sources": [".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
    }


def test_parse_workflow_recommendation_accepts_valid_response():
    report = parse_workflow_recommendation_response(
        json.dumps(_valid_payload()),
        configured_workflows={"lightweight", "bugfix", "standard"},
        routing_rule_ids={"bugfix-intent", "low-risk-lightweight", "standard-escalation"},
    )

    assert report.recommended_workflow == "bugfix"
    assert report.review_status == "pending_harness_maintainer_review"
    assert report.matched_rule_ids == ["bugfix-intent"]


def test_parse_workflow_recommendation_rejects_invalid_json():
    with pytest.raises(ValueError, match="must be valid JSON"):
        parse_workflow_recommendation_response(
            "not json",
            configured_workflows={"lightweight", "bugfix", "standard"},
            routing_rule_ids={"bugfix-intent"},
        )


def test_parse_workflow_recommendation_rejects_missing_explicit_review_status():
    payload = _valid_payload()
    payload.pop("review_status")

    with pytest.raises(ValueError, match="must include explicit keys: review_status"):
        parse_workflow_recommendation_response(
            json.dumps(payload),
            configured_workflows={"lightweight", "bugfix", "standard"},
            routing_rule_ids={"bugfix-intent"},
        )


def test_parse_workflow_recommendation_rejects_unknown_selected_workflow():
    payload = _valid_payload()
    payload["recommended_workflow"] = "prototype"

    with pytest.raises(ValueError, match="unknown recommended_workflow"):
        parse_workflow_recommendation_response(
            json.dumps(payload),
            configured_workflows={"lightweight", "bugfix", "standard"},
            routing_rule_ids={"bugfix-intent"},
        )


def test_parse_workflow_recommendation_rejects_unknown_routing_rule_id():
    payload = _valid_payload()
    payload["matched_rule_ids"] = ["missing-rule"]

    with pytest.raises(ValueError, match="unknown matched_rule_ids"):
        parse_workflow_recommendation_response(
            json.dumps(payload),
            configured_workflows={"lightweight", "bugfix", "standard"},
            routing_rule_ids={"bugfix-intent"},
        )


def test_parse_workflow_recommendation_rejects_non_ai_evidence_source():
    payload = _valid_payload()
    payload["evidence_sources"] = ["README.md"]

    with pytest.raises(ValueError, match="evidence_sources must be under .ai/"):
        parse_workflow_recommendation_response(
            json.dumps(payload),
            configured_workflows={"lightweight", "bugfix", "standard"},
            routing_rule_ids={"bugfix-intent"},
        )


def test_build_workflow_recommendation_messages_include_task_policy_and_review_boundary():
    messages = build_workflow_recommendation_messages(
        task_id="task-1",
        task_brief="Fix checkout permission bug.",
        config=_config(),
        evidence_pack=_evidence_pack(),
    )

    content = messages[-1]["content"]
    assert "Fix checkout permission bug." in content
    assert "workflow_routing" in content
    assert "bugfix-intent" in content
    assert "standard-escalation" in content
    assert "pending_harness_maintainer_review" in content
    assert "Do not execute the workflow" in content
    assert ".ai/task-runs" in content
    assert "The response object MUST include every top-level key" in content
    assert '"review_status": "pending_harness_maintainer_review"' in content


def test_recommend_workflow_with_llm_returns_schema_valid_recommendation():
    report = recommend_workflow_with_llm(
        task_id="task-1",
        task_brief="Fix checkout permission bug.",
        config=_config(),
        evidence_pack=_evidence_pack(),
        caller=lambda _messages: json.dumps(_valid_payload()),
    )

    assert report.task_id == "task-1"
    assert report.recommended_workflow == "bugfix"
