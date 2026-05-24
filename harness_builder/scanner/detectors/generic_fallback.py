from __future__ import annotations

from pathlib import Path

SCRIPT_DIR_NAMES = {"scripts", "bin", "tools"}
CONFIG_DIR_NAMES = {"config", "conf", "settings"}
DOC_NAMES = {"README.md", "CONTRIBUTING.md"}


def detect_generic_fallback(repo_root: Path) -> dict:
    documentation = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.rglob("*") if p.is_file() and p.name in DOC_NAMES)
    script_candidates = sorted(
        p.relative_to(repo_root).as_posix()
        for p in repo_root.rglob("*")
        if p.is_file() and any(part in SCRIPT_DIR_NAMES for part in p.relative_to(repo_root).parts)
    )
    config_candidates = sorted(
        p.relative_to(repo_root).as_posix()
        for p in repo_root.rglob("*")
        if p.is_file() and any(part in CONFIG_DIR_NAMES for part in p.relative_to(repo_root).parts)
    )
    return {
        "stackClassification": "unknown",
        "documentation": documentation,
        "scriptCandidates": script_candidates,
        "configCandidates": config_candidates,
        "manualCalibrationPoints": [
            "未识别到受支持的主技术栈 detector，请人工确认构建系统和测试命令。"
        ],
    }
