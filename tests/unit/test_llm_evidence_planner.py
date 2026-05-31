from __future__ import annotations

import json

import pytest

from harness_builder_agent.schemas.scan import EvidenceBundle, EvidenceFile
from harness_builder_agent.tools.llm_evidence_planner import (
    build_evidence_plan_messages,
    parse_llm_evidence_plan_response,
    plan_evidence_expansion_with_llm,
)


def _bundle() -> EvidenceBundle:
    return EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[
            EvidenceFile(path="pom.xml", kind="file"),
            EvidenceFile(path="src/checkout/RefundService.java", kind="file"),
        ],
    )


def _plan_json() -> str:
    return json.dumps(
        {
            "schema_version": "1.0",
            "requested_paths": ["src/checkout/RefundService.java"],
            "risk_focus": ["checkout refund flow"],
            "rationale": "The source index suggests checkout logic deserves deeper inspection.",
            "confidence": "high",
        }
    )


def test_parse_llm_evidence_plan_accepts_json_fence():
    plan = parse_llm_evidence_plan_response(f"```json\n{_plan_json()}\n```", {"pom.xml", "src/checkout/RefundService.java"})

    assert plan.requested_paths == ["src/checkout/RefundService.java"]
    assert plan.confidence == "high"


def test_parse_llm_evidence_plan_rejects_bad_json():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_llm_evidence_plan_response("not json", {"pom.xml"})


def test_parse_llm_evidence_plan_rejects_schema_mismatch():
    with pytest.raises(ValueError, match="schema"):
        parse_llm_evidence_plan_response('{"requested_paths": "pom.xml"}', {"pom.xml"})


def test_parse_llm_evidence_plan_rejects_path_outside_repo():
    payload = json.loads(_plan_json())
    payload["requested_paths"] = ["../secret.txt"]

    with pytest.raises(ValueError, match="outside repository"):
        parse_llm_evidence_plan_response(json.dumps(payload), {"pom.xml"})


def test_parse_llm_evidence_plan_rejects_unknown_path():
    payload = json.loads(_plan_json())
    payload["requested_paths"] = ["src/unknown/Hidden.java"]

    with pytest.raises(ValueError, match="unknown evidence path"):
        parse_llm_evidence_plan_response(json.dumps(payload), {"pom.xml"})


def test_build_evidence_plan_messages_uses_registered_prompt_asset():
    messages = build_evidence_plan_messages(_bundle())
    combined = "\n".join(message["content"] for message in messages)

    assert [message["role"] for message in messages] == ["system", "user"]
    assert "Evidence planning input JSON" in combined
    assert "requested_paths" in combined
    assert "逐字复制某一个 `files[].path` 字符串" in combined
    assert "src/checkout/RefundService.java" in combined


def test_evidence_plan_prompt_explains_full_manifest_semantics_and_coverage_gap():
    bundle = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[
            EvidenceFile(
                path="src/ordinary.py",
                kind="file",
                bucket="source:.py",
                priority="medium",
                reason="Representative .py source sample.",
            ),
            EvidenceFile(
                path="src/auth/AuthService.py",
                kind="file",
                bucket="risk",
                priority="high",
                reason="Security, auth, database, or migration risk area.",
            ),
        ],
        source_samples=[
            EvidenceFile(
                path="src/ordinary.py",
                kind="source",
                bucket="source:.py",
                priority="medium",
                summary="print('ordinary')",
            ),
        ],
        coverage={
            "detected_file_count": 2,
            "selected_evidence_count": 1,
            "bucket_coverage": [
                {
                    "bucket": "source:.py",
                    "total_count": 2,
                    "selected_count": 1,
                    "skipped_count": 1,
                    "selected_paths": ["src/ordinary.py"],
                }
            ],
            "warnings": [
                {
                    "code": "source_sampling_truncated",
                    "bucket": "source:.py",
                    "total_count": 2,
                    "selected_count": 1,
                    "skipped_count": 1,
                    "message": "source:.py skipped 1 files",
                }
            ],
        },
    )

    combined = "\n".join(message["content"] for message in build_evidence_plan_messages(bundle))

    assert "全量轻量 file manifest" in combined
    assert "bucket / priority / reason" in combined
    assert "coverage warnings" in combined
    assert "未进入初始摘要" in combined
    assert "src/auth/AuthService.py" in combined
    assert '"bucket": "risk"' in combined
    assert '"priority": "high"' in combined


def test_plan_evidence_expansion_with_llm_rejects_empty_response():
    def caller(_messages):
        return ""

    with pytest.raises(ValueError, match="empty"):
        plan_evidence_expansion_with_llm(_bundle(), caller=caller)


def test_plan_evidence_expansion_retries_once_on_allowlist_validation_error():
    responses = iter(
        [
            json.dumps(
                {
                    "schema_version": "1.0",
                    "requested_paths": ["src/checkout/FakeRefundService.java"],
                    "risk_focus": ["checkout refund flow"],
                    "rationale": "I inferred a path that is not in the provided index.",
                    "confidence": "medium",
                }
            ),
            _plan_json(),
        ]
    )
    calls: list[list[dict[str, str]]] = []

    def caller(messages):
        calls.append(messages)
        return next(responses)

    plan = plan_evidence_expansion_with_llm(_bundle(), caller=caller)

    assert plan.requested_paths == ["src/checkout/RefundService.java"]
    assert len(calls) == 2
    retry_content = calls[1][-1]["content"]
    assert "上一次 evidence plan 响应未通过契约校验" in retry_content
    assert "DeepSeek evidence plan requested unknown evidence path" in retry_content
    assert "只能从 files[].path 中逐字复制路径" in retry_content
