from __future__ import annotations

from pathlib import Path

from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire
from harness_builder_agent.tools.human_confirmation import build_questionnaire, read_context_inputs


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
