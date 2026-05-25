import json
from pathlib import Path

from harness_builder.scanner.core import (
    ScanResult,
    _command,
    _build_command_catalog,
    scan_repository,
    write_scan_outputs,
)


# ── _command ──


def test_command_default_values():
    cmd = _command("test", "echo hi", "source.txt")

    assert cmd["name"] == "test"
    assert cmd["command"] == "echo hi"
    assert cmd["source"] == "source.txt"
    assert cmd["workingDirectory"] == "."
    assert cmd["confidence"] == "medium"
    assert cmd["verified"] is False


def test_command_custom_values():
    cmd = _command("test", "echo hi", "source.txt", working_directory="sub/", confidence="high")

    assert cmd["workingDirectory"] == "sub/"
    assert cmd["confidence"] == "high"


# ── _build_command_catalog ──


def test_build_command_catalog_java():
    catalog = _build_command_catalog("my-repo", {"detected": True}, {"projects": []}, {"detected": False})

    assert catalog["repo"] == "my-repo"
    build_names = [c["name"] for c in catalog["commands"]["build"]]
    assert "maven-package" in build_names
    test_names = [c["name"] for c in catalog["commands"]["test"]]
    assert "maven-test" in test_names


def test_build_command_catalog_node_with_build_and_dev():
    node = {"projects": [{"path": "ui", "packageFile": "ui/package.json", "scripts": {"build": "vite build", "dev": "vite"}}]}
    catalog = _build_command_catalog("repo", {"detected": False}, node, {"detected": False})

    frontend = [c["command"] for c in catalog["commands"]["frontend"]]
    run_cmds = [c["command"] for c in catalog["commands"]["run"]]
    assert "npm run build" in frontend
    assert "npm run dev" in run_cmds


def test_build_command_catalog_node_no_build_script():
    """Node project without build/dev scripts → no frontend/run commands."""
    node = {"projects": [{"path": "lib", "packageFile": "lib/package.json", "scripts": {"test": "jest"}}]}
    catalog = _build_command_catalog("repo", {"detected": False}, node, {"detected": False})

    assert catalog["commands"]["frontend"] == []
    assert catalog["commands"]["run"] == []


def test_build_command_catalog_dotnet():
    catalog = _build_command_catalog("repo", {"detected": False}, {"projects": []}, {"detected": True})

    build_cmds = [c["command"] for c in catalog["commands"]["build"]]
    test_cmds = [c["command"] for c in catalog["commands"]["test"]]
    assert "dotnet build" in build_cmds
    assert "dotnet test" in test_cmds


def test_build_command_catalog_no_stack():
    """Nothing detected → all command lists empty."""
    catalog = _build_command_catalog("repo", {"detected": False}, {"projects": []}, {"detected": False})

    for key in ["build", "test", "run", "frontend", "docker"]:
        assert catalog["commands"][key] == []


def test_build_command_catalog_all_keys_present():
    """All expected command categories should exist even if empty."""
    catalog = _build_command_catalog("x", {}, {}, {})

    assert set(catalog["commands"].keys()) == {"build", "test", "run", "frontend", "docker"}


# ── scan_repository ──


def test_scan_repository_returns_scan_result():
    repo = Path("tests/fixtures/minimal-java-maven")
    out = Path("/tmp/unused")  # out_dir is only mkdir'd, not used for return

    result = scan_repository(repo, out)

    assert isinstance(result, ScanResult)
    assert isinstance(result.inventory, dict)
    assert isinstance(result.commands, dict)


def test_scan_repository_inventory_structure():
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"))
    inv = result.inventory

    assert "repo" in inv
    assert "structure" in inv
    assert "stackExtensions" in inv
    assert "ci" in inv
    assert "codeStructure" in inv
    assert "llmHints" in inv
    assert inv["repo"]["name"] == "minimal-java-maven"
    assert isinstance(inv["repo"]["path"], str)
    assert isinstance(inv["structure"], dict)
    assert isinstance(inv["ci"], dict)
    assert isinstance(inv["codeStructure"], dict)


def test_scan_repository_stack_extensions_keys():
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"))

    ext = result.inventory["stackExtensions"]
    assert "java" in ext
    assert "node" in ext
    assert "dotnet" in ext
    assert "genericFallback" in ext


def test_scan_repository_llm_hints_present():
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"))

    assert "llmHints" in result.inventory
    assert "enabled" in result.inventory["llmHints"]
    assert "hints" in result.inventory["llmHints"]


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
    import yaml

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
