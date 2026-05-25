import json
from unittest.mock import MagicMock

from harness_builder.scanner.detectors.llm_hints import (
    LLM_HINT_POLICY,
    _build_prompt,
    _parse_llm_response,
    _format_hints,
    build_llm_hints,
    build_llm_hint_placeholder,
)


# ── _build_prompt ──


def test_build_prompt_contains_repo_name():
    inventory = {"repo": {"name": "my-project"}, "structure": {}, "stackExtensions": {}, "ci": {}, "codeStructure": {}}
    prompt = _build_prompt(inventory)

    assert "my-project" in prompt


def test_build_prompt_contains_detected_stacks():
    inventory = {
        "repo": {"name": "test"},
        "structure": {},
        "stackExtensions": {"java": {"detected": True}, "node": {"detected": False}},
        "ci": {},
        "codeStructure": {},
    }
    prompt = _build_prompt(inventory)

    assert "java" in prompt


def test_build_prompt_includes_rules():
    inventory = {"repo": {"name": "test"}, "structure": {}, "stackExtensions": {}, "ci": {}, "codeStructure": {}}
    prompt = _build_prompt(inventory)

    assert "hints" in prompt.lower() or "hint" in prompt.lower()
    assert "confidence" in prompt.lower()


def test_build_prompt_includes_code_structure_counts():
    inventory = {
        "repo": {"name": "test"},
        "structure": {},
        "stackExtensions": {},
        "ci": {},
        "codeStructure": {"controllers": ["a.java"], "services": [], "entitiesOrModels": [], "tests": ["t.java"], "frontendComponents": []},
    }
    prompt = _build_prompt(inventory)

    assert "Controllers: 1" in prompt
    assert "Test files: 1" in prompt


# ── _parse_llm_response ──


def test_parse_llm_response_plain_json():
    raw = json.dumps({
        "stackGuess": {"primary": "Java", "secondary": [], "confidence": "high", "evidence": ["pom.xml"]},
        "moduleResponsibilities": [],
        "calibrationPoints": [],
        "anomalies": [],
    })

    parsed = _parse_llm_response(raw)

    assert parsed["stackGuess"]["primary"] == "Java"


def test_parse_llm_response_markdown_code_block():
    raw = '```json\n{"stackGuess": {"primary": "Go"}, "moduleResponsibilities": [], "calibrationPoints": [], "anomalies": []}\n```'

    parsed = _parse_llm_response(raw)

    assert parsed["stackGuess"]["primary"] == "Go"


def test_parse_llm_response_plain_code_block():
    raw = '```\n{"stackGuess": null, "moduleResponsibilities": [], "calibrationPoints": [], "anomalies": []}\n```'

    parsed = _parse_llm_response(raw)

    assert parsed["stackGuess"] is None


def test_parse_llm_response_invalid_json():
    raw = "This is not JSON at all"

    parsed = _parse_llm_response(raw)

    assert parsed.get("_parseError") is True
    assert "stackGuess" in parsed  # Still has the expected keys


def test_parse_llm_response_empty_string():
    parsed = _parse_llm_response("")

    assert parsed.get("_parseError") is True


# ── _format_hints ──


def test_format_hints_stack_guess():
    parsed = {
        "stackGuess": {"primary": "Java", "secondary": ["Vue"], "confidence": "high", "evidence": ["pom.xml found"]},
        "moduleResponsibilities": [],
        "calibrationPoints": [],
        "anomalies": [],
    }

    result = _format_hints(parsed, [])

    stack_hints = [h for h in result["hints"] if h["type"] == "stack-guess"]
    assert len(stack_hints) == 1
    assert "Java" in stack_hints[0]["message"]
    assert "Vue" in stack_hints[0]["message"]
    assert stack_hints[0]["confidence"] == "high"
    assert "pom.xml found" in stack_hints[0]["evidence"]


def test_format_hints_module_responsibility():
    parsed = {
        "stackGuess": None,
        "moduleResponsibilities": [{"module": "app", "guessedRole": "Main application module", "confidence": "medium", "evidence": ["has Spring config"]}],
        "calibrationPoints": [],
        "anomalies": [],
    }

    result = _format_hints(parsed, [])

    mod_hints = [h for h in result["hints"] if h["type"] == "module-responsibility"]
    assert len(mod_hints) == 1
    assert "app" in mod_hints[0]["message"]
    assert "Main application module" in mod_hints[0]["message"]


def test_format_hints_anomalies():
    parsed = {
        "stackGuess": None,
        "moduleResponsibilities": [],
        "calibrationPoints": [],
        "anomalies": [{"message": "Multiple build systems detected", "confidence": "medium", "evidence": ["pom.xml and build.gradle both exist"]}],
    }

    result = _format_hints(parsed, [])

    anom_hints = [h for h in result["hints"] if h["type"] == "anomaly"]
    assert len(anom_hints) == 1
    assert anom_hints[0]["message"] == "Multiple build systems detected"


def test_format_hints_calibration_from_llm():
    parsed = {
        "stackGuess": None,
        "moduleResponsibilities": [],
        "calibrationPoints": [{"message": "Verify Spring profile configuration", "confidence": "medium", "evidence": ["application.yml found"]}],
        "anomalies": [],
    }

    result = _format_hints(parsed, [])

    cal_hints = [h for h in result["hints"] if h["type"] == "calibration"]
    assert len(cal_hints) == 1


def test_format_hints_manual_points_appended():
    parsed = {"stackGuess": None, "moduleResponsibilities": [], "calibrationPoints": [], "anomalies": []}
    manual = ["check build system", "verify test commands"]

    result = _format_hints(parsed, manual)

    manual_hints = [h for h in result["hints"] if h["type"] == "manual-calibration"]
    assert len(manual_hints) == 2
    assert manual_hints[0]["message"] == "check build system"


def test_format_hints_no_stack_guess():
    parsed = {"stackGuess": {"primary": None, "secondary": [], "confidence": "low", "evidence": []}, "moduleResponsibilities": [], "calibrationPoints": [], "anomalies": []}

    result = _format_hints(parsed, [])

    stack_hints = [h for h in result["hints"] if h["type"] == "stack-guess"]
    assert len(stack_hints) == 0  # No hint when primary is None


# ── build_llm_hints (integration of all pieces) ──


def test_build_llm_hints_without_caller():
    """Without llm_caller → enabled=False, only manual points."""
    result = build_llm_hints({"repo": {"name": "test"}}, ["manual point"], llm_caller=None)

    assert result["enabled"] is False
    assert len(result["hints"]) == 1
    assert result["hints"][0]["type"] == "manual-calibration"


def test_build_llm_hints_with_mock_caller():
    """With a mock LLM caller → enabled=True, hints from LLM + manual."""
    mock_response = json.dumps({
        "stackGuess": {"primary": "Java", "secondary": [], "confidence": "high", "evidence": ["pom.xml"]},
        "moduleResponsibilities": [
            {"module": "core", "guessedRole": "Core business logic", "confidence": "medium", "evidence": ["has services/"]}
        ],
        "calibrationPoints": [
            {"message": "Verify database type", "confidence": "low", "evidence": ["SQL files found"]}
        ],
        "anomalies": [],
    })
    caller = MagicMock(return_value=mock_response)

    result = build_llm_hints({"repo": {"name": "test"}, "structure": {}, "stackExtensions": {}, "ci": {}, "codeStructure": {}}, ["check this"], llm_caller=caller)

    assert result["enabled"] is True
    types = [h["type"] for h in result["hints"]]
    assert "stack-guess" in types
    assert "module-responsibility" in types
    assert "calibration" in types
    assert "manual-calibration" in types
    assert caller.called


def test_build_llm_hints_llm_exception_graceful_degradation():
    """When LLM caller throws → graceful degradation to manual points only."""
    caller = MagicMock(side_effect=RuntimeError("API error"))

    result = build_llm_hints({"repo": {"name": "test"}}, ["manual fallback"], llm_caller=caller)

    assert result["enabled"] is False
    assert result.get("_llmError") is True
    assert len(result["hints"]) == 1
    assert result["hints"][0]["message"] == "manual fallback"


def test_build_llm_hints_llm_returns_garbage():
    """When LLM returns unparseable text → still produces output with _parseError."""
    caller = MagicMock(return_value="I don't know what this project is")

    result = build_llm_hints({"repo": {"name": "test"}, "structure": {}, "stackExtensions": {}, "ci": {}, "codeStructure": {}}, [], llm_caller=caller)

    # Should still produce valid output structure
    assert "hints" in result
    assert isinstance(result["hints"], list)


# ── backward compatibility ──


def test_build_llm_hint_placeholder_backward_compat():
    """Old alias should still work."""
    result = build_llm_hint_placeholder(["point a"])

    assert result["enabled"] is False
    assert len(result["hints"]) == 1


# ── policy constant ──


def test_policy_is_non_empty():
    assert len(LLM_HINT_POLICY) > 0
    assert "LLM" in LLM_HINT_POLICY
