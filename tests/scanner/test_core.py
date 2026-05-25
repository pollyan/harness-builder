import json
from pathlib import Path
from unittest.mock import MagicMock

import yaml

from harness_builder.scanner.core import (
    ScanResult,
    scan_repository,
    write_scan_outputs,
)


# ── scan_repository v2 pipeline ──


def test_scan_repository_returns_scan_result():
    repo = Path("tests/fixtures/minimal-java-maven")
    out = Path("/tmp/unused")

    result = scan_repository(repo, out)

    assert isinstance(result, ScanResult)
    assert isinstance(result.inventory, dict)
    assert isinstance(result.commands, dict)


def test_scan_no_llm_has_file_tree_and_analysis():
    """No LLM caller → fileTree present, analysis.enabled is False."""
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=None)

    assert "fileTree" in result.inventory
    assert "analysis" in result.inventory
    assert result.inventory["analysis"]["enabled"] is False


def test_scan_with_mock_llm():
    """Two-round mock LLM → analysis.enabled True, evidence present."""
    round1 = json.dumps({
        "stackAnalysis": {"primary": {"name": "Java", "confidence": "high", "evidence": []}, "secondary": []},
        "moduleAnalysis": [],
        "commandCandidates": [{"category": "build", "command": "mvn package", "confidence": "high", "evidence": []}],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    })
    round2 = json.dumps({
        "stackAnalysis": {"primary": {"name": "Java / Spring Boot", "confidence": "high", "evidence": ["pom.xml"]}, "secondary": []},
        "moduleAnalysis": [{"module": "app", "guessedRole": "App", "confidence": "medium", "evidence": []}],
        "commandCandidates": [{"category": "build", "command": "mvn clean package", "confidence": "high", "evidence": []}],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    })
    caller = MagicMock(side_effect=[round1, round2])
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=caller)

    assert result.inventory["analysis"]["enabled"] is True
    assert "evidence" in result.inventory


def test_scan_evidence_matches_llm_stack():
    """LLM says Java → evidence.java.detected True."""
    round1 = json.dumps({
        "stackAnalysis": {"primary": {"name": "Java"}, "secondary": []},
        "moduleAnalysis": [],
        "commandCandidates": [],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    })
    round2 = round1
    caller = MagicMock(side_effect=[round1, round2])
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=caller)

    assert "java" in result.inventory["evidence"]
    assert result.inventory["evidence"]["java"]["detected"] is True


def test_scan_commands_come_from_analysis():
    """No-LLM mode should still include build commands from evidence-based fallback."""
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=None)

    assert "build" in result.commands["commands"]
    build_cmds = [c["command"] for c in result.commands["commands"]["build"]]
    assert "mvn clean package -DskipTests" in build_cmds


def test_scan_includes_validation_points():
    """Should include validation results."""
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=None)

    assert "validation" in result.inventory
    assert "enabled" in result.inventory["validation"]


def test_scan_inventory_has_expected_keys():
    """v2 inventory should have: repo, fileTree, analysis, evidence, validation."""
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=None)
    inv = result.inventory

    assert "repo" in inv
    assert "fileTree" in inv
    assert "analysis" in inv
    assert "evidence" in inv
    assert "validation" in inv


# ── write_scan_outputs ──


def test_write_scan_outputs_creates_files(tmp_path):
    out = tmp_path / ".harness"
    result = ScanResult(
        inventory={"repo": {"name": "test", "path": "/test"}},
        commands={"repo": "test", "commands": {"build": [], "test": [], "run": [], "frontend": [], "docker": []}},
    )

    write_scan_outputs(result, out)

    assert (out / "project-inventory.json").exists()
    assert (out / "command-catalog.yaml").exists()
    assert (out / "scanner-report.md").exists()


def test_write_scan_outputs_json_valid(tmp_path):
    out = tmp_path / ".harness"
    result = ScanResult(
        inventory={"repo": {"name": "test", "path": "/test"}, "中文键": "中文值"},
        commands={"repo": "test", "commands": {"build": []}},
    )

    write_scan_outputs(result, out)

    data = json.loads((out / "project-inventory.json").read_text())
    assert data["中文键"] == "中文值"


def test_write_scan_outputs_yaml_valid(tmp_path):
    out = tmp_path / ".harness"
    result = ScanResult(
        inventory={"repo": {"name": "test", "path": "/test"}},
        commands={"repo": "test", "commands": {"build": [{"name": "b1"}]}},
    )

    write_scan_outputs(result, out)

    data = yaml.safe_load((out / "command-catalog.yaml").read_text())
    assert data["repo"] == "test"


def test_write_scan_outputs_creates_parent_dirs(tmp_path):
    out = tmp_path / "a" / "b" / "c"
    result = ScanResult(inventory={"repo": {"name": "t", "path": "/t"}}, commands={"repo": "t", "commands": {}})

    write_scan_outputs(result, out)

    assert out.exists()


def test_write_scan_outputs_overwrites_existing(tmp_path):
    out = tmp_path / ".harness"
    result = ScanResult(inventory={"repo": {"name": "v1", "path": "/v1"}}, commands={"repo": "v1", "commands": {}})
    write_scan_outputs(result, out)

    result2 = ScanResult(inventory={"repo": {"name": "v2", "path": "/v2"}}, commands={"repo": "v2", "commands": {}})
    write_scan_outputs(result2, out)

    data = json.loads((out / "project-inventory.json").read_text())
    assert data["repo"]["name"] == "v2"


def test_scan_skips_malformed_llm_command_candidate():
    """Malformed LLM command candidate without command should not crash scan."""
    round1 = json.dumps({
        "stackAnalysis": {"primary": {"name": "Java"}, "secondary": []},
        "moduleAnalysis": [],
        "commandCandidates": [{"category": "build", "confidence": "high"}],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    })
    caller = MagicMock(side_effect=[round1, round1])
    repo = Path("tests/fixtures/minimal-java-maven")

    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=caller)

    build_cmds = [c["command"] for c in result.commands["commands"]["build"]]
    assert "mvn clean package -DskipTests" in build_cmds


def test_scan_command_candidates_accept_type_as_category():
    """Real LLM command candidates may use type instead of category."""
    response = json.dumps({
        "stackAnalysis": {"primaryLanguage": "Java", "buildSystem": "Maven"},
        "moduleAnalysis": [],
        "commandCandidates": [{"type": "test", "command": "mvn test", "confidence": "high"}],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    })
    caller = MagicMock(side_effect=[response, response])

    result = scan_repository(Path("tests/fixtures/minimal-java-maven"), Path("/tmp/unused"), llm_caller=caller)

    test_cmds = [c["command"] for c in result.commands["commands"]["test"]]
    assert "mvn test" in test_cmds


def test_scan_validation_detects_nested_stack_claim_without_evidence(monkeypatch):
    """Validation should inspect real nested stackAnalysis shapes, not only primary/secondary."""
    from harness_builder.scanner.detectors import evidence_extractor

    response = json.dumps({
        "stackAnalysis": {"backend": {"language": "Java", "buildTool": "Maven"}},
        "moduleAnalysis": [],
        "commandCandidates": [],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    })
    caller = MagicMock(side_effect=[response, response])

    def fake_extract(repo_root, analysis):
        return {"filesystem": {}, "ci": {}, "codeStructure": {}, "genericFallback": {}}

    monkeypatch.setattr(evidence_extractor, "extract_evidence", fake_extract)
    monkeypatch.setattr("harness_builder.scanner.core.extract_evidence", fake_extract)

    result = scan_repository(Path("tests/fixtures/minimal-java-maven"), Path("/tmp/unused"), llm_caller=caller)

    assert result.inventory["validation"]["points"]
    assert result.inventory["validation"]["points"][0]["stack"] == "java"


def test_scan_infers_command_category_when_llm_omits_it():
    """Real LLM candidates may omit category/type; infer obvious test/run/frontend buckets."""
    response = json.dumps({
        "stackAnalysis": {"primaryLanguage": "C#", "buildSystem": "dotnet CLI"},
        "moduleAnalysis": [],
        "commandCandidates": [
            {"command": "dotnet build eShopOnWeb.sln", "confidence": "high"},
            {"command": "dotnet test tests/UnitTests/UnitTests.csproj", "confidence": "high"},
        ],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    })
    caller = MagicMock(side_effect=[response, response])

    result = scan_repository(Path("tests/fixtures/minimal-dotnet"), Path("/tmp/unused"), llm_caller=caller)

    assert [c["command"] for c in result.commands["commands"]["build"]] == ["dotnet build eShopOnWeb.sln"]
    assert [c["command"] for c in result.commands["commands"]["test"]] == ["dotnet test tests/UnitTests/UnitTests.csproj"]


def test_scan_skips_non_dict_llm_command_candidate():
    """Real LLMs may return commandCandidates entries as strings; skip them safely."""
    response = json.dumps({
        "stackAnalysis": {"primaryLanguage": "Java", "buildSystem": "Maven"},
        "moduleAnalysis": [],
        "commandCandidates": ["mvn test", {"command": "mvn clean package", "category": "build"}],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    })
    caller = MagicMock(side_effect=[response, response])

    result = scan_repository(Path("tests/fixtures/minimal-java-maven"), Path("/tmp/unused"), llm_caller=caller)

    assert [c["command"] for c in result.commands["commands"]["build"]] == ["mvn clean package"]


def test_scan_accepts_grouped_llm_command_candidates():
    """Real LLMs may return commandCandidates grouped by category."""
    response = json.dumps({
        "stackAnalysis": {"primaryLanguage": "C#", "buildSystem": "dotnet CLI"},
        "moduleAnalysis": [],
        "commandCandidates": {
            "build": {"commands": [{"command": "dotnet build eShopOnWeb.sln", "confidence": "high"}]},
            "test": {"commands": [{"command": "dotnet test tests/UnitTests/UnitTests.csproj", "confidence": "high"}]},
            "other": {"commands": [{"command": "dotnet run --project src/Web", "confidence": "high"}]},
        },
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    })
    caller = MagicMock(side_effect=[response, response])

    result = scan_repository(Path("tests/fixtures/minimal-dotnet"), Path("/tmp/unused"), llm_caller=caller)

    assert [c["command"] for c in result.commands["commands"]["build"]] == ["dotnet build eShopOnWeb.sln"]
    assert [c["command"] for c in result.commands["commands"]["test"]] == ["dotnet test tests/UnitTests/UnitTests.csproj"]
    assert [c["command"] for c in result.commands["commands"]["run"]] == ["dotnet run --project src/Web"]
