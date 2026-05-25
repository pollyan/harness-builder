"""evidence_extractor — run existing detectors selectively based on LLM analysis."""
from __future__ import annotations

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
_NODE_KEYWORDS = {"node", "npm", "vue", "react", "angular", "typescript", "javascript", "frontend"}
_DOTNET_KEYWORDS = {".net", "dotnet", "c#", "csharp", "f#"}


def _stack_mentions(analysis: dict[str, Any], keywords: set[str]) -> bool:
    """Check if the LLM analysis mentions any of the given keywords in stack names."""
    stack_analysis = analysis.get("stackAnalysis", {})

    # Collect all stack name strings to check
    names: list[str] = []

    primary = stack_analysis.get("primary")
    if primary and isinstance(primary, dict):
        name = primary.get("name", "")
        if name:
            names.append(name.lower())

    secondary = stack_analysis.get("secondary")
    if isinstance(secondary, list):
        for item in secondary:
            if isinstance(item, dict):
                name = item.get("name", "")
                if name:
                    names.append(name.lower())

    # Also check top-level "name" field if stackAnalysis itself has one
    top_name = stack_analysis.get("name", "")
    if top_name:
        names.append(str(top_name).lower())

    combined = " ".join(names)
    return any(kw in combined for kw in keywords)


def extract_evidence(repo_root: Path, llm_analysis: dict[str, Any]) -> dict[str, Any]:
    """Choose detectors based on LLM analysis and extract evidence."""
    result: dict[str, Any] = {}

    # Selective stack detectors
    if _stack_mentions(llm_analysis, _JAVA_KEYWORDS):
        result["java"] = _safe_detect(detect_java_maven, repo_root, "java")

    if _stack_mentions(llm_analysis, _NODE_KEYWORDS):
        result["node"] = _safe_detect(detect_node_frontend, repo_root, "node")

    if _stack_mentions(llm_analysis, _DOTNET_KEYWORDS):
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
