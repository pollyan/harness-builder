from harness_builder.scanner.detectors.llm_hints import build_llm_hint_placeholder


def test_llm_hint_placeholder_is_separate_from_facts():
    hints = build_llm_hint_placeholder(["未识别到主技术栈"])

    assert hints["enabled"] is False
    assert hints["hints"][0]["type"] == "manual-calibration"
    assert hints["hints"][0]["confidence"] == "low"
    assert "evidence" in hints["hints"][0]
