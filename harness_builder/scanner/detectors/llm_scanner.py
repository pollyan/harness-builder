"""LLM scan engine with self-check for Scanner v2.

Performs two rounds over the file tree:
  Round 1: Full analysis (tech stack, modules, commands, architecture).
  Round 2: Self-check — what did round 1 miss?

The caller is injected so tests can mock it without real LLM calls.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

# Expected top-level keys in a valid LLM analysis response
_REQUIRED_KEYS = frozenset({
    "stackAnalysis",
    "moduleAnalysis",
    "commandCandidates",
    "architecturePattern",
    "anomalies",
    "calibrationPoints",
})


def build_scan_prompt(file_tree: dict[str, Any]) -> str:
    """Build the round-1 analysis prompt from a file tree manifest.

    Requires the LLM to analyze every top-level module and cover
    build/test commands.
    """
    files_summary = _summarize_tree(file_tree)
    top_dirs = _top_level_dirs(file_tree)

    return (
        "You are an expert codebase analyst. Analyze the following repository file tree "
        "and produce a JSON object with these keys:\n"
        "  stackAnalysis, moduleAnalysis, commandCandidates, "
        "architecturePattern, anomalies, calibrationPoints\n\n"
        "Requirements:\n"
        f"1. Analyze EVERY top-level module/directory: {', '.join(top_dirs) if top_dirs else '(none)'}\n"
        "2. Provide build and test commands with confidence levels\n"
        "3. Identify the architecture pattern and any anomalies\n"
        "4. Return ONLY valid JSON (no markdown fences needed, but accepted)\n\n"
        f"File tree:\n{files_summary}"
    )


def build_self_check_prompt(round1_json: str, file_tree: dict[str, Any]) -> str:
    """Build the round-2 self-check prompt.

    Presents the round-1 conclusion and asks the LLM to find gaps,
    listing all top-level directories for cross-checking.
    """
    top_dirs = _top_level_dirs(file_tree)

    return (
        "You previously analyzed a repository. Here was your round-1 conclusion:\n\n"
        f"{round1_json}\n\n"
        "Please self-check your analysis for completeness.\n"
        "Here are ALL top-level directories in the repo:\n"
        f"  {', '.join(top_dirs) if top_dirs else '(none)'}\n\n"
        "Identify anything you missed: modules not analyzed, "
        "commands not covered, or inconsistencies.\n"
        "Return an UPDATED full JSON with the same keys:\n"
        "  stackAnalysis, moduleAnalysis, commandCandidates, "
        "architecturePattern, anomalies, calibrationPoints\n"
        "Return ONLY valid JSON."
    )


def parse_scan_response(raw: Optional[str]) -> Optional[dict[str, Any]]:
    """Parse an LLM response into a structured dict.

    Handles: plain JSON, JSON inside markdown code blocks, graceful None fallback.
    """
    if not raw:
        return None

    text = raw.strip()

    # Try extracting from markdown code block
    code_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if code_match:
        candidate = code_match.group(1).strip()
        parsed = _try_parse_json(candidate)
        if parsed is not None:
            return parsed

    # Try the whole text as JSON
    return _try_parse_json(text)


def merge_rounds(
    round1: dict[str, Any],
    round2: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """Merge round-1 and round-2 analyses.

    Round-2 takes priority. If round-2 is None/invalid, fall back to round-1.
    Unique module analyses from round-1 are preserved.
    """
    if round2 is None:
        return round1

    merged = dict(round2)

    # Preserve unique module analyses from round-1 that round-2 dropped
    def _module_key(m):
        return m.get("module") if isinstance(m, dict) else str(m)

    r2_modules = {_module_key(m) for m in (round2.get("moduleAnalysis") or [])}
    r1_unique = [
        m for m in (round1.get("moduleAnalysis") or [])
        if _module_key(m) not in r2_modules
    ]
    if r1_unique:
        existing = list(merged.get("moduleAnalysis") or [])
        existing.extend(r1_unique)
        merged["moduleAnalysis"] = existing

    return merged


def scan_with_llm(
    file_tree: dict[str, Any],
    caller: Optional[Callable[[str, Optional[str]], Optional[str]]],
) -> dict[str, Any]:
    """Two-round LLM scanning entrypoint.

    Args:
        file_tree: Structured file tree from file_tree_collector.
        caller: LLM caller with signature (user_message, system_prompt) -> str | None.
            If None, returns a disabled analysis object.

    Returns:
        Analysis dict with 'enabled' key. Structure depends on success/failure.
    """
    if caller is None:
        return {"enabled": False}

    # Round 1: full analysis
    prompt1 = build_scan_prompt(file_tree)
    raw1 = caller(prompt1, None)
    round1 = parse_scan_response(raw1)

    if round1 is None:
        return {"enabled": False}

    # Round 2: self-check
    prompt2 = build_self_check_prompt(json.dumps(round1), file_tree)
    raw2 = caller(prompt2, None)
    round2 = parse_scan_response(raw2)

    merged = merge_rounds(round1, round2)
    merged["enabled"] = True
    merged["selfCheckDegraded"] = round2 is None

    return merged


# ── Internal helpers ───────────────────────────────────────────────


def _summarize_tree(file_tree: dict[str, Any]) -> str:
    """Produce a compact text summary of the file tree for prompts."""
    lines: list[str] = []
    for f in file_tree.get("files", []):
        lines.append(f"  FILE: {f['path']} ({f.get('sizeBytes', 0)} bytes)")
    for d in file_tree.get("directories", []):
        lines.append(f"  DIR:  {d['path']} ({d.get('fileCount', 0)} files, {d.get('subdirectoryCount', 0)} subdirs)")
    return "\n".join(lines)


def _top_level_dirs(file_tree: dict[str, Any]) -> list[str]:
    """Extract top-level directory names from file tree."""
    dirs: list[str] = []
    for d in file_tree.get("directories", []):
        path = d.get("path", "")
        # Top-level means no '/' in relative path
        if "/" not in path:
            dirs.append(d["name"])
    return sorted(dirs)


def _try_parse_json(text: str) -> Optional[dict[str, Any]]:
    """Attempt JSON parse; return None on failure."""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and _has_required_keys(parsed):
            return parsed
        return None
    except (json.JSONDecodeError, ValueError):
        return None


def _has_required_keys(parsed: dict[str, Any]) -> bool:
    """Return True when parsed LLM output satisfies the scanner contract."""
    return _REQUIRED_KEYS.issubset(parsed.keys())
