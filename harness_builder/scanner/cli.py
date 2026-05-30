from __future__ import annotations

import argparse
import os
from pathlib import Path

from harness_builder.scanner.core import scan_repository, write_scan_outputs
from harness_builder.scanner.deepseek_client import call_deepseek


def _load_dotenv(directory: Path) -> None:
    """Load .env file from directory without overriding existing env vars.

    Simple KEY=VALUE loader. Skips comments (#) and blank lines.
    Tries directory/.env first, then falls back to CWD/.env.
    """
    candidates = [directory / ".env", Path.cwd() / ".env"]
    env_path = None
    for candidate in candidates:
        if candidate.is_file():
            env_path = candidate
            break

    if env_path is None:
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def _make_llm_caller():
    """Create an LLM caller using DeepSeek via call_deepseek.

    Returns None if DEEPSEEK_API_KEY is not set.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return None

    def caller(user_message: str, system_prompt: str | None = None) -> str | None:
        return call_deepseek(user_message, system_prompt=system_prompt)

    return caller


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness Builder Scanner")
    parser.add_argument("--repo", default=".", help="Repository root path. Defaults to current directory.")
    parser.add_argument("--out", default=None, help="Output directory. Defaults to <repo>/.harness.")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM analysis (offline mode).")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    out = Path(args.out).resolve() if args.out else repo / ".harness"
    if not repo.exists():
        parser.error(f"repo path does not exist: {repo}")

    if args.no_llm:
        llm_caller = None
    else:
        _load_dotenv(repo)
        llm_caller = _make_llm_caller()

    result = scan_repository(repo, out, llm_caller=llm_caller)
    write_scan_outputs(result, out)
    print(f"Generated Harness scanner outputs at {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
