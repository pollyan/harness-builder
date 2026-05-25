from harness_builder.scanner.detectors.llm_hints import build_llm_hint_placeholder


def test_llm_hint_placeholder_is_separate_from_facts():
    hints = build_llm_hint_placeholder(["未识别到主技术栈"])

    assert hints["enabled"] is False
    assert hints["hints"][0]["type"] == "manual-calibration"
    assert hints["hints"][0]["confidence"] == "low"
    assert "evidence" in hints["hints"][0]


def test_llm_hint_placeholder_empty_points():
    """No manual points → empty hints list."""
    hints = build_llm_hint_placeholder([])

    assert hints["hints"] == []


def test_llm_hint_placeholder_multiple_points():
    """Each manual point should produce one hint."""
    points = ["point a", "point b", "point c"]
    hints = build_llm_hint_placeholder(points)

    assert len(hints["hints"]) == 3
    assert hints["hints"][0]["message"] == "point a"
    assert hints["hints"][1]["message"] == "point b"
    assert hints["hints"][2]["message"] == "point c"


def test_llm_hint_placeholder_has_policy():
    """Policy string should always be present."""
    hints = build_llm_hint_placeholder([])

    assert "policy" in hints
    assert isinstance(hints["policy"], str)
    assert len(hints["policy"]) > 0


def test_llm_hint_placeholder_hint_structure():
    """Each hint should have all required keys."""
    hints = build_llm_hint_placeholder(["test point"])

    hint = hints["hints"][0]
    assert set(hint.keys()) == {"type", "message", "confidence", "evidence"}
    assert hint["evidence"] == []
