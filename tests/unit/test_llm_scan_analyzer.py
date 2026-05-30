from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from harness_builder_agent.schemas.scan import EvidenceBundle
from harness_builder_agent.tools.llm_config import DeepSeekConfig
from harness_builder_agent.tools.llm_scan_analyzer import analyze_evidence_with_llm, parse_llm_scan_response


def _bundle() -> EvidenceBundle:
    return EvidenceBundle(repo_name="demo", root_path="/tmp/demo")


def _proposal_json() -> str:
    return (
        '{"primary_stack":"java-spring","stacks":["java","maven"],'
        '"modules":[{"name":"app","path":".","kind":"backend"}],'
        '"architecture_signals":["spring mvc"],"risk_areas":[],'
        '"command_candidates":[{"id":"unit_test","command":"mvn test","type":"test","gate":"hard","source":"pom.xml","confidence":"high"}],'
        '"configs":[],"ci_files":[],"confidence":"high","needs_human_confirmation":false,'
        '"reasoning_summary":"Maven project."}'
    )


def test_parse_llm_scan_response_accepts_json_fence():
    proposal = parse_llm_scan_response(f"```json\n{_proposal_json()}\n```")

    assert proposal.primary_stack == "java-spring"
    assert proposal.command_candidates[0].command == "mvn test"
    assert proposal.needs_human_confirmation is False


def test_parse_llm_scan_response_rejects_bad_json():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_llm_scan_response("not json")


def test_parse_llm_scan_response_rejects_schema_mismatch():
    with pytest.raises(ValueError, match="schema"):
        parse_llm_scan_response('{"primary_stack":"java-spring"}')


def test_analyze_evidence_rejects_empty_llm_response():
    def caller(_messages):
        return ""

    with pytest.raises(ValueError, match="empty"):
        analyze_evidence_with_llm(_bundle(), caller=caller)


def test_deepseek_config_requires_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("HARNESS_BUILDER_LLM_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        DeepSeekConfig.from_env(load_dotenv=False)


def test_deepseek_config_loads_local_dotenv_without_overriding_env(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEEPSEEK_API_KEY=from-file\nHARNESS_BUILDER_LLM_MODEL=deepseek-test\n",
        encoding="utf-8",
    )

    with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "from-env"}, clear=False):
        config = DeepSeekConfig.from_env(env_path=env_file)

    assert config.api_key == "from-env"
    assert config.model == "deepseek-test"
