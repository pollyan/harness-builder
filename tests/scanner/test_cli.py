import subprocess
import sys


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
