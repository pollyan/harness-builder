"""Tests for llm_scanner.py — LLM scan engine with self-check.

TDD: These tests define the expected behaviour of the LLM scanning engine
that performs two rounds over a file tree (analysis + self-check).
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from harness_builder.scanner.detectors.llm_scanner import (
    build_scan_prompt,
    build_self_check_prompt,
    merge_rounds,
    parse_scan_response,
    scan_with_llm,
)


# ── build_scan_prompt ──────────────────────────────────────────────


class TestBuildScanPrompt:
    """build_scan_prompt must include file tree info and require minimum coverage."""

    def test_includes_file_tree_info(self) -> None:
        file_tree = {
            "root": "/tmp/repo",
            "files": [
                {"path": "pom.xml", "name": "pom.xml", "extension": ".xml", "sizeBytes": 1200},
                {"path": "src/main/java/App.java", "name": "App.java", "extension": ".java", "sizeBytes": 500},
            ],
            "directories": [
                {"path": "src", "name": "src", "fileCount": 0, "subdirectoryCount": 1},
                {"path": "src/main", "name": "main", "fileCount": 0, "subdirectoryCount": 1},
            ],
        }
        prompt = build_scan_prompt(file_tree)
        assert "pom.xml" in prompt
        assert "App.java" in prompt
        assert "src" in prompt

    def test_requires_minimum_coverage(self) -> None:
        file_tree = {
            "root": "/tmp/repo",
            "files": [],
            "directories": [],
        }
        prompt = build_scan_prompt(file_tree)
        # Must require analysis of every top-level module and build/test coverage
        assert "top-level" in prompt.lower() or "module" in prompt.lower()
        assert "build" in prompt.lower()
        assert "test" in prompt.lower()


# ── build_self_check_prompt ────────────────────────────────────────


class TestBuildSelfCheckPrompt:
    """build_self_check_prompt must reference round1 conclusion and list unanalyzed dirs."""

    def test_references_round1_and_lists_dirs(self) -> None:
        file_tree = {
            "root": "/tmp/repo",
            "files": [],
            "directories": [
                {"path": "src", "name": "src", "fileCount": 5, "subdirectoryCount": 2},
                {"path": "docs", "name": "docs", "fileCount": 3, "subdirectoryCount": 0},
            ],
        }
        round1_json = json.dumps({
            "stackAnalysis": {"primary": {"name": "Java"}},
            "moduleAnalysis": [],
            "commandCandidates": [],
            "architecturePattern": None,
            "anomalies": [],
            "calibrationPoints": [],
        })
        prompt = build_self_check_prompt(round1_json, file_tree)
        # Must reference the round1 conclusion
        assert "Java" in prompt
        # Must list top-level directories for self-check
        assert "src" in prompt
        assert "docs" in prompt


# ── parse_scan_response ────────────────────────────────────────────


class TestParseScanResponse:
    """parse_scan_response handles valid JSON, code blocks, and invalid fallback."""

    def test_valid_json(self) -> None:
        raw = json.dumps({
            "stackAnalysis": {"primary": {"name": "Java"}},
            "moduleAnalysis": [],
            "commandCandidates": [],
            "architecturePattern": None,
            "anomalies": [],
            "calibrationPoints": [],
        })
        result = parse_scan_response(raw)
        assert result is not None
        assert result["stackAnalysis"]["primary"]["name"] == "Java"

    def test_code_block_extraction(self) -> None:
        payload = json.dumps({
            "stackAnalysis": {"primary": {"name": "Python"}},
            "moduleAnalysis": [],
            "commandCandidates": [],
            "architecturePattern": None,
            "anomalies": [],
            "calibrationPoints": [],
        })
        raw = f"Here is my analysis:\n```json\n{payload}\n```\nDone."
        result = parse_scan_response(raw)
        assert result is not None
        assert result["stackAnalysis"]["primary"]["name"] == "Python"

    def test_invalid_fallback(self) -> None:
        result = parse_scan_response("this is not json at all!!!")
        assert result is None


# ── merge_rounds ───────────────────────────────────────────────────


class TestMergeRounds:
    """merge_rounds gives round2 priority, falls back to round1 on round2 failure."""

    def _round1(self) -> dict:
        return {
            "stackAnalysis": {"primary": {"name": "Java"}},
            "moduleAnalysis": [{"module": "app", "guessedRole": "App"}],
            "commandCandidates": [{"category": "build", "command": "mvn package"}],
            "architecturePattern": None,
            "anomalies": [],
            "calibrationPoints": [],
        }

    def _round2(self) -> dict:
        return {
            "stackAnalysis": {"primary": {"name": "Java / Spring Boot"}},
            "moduleAnalysis": [
                {"module": "app", "guessedRole": "App"},
                {"module": "common", "guessedRole": "Shared Utilities"},
            ],
            "commandCandidates": [{"category": "build", "command": "mvn clean package"}],
            "architecturePattern": "monolith",
            "anomalies": ["missing tests"],
            "calibrationPoints": [],
        }

    def test_round2_priority(self) -> None:
        r1 = self._round1()
        r2 = self._round2()
        merged = merge_rounds(r1, r2)
        # Round2 stack takes priority
        assert merged["stackAnalysis"]["primary"]["name"] == "Java / Spring Boot"
        # Round2 command takes priority
        assert merged["commandCandidates"][0]["command"] == "mvn clean package"
        # Round2 unique module analysis preserved
        modules = [m["module"] for m in merged["moduleAnalysis"]]
        assert "common" in modules

    def test_round2_failure_fallback_to_round1(self) -> None:
        r1 = self._round1()
        merged = merge_rounds(r1, None)
        assert merged["stackAnalysis"]["primary"]["name"] == "Java"
        assert merged["moduleAnalysis"][0]["module"] == "app"


# ── scan_with_llm ─────────────────────────────────────────────────


class TestScanWithLlm:
    """scan_with_llm orchestrates two LLM calls with proper degradation."""

    def _file_tree(self) -> dict:
        return {
            "root": "/tmp/repo",
            "files": [
                {"path": "pom.xml", "name": "pom.xml", "extension": ".xml", "sizeBytes": 1200},
            ],
            "directories": [
                {"path": "src", "name": "src", "fileCount": 1, "subdirectoryCount": 0},
            ],
        }

    def _round1_response(self) -> str:
        return json.dumps({
            "stackAnalysis": {"primary": {"name": "Java", "confidence": "high", "evidence": []}},
            "moduleAnalysis": [],
            "commandCandidates": [{"category": "build", "command": "mvn package", "confidence": "high", "evidence": []}],
            "architecturePattern": None,
            "anomalies": [],
            "calibrationPoints": [],
        })

    def _round2_response(self) -> str:
        return json.dumps({
            "stackAnalysis": {"primary": {"name": "Java / Spring Boot", "confidence": "high", "evidence": ["pom.xml"]}},
            "moduleAnalysis": [{"module": "src", "guessedRole": "App", "confidence": "medium", "evidence": []}],
            "commandCandidates": [{"category": "build", "command": "mvn clean package", "confidence": "high", "evidence": []}],
            "architecturePattern": None,
            "anomalies": [],
            "calibrationPoints": [],
        })

    def test_two_calls_made(self) -> None:
        """Both round1 and round2 LLM calls are made."""
        caller = MagicMock(side_effect=[self._round1_response(), self._round2_response()])
        result = scan_with_llm(self._file_tree(), caller)
        assert caller.call_count == 2
        assert result["enabled"] is True
        assert result["stackAnalysis"]["primary"]["name"] == "Java / Spring Boot"

    def test_round2_failure_degradation(self) -> None:
        """If round2 returns None/invalid, fall back to round1."""
        caller = MagicMock(side_effect=[self._round1_response(), None])
        result = scan_with_llm(self._file_tree(), caller)
        assert result["enabled"] is True
        assert result["stackAnalysis"]["primary"]["name"] == "Java"
        assert result.get("selfCheckDegraded") is True

    def test_no_caller_degradation(self) -> None:
        """If caller is None, return disabled analysis without exception."""
        result = scan_with_llm(self._file_tree(), None)
        assert result["enabled"] is False
        assert "stackAnalysis" not in result or result.get("stackAnalysis") is None

    def test_first_round_failure(self) -> None:
        """If round1 fails, return disabled/error fallback."""
        caller = MagicMock(return_value=None)
        result = scan_with_llm(self._file_tree(), caller)
        assert result["enabled"] is False


def test_parse_rejects_missing_required_keys() -> None:
    """Malformed LLM JSON missing the scanner contract should be rejected."""
    result = parse_scan_response(json.dumps({"stackAnalysis": {"primary": {"name": "Java"}}}))
    assert result is None


def test_merge_rounds_handles_non_dict_module_entries() -> None:
    """Real LLMs may return moduleAnalysis entries as strings; merging should not crash."""
    round1 = {
        "stackAnalysis": {},
        "moduleAnalysis": ["src"],
        "commandCandidates": [],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    }
    round2 = {
        "stackAnalysis": {},
        "moduleAnalysis": [{"module": "tests", "guessedRole": "Tests"}],
        "commandCandidates": [],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    }

    merged = merge_rounds(round1, round2)

    assert "src" in merged["moduleAnalysis"]
    assert {"module": "tests", "guessedRole": "Tests"} in merged["moduleAnalysis"]
