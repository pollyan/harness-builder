from __future__ import annotations

from pathlib import Path

from harness_builder_agent.schemas.command_catalog import CommandDefinition
from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire
from harness_builder_agent.tools.human_confirmation import build_questionnaire, read_context_inputs
from harness_builder_agent.tools.interaction_decisions import accepted_interactive_decisions


def test_read_context_inputs_summarizes_files(tmp_path: Path):
    context = tmp_path / "team-rules.md"
    context.write_text("团队规则" * 700, encoding="utf-8")

    payload = read_context_inputs([context])

    assert payload["schema_version"] == "1.0"
    assert payload["contexts"][0]["path"] == str(context)
    assert payload["contexts"][0]["size_bytes"] > 0
    assert payload["contexts"][0]["truncated"] is True
    assert len(payload["contexts"][0]["summary"]) <= 1200
    ContextInputs.model_validate(payload)


def test_build_questionnaire_includes_context_guides_sensors_and_warnings():
    questionnaire = build_questionnaire(
        context_inputs={"schema_version": "1.0", "contexts": []},
        scan_metadata={"warnings": [{"code": "command_without_evidence", "message": "Command downgraded"}]},
        risk_areas=[{"path": "docs/a.json", "reason": "可能包含明文 API key"}],
    )

    ids = {item["interaction_id"] for item in questionnaire["questions"]}
    assert {"confirm:team-context", "confirm:guide-candidates", "confirm:sensor-gates"}.issubset(ids)
    assert "confirm:scan-warning:command_without_evidence" in ids
    assert "confirm:high-risk:docs-a-json" in ids
    high_risk_question = next(
        item for item in questionnaire["questions"] if item["interaction_id"] == "confirm:high-risk:docs-a-json"
    )
    assert high_risk_question["interaction_type"] == "risk_area_confirmation"
    assert "docs/a.json" in high_risk_question["question"]
    assert "高风险" in high_risk_question["question"]
    assert "API key" in high_risk_question["reason"]
    Questionnaire.model_validate(questionnaire)


def test_build_questionnaire_includes_low_confidence_evidence_expansion():
    questionnaire = build_questionnaire(
        context_inputs={"schema_version": "1.0", "contexts": []},
        scan_metadata={
            "warnings": [],
            "evidence_expansion": {
                "requested_paths": ["src/auth/AuthService.py"],
                "risk_focus": ["auth flow"],
                "rationale": "Auth code was not sampled.",
                "confidence": "low",
                "read_paths": ["src/auth/AuthService.py"],
                "read_file_count": 1,
            },
        },
    )

    question = next(item for item in questionnaire["questions"] if item["interaction_id"] == "confirm:evidence-expansion")
    assert question["interaction_type"] == "evidence_expansion_confirmation"
    assert "src/auth/AuthService.py" in question["question"]
    assert "Auth code was not sampled." in question["reason"]
    Questionnaire.model_validate(questionnaire)


def test_build_questionnaire_includes_scan_followup_questions():
    questionnaire = build_questionnaire(
        context_inputs={"schema_version": "1.0", "contexts": []},
        scan_metadata={
            "warnings": [],
            "followup_questions": [
                {
                    "interaction_id": "confirm:scan-followup:coverage-source-java",
                    "trigger": "coverage_gap",
                    "question": "哪些 Java 目录、入口文件或高风险路径需要补充扫描？",
                    "reason": "source:.java 抽样不足，可能影响模块和风险判断。",
                    "evidence": ["source:.java"],
                    "confidence": "low",
                    "affects": ["maturity", "guides", "sensors"],
                }
            ],
        },
    )

    question = next(
        item for item in questionnaire["questions"] if item["interaction_id"] == "confirm:scan-followup:coverage-source-java"
    )
    assert question["interaction_type"] == "scan_followup_confirmation"
    assert "哪些 Java 目录" in question["question"]
    assert "maturity" in question["reason"]
    Questionnaire.model_validate(questionnaire)


def test_build_questionnaire_includes_scan_self_check_resolution():
    questionnaire = build_questionnaire(
        context_inputs={"schema_version": "1.0", "contexts": []},
        scan_metadata={
            "warnings": [],
            "followup_questions": [
                {
                    "interaction_id": "confirm:scan-followup:coverage-source-java",
                    "trigger": "coverage_gap",
                    "question": "哪些 Java 目录、入口文件或高风险路径需要补充扫描？",
                    "reason": "source:.java 抽样不足，可能影响模块和风险判断。",
                    "evidence": ["source:.java"],
                    "confidence": "low",
                    "affects": ["maturity", "guides", "sensors"],
                }
            ],
            "self_check": {
                "prompt_version": "llm-scan-self-check-v1",
                "review_status": "pending_harness_maintainer_review",
                "overall_risk": "medium",
                "summary": "仍需要人工确认源码覆盖。",
                "resolutions": [
                    {
                        "interaction_id": "confirm:scan-followup:coverage-source-java",
                        "trigger": "coverage_gap",
                        "status": "needs_targeted_scan",
                        "rationale": "当前 evidence 只有少量 Java 样本。",
                        "evidence_sources": ["source:.java"],
                        "suggested_next_action": "请补充核心 Java 模块路径。",
                        "confidence": "medium",
                    }
                ],
            },
        },
    )

    question = next(
        item for item in questionnaire["questions"] if item["interaction_id"] == "confirm:scan-followup:coverage-source-java"
    )
    assert "LLM 二次自检" in question["reason"]
    assert "needs_targeted_scan" in question["reason"]
    assert "请补充核心 Java 模块路径" in question["reason"]
    Questionnaire.model_validate(questionnaire)


def test_build_questionnaire_marks_followup_partially_addressed_by_scan_supplement():
    decisions = accepted_interactive_decisions(
        "/repo",
        scan_modules=[{"path": "src/main/java", "kind": "backend", "name": "core"}],
        scan_commands=[
            CommandDefinition(
                id="unit_test",
                command="mvn test",
                type="test",
                gate="hard",
                source="pom.xml",
                confidence="high",
            )
        ],
        scan_risk_areas=[{"path": "src/main/java/com/example/AuthService.java", "reason": "认证逻辑高风险"}],
    )

    questionnaire = build_questionnaire(
        context_inputs={"schema_version": "1.0", "contexts": []},
        scan_metadata={
            "warnings": [],
            "followup_questions": [
                {
                    "interaction_id": "confirm:scan-followup:test-evidence",
                    "trigger": "test_evidence_missing",
                    "question": "真实测试入口是什么？",
                    "reason": "缺少测试 evidence。",
                    "evidence": ["test_evidence_not_found"],
                    "confidence": "low",
                    "affects": ["sensors"],
                }
            ],
        },
        interaction_decisions=decisions,
    )

    question = next(
        item for item in questionnaire["questions"] if item["interaction_id"] == "confirm:scan-followup:test-evidence"
    )
    assert "本轮 scan 补充可能已部分回应该追问" in question["reason"]
    assert "command=unit_test:mvn test" in question["reason"]
    assert "review_status=pending_harness_maintainer_review" in question["reason"]
    Questionnaire.model_validate(questionnaire)


def test_build_questionnaire_does_not_mark_unrelated_followup_as_addressed():
    decisions = accepted_interactive_decisions(
        "/repo",
        scan_risk_areas=[{"path": "src/main/java/com/example/AuthService.java", "reason": "认证逻辑高风险"}],
    )

    questionnaire = build_questionnaire(
        context_inputs={"schema_version": "1.0", "contexts": []},
        scan_metadata={
            "warnings": [],
            "followup_questions": [
                {
                    "interaction_id": "confirm:scan-followup:test-evidence",
                    "trigger": "test_evidence_missing",
                    "question": "真实测试入口是什么？",
                    "reason": "缺少测试 evidence。",
                    "evidence": ["test_evidence_not_found"],
                    "confidence": "low",
                    "affects": ["sensors"],
                }
            ],
        },
        interaction_decisions=decisions,
    )

    question = next(
        item for item in questionnaire["questions"] if item["interaction_id"] == "confirm:scan-followup:test-evidence"
    )
    assert "本轮 scan 补充可能已部分回应该追问" not in question["reason"]
    Questionnaire.model_validate(questionnaire)


def test_build_questionnaire_skips_raw_warnings_represented_by_targeted_followups():
    questionnaire = build_questionnaire(
        context_inputs={"schema_version": "1.0", "contexts": []},
        scan_metadata={
            "warnings": [
                {"code": "source_sampling_truncated", "message": "source:.java skipped files"},
                {"code": "test_evidence_not_found", "message": "No dedicated test evidence bucket was found."},
                {"code": "llm_stack_claim_without_evidence", "message": "node claim is unsupported."},
                {"code": "llm_evidence_plan_low_confidence", "message": "planner low confidence."},
            ],
            "evidence_expansion": {
                "requested_paths": [],
                "risk_focus": ["unclear modules"],
                "rationale": "Planner could not identify enough source evidence.",
                "confidence": "low",
                "read_paths": [],
                "read_file_count": 0,
            },
            "followup_questions": [
                {
                    "interaction_id": "confirm:scan-followup:coverage-source-java",
                    "trigger": "coverage_gap",
                    "question": "哪些 Java 目录需要补充扫描？",
                    "reason": "source:.java 抽样不足。",
                    "confidence": "low",
                    "affects": ["maturity", "guides"],
                },
                {
                    "interaction_id": "confirm:scan-followup:test-evidence",
                    "trigger": "test_evidence_missing",
                    "question": "真实测试入口是什么？",
                    "reason": "缺少测试 evidence。",
                    "confidence": "low",
                    "affects": ["sensors"],
                },
                {
                    "interaction_id": "confirm:scan-followup:stack-node",
                    "trigger": "stack_claim_without_evidence",
                    "question": "是否存在 Node 子模块？",
                    "reason": "node claim 缺少 evidence。",
                    "confidence": "low",
                    "affects": ["workflow"],
                },
            ],
        },
    )

    ids = {item["interaction_id"] for item in questionnaire["questions"]}
    assert "confirm:scan-followup:coverage-source-java" in ids
    assert "confirm:scan-followup:test-evidence" in ids
    assert "confirm:scan-followup:stack-node" in ids
    assert "confirm:evidence-expansion" in ids
    assert "confirm:scan-warning:source_sampling_truncated" not in ids
    assert "confirm:scan-warning:test_evidence_not_found" not in ids
    assert "confirm:scan-warning:llm_stack_claim_without_evidence" not in ids
    assert "confirm:scan-warning:llm_evidence_plan_low_confidence" not in ids
