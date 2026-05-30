import json
import subprocess
import sys
from pathlib import Path

import yaml


def test_cli_generates_harness_files(tmp_path):
    repo = Path("tests/fixtures/minimal-java-maven").resolve()
    out = tmp_path / ".harness"

    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(repo), "--out", str(out), "--no-llm"],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    inventory = json.loads((out / "project-inventory.json").read_text())
    commands = yaml.safe_load((out / "command-catalog.yaml").read_text())
    report = (out / "scanner-report.md").read_text()

    assert inventory["repo"]["name"] == "minimal-java-maven"
    assert commands["repo"] == "minimal-java-maven"
    assert "# Scanner Report" in report
