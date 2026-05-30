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


def test_generic_fallback_empty_repo(tmp_path):
    """Empty repo → empty lists but still has manualCalibrationPoints."""
    result = detect_generic_fallback(tmp_path)

    assert result["documentation"] == []
    assert result["scriptCandidates"] == []
    assert result["configCandidates"] == []
    assert len(result["manualCalibrationPoints"]) > 0


def test_generic_fallback_contributing_md(tmp_path):
    """CONTRIBUTING.md should also be detected as documentation."""
    (tmp_path / "CONTRIBUTING.md").write_text("# Contributing")

    result = detect_generic_fallback(tmp_path)

    assert "CONTRIBUTING.md" in result["documentation"]


def test_generic_fallback_scripts_in_bin_dir(tmp_path):
    """Files in 'bin' directory should be script candidates."""
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "setup.sh").write_text("#!/bin/bash")

    result = detect_generic_fallback(tmp_path)

    assert "bin/setup.sh" in result["scriptCandidates"]


def test_generic_fallback_scripts_in_tools_dir(tmp_path):
    """Files in 'tools' directory should be script candidates."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "migrate.py").write_text("print('migrate')")

    result = detect_generic_fallback(tmp_path)

    assert "tools/migrate.py" in result["scriptCandidates"]


def test_generic_fallback_config_in_conf_dir(tmp_path):
    """Files in 'conf' directory should be config candidates."""
    (tmp_path / "conf").mkdir()
    (tmp_path / "conf" / "app.ini").write_text("[default]")

    result = detect_generic_fallback(tmp_path)

    assert "conf/app.ini" in result["configCandidates"]


def test_generic_fallback_config_in_settings_dir(tmp_path):
    """Files in 'settings' directory should be config candidates."""
    (tmp_path / "settings").mkdir()
    (tmp_path / "settings" / "prod.json").write_text("{}")

    result = detect_generic_fallback(tmp_path)

    assert "settings/prod.json" in result["configCandidates"]


def test_generic_fallback_nested_scripts(tmp_path):
    """Scripts in nested directories under scripts/ should be found."""
    nested = tmp_path / "scripts" / "deploy"
    nested.mkdir(parents=True)
    (nested / "prod.sh").write_text("#!/bin/bash")

    result = detect_generic_fallback(tmp_path)

    assert "scripts/deploy/prod.sh" in result["scriptCandidates"]
