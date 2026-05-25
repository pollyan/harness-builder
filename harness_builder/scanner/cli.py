from __future__ import annotations

import argparse
import os
from pathlib import Path

from harness_builder.scanner.core import scan_repository, write_scan_outputs


def _make_llm_caller():
    """Create an LLM caller that uses the OpenAI-compatible API via environment config."""
    try:
        import urllib.request
        import json as _json

        base_url = os.environ.get("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        api_key = os.environ.get("LLM_API_KEY", "")
        model = os.environ.get("LLM_MODEL", "glm-5.1")

        if not api_key:
            return None

        def call(prompt: str) -> str:
            url = f"{base_url}/chat/completions"
            payload = _json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 2000,
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

        return call
    except Exception:
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness Builder Scanner")
    parser.add_argument("--repo", default=".", help="Repository root path. Defaults to current directory.")
    parser.add_argument("--out", default=None, help="Output directory. Defaults to <repo>/.harness.")
    parser.add_argument("--llm", action="store_true", help="Enable LLM hint generation (requires LLM_API_KEY env var).")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    out = Path(args.out).resolve() if args.out else repo / ".harness"
    if not repo.exists():
        parser.error(f"repo path does not exist: {repo}")

    llm_caller = _make_llm_caller() if args.llm else None
    result = scan_repository(repo, out, llm_caller=llm_caller)
    write_scan_outputs(result, out)
    print(f"Generated Harness scanner outputs at {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
