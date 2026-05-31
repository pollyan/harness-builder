from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SLICE_SCRIPTS = [
    "scripts/test-unit.sh",
    "scripts/test-integration.sh",
    "scripts/test-guided-init.sh",
    "scripts/test-llm-contracts.sh",
    "scripts/test-acceptance-llm-smoke.sh",
    "scripts/test-acceptance-real-repo.sh",
    "scripts/test-acceptance-self-improve.sh",
]


def _run_bash(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_test_slice_scripts_have_valid_bash_syntax():
    scripts = [
        ".githooks/pre-commit",
        "scripts/lib-test-env.sh",
        "scripts/test-fast.sh",
        "scripts/test-acceptance.sh",
        *SLICE_SCRIPTS,
    ]

    for script in scripts:
        result = subprocess.run(["bash", "-n", script], cwd=ROOT, text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stderr


def test_readme_documents_test_slice_scripts():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for script in SLICE_SCRIPTS:
        assert script in readme
    assert "只用于缩短开发反馈" in readme
    assert "不能替代 `scripts/test-fast.sh` 或 `scripts/test-full.sh`" in readme


def test_fast_stamp_uses_pytest_cache_not_git_internal_state():
    result = _run_bash(". scripts/lib-test-env.sh; hb_fast_stamp_path")

    assert result.returncode == 0, result.stderr
    stamp_path = result.stdout.strip()
    assert stamp_path == ".pytest_cache/harness-builder-test-fast.stamp"
    assert ".git" not in stamp_path


def test_fast_stamp_matches_after_write_and_detects_tree_change():
    probe = ROOT / "tmp-fast-stamp-probe.txt"
    if probe.exists():
        probe.unlink()

    try:
        result = _run_bash(
            ". scripts/lib-test-env.sh; "
            "hb_write_fast_stamp; "
            "hb_fast_stamp_matches; "
            "echo first:$?; "
            "printf changed > tmp-fast-stamp-probe.txt; "
            "hb_fast_stamp_matches; "
            "echo second:$?"
        )
    finally:
        if probe.exists():
            probe.unlink()

    assert result.returncode == 0, result.stderr
    assert "first:0" in result.stdout
    assert "second:1" in result.stdout


def test_slice_scripts_accept_pytest_options_without_running_full_suite():
    commands = [
        "bash scripts/test-unit.sh --version",
        "bash scripts/test-integration.sh --version",
        "bash scripts/test-guided-init.sh --collect-only -q",
        "bash scripts/test-llm-contracts.sh --collect-only -q",
    ]

    for command in commands:
        result = _run_bash(command)
        assert result.returncode == 0, result.stderr
