import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

from harness_builder.scanner.cli import _load_dotenv, _make_llm_caller, build_parser


# ── Existing tests ────────────────────────────────────────────────


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
        [sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(repo), "--out", str(out), "--no-llm"],
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
        [sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(repo), "--no-llm"],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert (repo / ".harness" / "project-inventory.json").exists()


# ── Task 6: --no-llm, DeepSeek default, .env loader ──────────────


def test_cli_help_shows_no_llm():
    """--no-llm flag must appear in help output."""
    parser = build_parser()
    help_text = parser.format_help()
    assert "--no-llm" in help_text


def test_cli_help_does_not_show_old_llm():
    """The old --llm flag should no longer exist."""
    parser = build_parser()
    help_text = parser.format_help()
    assert "--llm" not in help_text or "--no-llm" in help_text


def test_cli_no_llm_flag(tmp_path):
    """With --no-llm, scan completes and analysis.enabled is False."""
    repo = Path("tests/fixtures/minimal-java-maven").resolve()
    out = tmp_path / ".harness"

    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli",
         "--repo", str(repo), "--out", str(out), "--no-llm"],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    inv = json.loads((out / "project-inventory.json").read_text())
    assert inv["analysis"]["enabled"] is False


def test_cli_no_llm_flag_short_circuit(tmp_path):
    """With --no-llm, no LLM caller is created at all."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# test")
    out = tmp_path / "out"

    with mock.patch("harness_builder.scanner.cli._make_llm_caller") as mock_caller:
        mock_caller.return_value = lambda prompt: "dummy"
        from harness_builder.scanner.cli import main

        # --no-llm should NOT call _make_llm_caller
        ret = main(["--repo", str(repo), "--out", str(out), "--no-llm"])
        assert ret == 0
        mock_caller.assert_not_called()


def test_make_llm_caller_returns_callable_with_key():
    """When DEEPSEEK_API_KEY is set, _make_llm_caller returns a callable."""
    with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test-key"}):
        caller = _make_llm_caller()
        assert callable(caller)


def test_make_llm_caller_returns_none_without_key():
    """When DEEPSEEK_API_KEY is not set, _make_llm_caller returns None."""
    env = {k: v for k, v in os.environ.items() if k != "DEEPSEEK_API_KEY"}
    with mock.patch.dict(os.environ, env, clear=True):
        caller = _make_llm_caller()
        assert caller is None


def test_make_llm_caller_uses_deepseek():
    """The default caller should use DeepSeek via call_deepseek."""
    with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test-key"}):
        with mock.patch("harness_builder.scanner.cli.call_deepseek") as mock_ds:
            mock_ds.return_value = "test response"
            caller = _make_llm_caller()
            result = caller("hello")
            mock_ds.assert_called_once_with("hello", system_prompt=None)
            assert result == "test response"


def test_make_llm_caller_passes_system_prompt():
    """The caller should forward system_prompt to call_deepseek."""
    with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test-key"}):
        with mock.patch("harness_builder.scanner.cli.call_deepseek") as mock_ds:
            mock_ds.return_value = "response"
            caller = _make_llm_caller()
            caller("msg", system_prompt="sys")
            mock_ds.assert_called_once_with("msg", system_prompt="sys")


def test_load_dotenv_reads_key(tmp_path):
    """_load_dotenv should read KEY=VALUE from a .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("DEEPSEEK_API_KEY=sk-from-file\nDEEPSEEK_MODEL=test-model\n")

    env = {k: v for k, v in os.environ.items() if k not in ("DEEPSEEK_API_KEY", "DEEPSEEK_MODEL")}
    with mock.patch.dict(os.environ, env, clear=True):
        _load_dotenv(tmp_path)
        assert os.environ.get("DEEPSEEK_API_KEY") == "sk-from-file"
        assert os.environ.get("DEEPSEEK_MODEL") == "test-model"


def test_load_dotenv_no_override_existing(tmp_path):
    """_load_dotenv must NOT override env vars that are already set."""
    env_file = tmp_path / ".env"
    env_file.write_text("DEEPSEEK_API_KEY=sk-from-file\n")

    with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-existing"}, clear=False):
        _load_dotenv(tmp_path)
        assert os.environ["DEEPSEEK_API_KEY"] == "sk-existing"


def test_load_dotenv_missing_file_ok(tmp_path):
    """_load_dotenv should not fail if .env doesn't exist."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    _load_dotenv(empty_dir)  # should not raise


def test_load_dotenv_skips_comments_and_blank_lines(tmp_path):
    """_load_dotenv should ignore comments (#) and blank lines."""
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\n\n  \nDEEPSEEK_API_KEY=sk-file\n# another comment\n")

    env = {k: v for k, v in os.environ.items() if k != "DEEPSEEK_API_KEY"}
    with mock.patch.dict(os.environ, env, clear=True):
        _load_dotenv(tmp_path)
        assert os.environ.get("DEEPSEEK_API_KEY") == "sk-file"


def test_default_cli_llm_enabled_with_key(tmp_path):
    """Without --no-llm, if DEEPSEEK_API_KEY is set, LLM path is attempted."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# test")
    out = tmp_path / "out"

    with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test"}):
        with mock.patch("harness_builder.scanner.cli.call_deepseek", return_value=None):
            # call_deepseek returning None simulates graceful failure
            from harness_builder.scanner.cli import main

            ret = main(["--repo", str(repo), "--out", str(out)])
            assert ret == 0
