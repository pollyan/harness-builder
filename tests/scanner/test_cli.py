import subprocess
import sys
from pathlib import Path


def test_scanner_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli", "--help"],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "Harness Builder Scanner" in result.stdout
    assert "--repo" in result.stdout
    assert "--out" in result.stdout


def test_scanner_cli_runs_on_fixture(tmp_path):
    repo = Path("tests/fixtures/minimal-java-maven").resolve()
    out = tmp_path / ".harness"

    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(repo), "--out", str(out)],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert (out / "project-inventory.json").exists()
    assert "Generated" in result.stdout


def test_scanner_cli_nonexistent_repo(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(tmp_path / "nonexistent")],
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0


def test_scanner_cli_default_out_dir(tmp_path):
    """When --out is omitted, output should go to <repo>/.harness."""
    repo = tmp_path / "myrepo"
    repo.mkdir()
    (repo / "README.md").write_text("# test")

    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(repo)],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert (repo / ".harness" / "project-inventory.json").exists()
