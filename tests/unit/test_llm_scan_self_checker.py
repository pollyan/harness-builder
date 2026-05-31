from __future__ import annotations

import json

import pytest

from harness_builder_agent.schemas.scan import EvidenceBundle, EvidenceFile, ScanFollowupQuestion, ScanMetadata
from harness_builder_agent.tools.llm_scan_self_checker import (
    build_scan_self_check_messages,
    parse_scan_self_check_response,
    review_scan_followups_with_llm,
)


def _bundle() -> EvidenceBundle:
    return EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[
            EvidenceFile(path="pom.xml", kind="build"),
            EvidenceFile(path="src/App.java", kind="source"),
        ],
    )


def _metadata() -> ScanMetadata:
    return ScanMetadata(
        prompt_version="scan-v2",
        evidence_file_count=2,
        followup_questions=[
            ScanFollowupQuestion(
                interaction_id="confirm:scan-followup:coverage-source-java",
                trigger="coverage_gap",
                question="哪些 Java 目录、入口文件或高风险路径需要补充扫描？",
                reason="source:.java 抽样不足。",
                evidence=["source:.java", "src/App.java"],
                affects=["maturity", "guides", "sensors"],
            )
        ],
    )


def _self_check_json() -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "prompt_version": "llm-scan-self-check-v1",
            "review_status": "pending_harness_maintainer_review",
            "overall_risk": "medium",
            "summary": "Coverage gap needs targeted maintainer confirmation.",
            "resolutions": [
                {
                    "schema_version": "1.0",
                    "interaction_id": "confirm:scan-followup:coverage-source-java",
                    "trigger": "coverage_gap",
                    "status": "needs_targeted_scan",
                    "rationale": "Current evidence contains only a small Java source sample.",
                    "evidence_sources": ["source:.java", "src/App.java"],
                    "suggested_next_action": "Ask maintainer for core Java module paths before finalizing sensors.",
                    "confidence": "medium",
                }
            ],
        }
    )


def test_parse_scan_self_check_response_accepts_known_followups_and_sources():
    report = parse_scan_self_check_response(
        f"```json\n{_self_check_json()}\n```",
        allowed_interaction_ids={"confirm:scan-followup:coverage-source-java"},
        allowed_evidence_sources={"source:.java", "src/App.java"},
    )

    assert report.review_status == "pending_harness_maintainer_review"
    assert report.resolutions[0].status == "needs_targeted_scan"
    assert report.resolutions[0].evidence_sources == ["source:.java", "src/App.java"]


def test_parse_scan_self_check_response_rejects_unknown_interaction_id():
    payload = json.loads(_self_check_json())
    payload["resolutions"][0]["interaction_id"] = "confirm:scan-followup:unknown"

    with pytest.raises(ValueError, match="unknown interaction id"):
        parse_scan_self_check_response(
            json.dumps(payload),
            allowed_interaction_ids={"confirm:scan-followup:coverage-source-java"},
            allowed_evidence_sources={"source:.java", "src/App.java"},
        )


def test_parse_scan_self_check_response_rejects_unknown_evidence_source():
    payload = json.loads(_self_check_json())
    payload["resolutions"][0]["evidence_sources"] = ["src/Missing.java"]

    with pytest.raises(ValueError, match="unknown evidence source"):
        parse_scan_self_check_response(
            json.dumps(payload),
            allowed_interaction_ids={"confirm:scan-followup:coverage-source-java"},
            allowed_evidence_sources={"source:.java", "src/App.java"},
        )


def test_parse_scan_self_check_response_rejects_bad_json():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_scan_self_check_response(
            "not json",
            allowed_interaction_ids={"confirm:scan-followup:coverage-source-java"},
            allowed_evidence_sources={"source:.java"},
        )


def test_build_scan_self_check_messages_uses_registered_prompt():
    messages = build_scan_self_check_messages(_bundle(), _metadata())
    combined = "\n".join(message["content"] for message in messages)

    assert [message["role"] for message in messages] == ["system", "user"]
    assert "Scan follow-up self-check input JSON" in combined
    assert "pending_harness_maintainer_review" in combined
    assert "confirm:scan-followup:coverage-source-java" in combined
    assert "src/App.java" in combined


def test_review_scan_followups_with_llm_rejects_empty_response():
    def caller(_messages):
        return ""

    with pytest.raises(ValueError, match="empty"):
        review_scan_followups_with_llm(_bundle(), _metadata(), caller=caller)
