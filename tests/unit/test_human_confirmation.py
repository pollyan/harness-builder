from __future__ import annotations

from pathlib import Path

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


def test_build_questionnaire_includes_context_guides_sensors_and_warnings():
    questionnaire = build_questionnaire(
        context_inputs={"schema_version": "1.0", "contexts": []},
        scan_metadata={"warnings": [{"code": "command_without_evidence", "message": "Command downgraded"}]},
    )

    ids = {item["interaction_id"] for item in questionnaire["questions"]}
    assert {"confirm:team-context", "confirm:guide-candidates", "confirm:sensor-gates"}.issubset(ids)
    assert "confirm:scan-warning:command_without_evidence" in ids

