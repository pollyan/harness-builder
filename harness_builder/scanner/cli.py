from __future__ import annotations

import argparse
from pathlib import Path

from harness_builder.scanner.core import scan_repository, write_scan_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness Builder Scanner")
    parser.add_argument("--repo", default=".", help="Repository root path. Defaults to current directory.")
    parser.add_argument("--out", default=None, help="Output directory. Defaults to <repo>/.harness.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    out = Path(args.out).resolve() if args.out else repo / ".harness"
    if not repo.exists():
        parser.error(f"repo path does not exist: {repo}")
    result = scan_repository(repo, out)
    write_scan_outputs(result, out)
    print(f"Generated Harness scanner outputs at {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
