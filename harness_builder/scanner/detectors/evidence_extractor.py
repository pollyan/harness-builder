"""evidence_extractor — run existing detectors selectively based on LLM analysis."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from .ci_docker import detect_ci_docker
from .dotnet import detect_dotnet
from .filesystem import scan_filesystem
from .generic_fallback import detect_generic_fallback
from .java_maven import detect_java_maven
from .node_frontend import detect_node_frontend
from .shallow_code import detect_shallow_code_structure

# Keyword sets for stack identification
_JAVA_KEYWORDS = {"java", "maven", "spring", "gradle"}
_NODE_KEYWORDS = {"node", "npm", "vue", "react", "angular", "typescript"}
_JAVASCRIPT_KEYWORDS = {"javascript"}
_DOTNET_KEYWORDS = {".net", "dotnet", "c#", "csharp", "f#"}


def _stack_mentions(analysis: dict[str, Any], keywords: set[str]) -> bool:
    """Check if the LLM analysis mentions any of the given keywords in stack names."""
    stack_analysis = analysis.get("stackAnalysis", {})

    combined = _flatten_text(stack_analysis)
    return any(_keyword_matches(combined, kw) for kw in keywords)


def _keyword_matches(text: str, keyword: str) -> bool:
    """Match stack keywords without substring false positives like java/javascript."""
    if keyword == ".net":
        return re.search(r"(^|[^a-z0-9])\.net([^a-z0-9]|$)", text) is not None
    if keyword in {"c#", "f#"}:
        return re.search(rf"(^|[^a-z0-9]){re.escape(keyword)}([^a-z0-9]|$)", text) is not None
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def _flatten_text(value: Any) -> str:
    """Flatten nested LLM analysis values into lower-case searchable text."""
    if isinstance(value, dict):
        return " ".join(_flatten_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(v) for v in value)
    if value is None:
        return ""
    return str(value).lower()


def extract_evidence(repo_root: Path, llm_analysis: dict[str, Any]) -> dict[str, Any]:
    """Choose detectors based on LLM analysis and extract evidence."""
    result: dict[str, Any] = {}

    # Selective stack detectors
    if _stack_mentions(llm_analysis, _JAVA_KEYWORDS):
        result["java"] = _safe_detect(detect_java_maven, repo_root, "java")

    mentions_dotnet = _stack_mentions(llm_analysis, _DOTNET_KEYWORDS)
    mentions_javascript_only = _stack_mentions(llm_analysis, _JAVASCRIPT_KEYWORDS) and not mentions_dotnet
    if _stack_mentions(llm_analysis, _NODE_KEYWORDS) or mentions_javascript_only:
        result["node"] = _safe_detect(detect_node_frontend, repo_root, "node")

    if mentions_dotnet:
        result["dotnet"] = _safe_detect(detect_dotnet, repo_root, "dotnet")

    # Always-run detectors
    result["filesystem"] = _safe_detect(scan_filesystem, repo_root, "filesystem")
    result["ci"] = _safe_detect(detect_ci_docker, repo_root, "ci")
    result["codeStructure"] = _safe_detect(detect_shallow_code_structure, repo_root, "codeStructure")

    # Always run generic fallback as context/fallback
    result["genericFallback"] = _safe_detect(detect_generic_fallback, repo_root, "genericFallback")

    return result


def _safe_detect(detector: Callable[[Path], dict[str, Any]], repo_root: Path, name: str) -> dict[str, Any]:
    """Run one detector without letting it abort the entire extraction stage."""
    try:
        return detector(repo_root)
    except Exception as exc:
        return {"detected": False, "error": str(exc), "detector": name}
