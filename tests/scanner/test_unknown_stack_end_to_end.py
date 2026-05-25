import json
import subprocess
import sys
from pathlib import Path


def test_unknown_stack_still_generates_outputs(tmp_path):
    repo = Path("tests/fixtures/unknown-stack").resolve()
    out = tmp_path / ".harness"

    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(repo), "--out", str(out)],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    inventory = json.loads((out / "project-inventory.json").read_text())
    assert inventory["evidence"]["genericFallback"]["stackClassification"] == "unknown"
    assert inventory["analysis"]["enabled"] is False
    assert (out / "command-catalog.yaml").exists()
    assert (out / "scanner-report.md").exists()
