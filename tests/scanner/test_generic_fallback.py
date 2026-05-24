from pathlib import Path

from harness_builder.scanner.detectors.generic_fallback import detect_generic_fallback


def test_generic_fallback_handles_unknown_stack():
    repo = Path("tests/fixtures/unknown-stack")

    result = detect_generic_fallback(repo)

    assert result["stackClassification"] in {"unknown", "mixed"}
    assert "README.md" in result["documentation"]
    assert "scripts/build.custom" in result["scriptCandidates"]
    assert "config/app.conf" in result["configCandidates"]
    assert result["manualCalibrationPoints"]
