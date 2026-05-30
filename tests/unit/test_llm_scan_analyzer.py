from __future__ import annotations

import os
import json
import re
from pathlib import Path
from unittest import mock

import pytest

from harness_builder_agent.schemas.scan import EvidenceBundle
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig
from harness_builder_agent.tools.llm_scan_analyzer import analyze_evidence_with_llm, build_scan_messages, parse_llm_scan_response

SCAN_PROMPT_ASSET = Path("src/harness_builder_agent/prompts/llm_first_scan_v2.md")
LLM_SCAN_ANALYZER_SOURCE = Path("src/harness_builder_agent/tools/llm_scan_analyzer.py")


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


def test_parse_llm_scan_response_rejects_non_canonical_primary_stack():
    payload = json.loads(_proposal_json())
    payload["primary_stack"] = "Spring Boot"

    with pytest.raises(ValueError, match="schema"):
        parse_llm_scan_response(json.dumps(payload))


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


def test_deepseek_config_default_max_tokens_handles_real_scan_json(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.delenv("HARNESS_BUILDER_LLM_MAX_TOKENS", raising=False)

    config = DeepSeekConfig.from_env(load_dotenv=False)

    assert config.max_tokens == 8192


def test_scan_prompt_asset_exists_and_preserves_machine_contract():
    assert SCAN_PROMPT_ASSET.exists()

    prompt = SCAN_PROMPT_ASSET.read_text(encoding="utf-8")

    assert len(re.findall(r"[\u4e00-\u9fff]", prompt)) > 100
    for required in [
        "primary_stack",
        "java-spring",
        "dotnet-aspnet",
        "node",
        "unknown",
        "command_candidates",
        "build",
        "test",
        "lint",
        "typecheck",
        "hard",
        "soft",
        "low",
        "medium",
        "high",
    ]:
        assert required in prompt


def test_build_scan_messages_uses_scan_prompt_asset():
    asset_prompt = SCAN_PROMPT_ASSET.read_text(encoding="utf-8").strip()

    messages = build_scan_messages(_bundle())
    user_message = next(message["content"] for message in messages if message["role"] == "user")
    analyzer_source = LLM_SCAN_ANALYZER_SOURCE.read_text(encoding="utf-8")

    assert "## User Message" in asset_prompt
    assert "机器契约字段" in user_message
    assert user_message.index("机器契约字段") < user_message.index("Evidence JSON:")
    assert "Stack decision rules:" not in analyzer_source
    assert "Example JSON shape:" not in analyzer_source


def test_scan_prompt_asset_provides_chinese_system_message():
    asset_prompt = SCAN_PROMPT_ASSET.read_text(encoding="utf-8")

    messages = build_scan_messages(_bundle())
    system_message = next(message["content"] for message in messages if message["role"] == "system")
    analyzer_source = LLM_SCAN_ANALYZER_SOURCE.read_text(encoding="utf-8")

    assert "## System Message" in asset_prompt
    assert "Harness Builder 的扫描分析器" in system_message
    assert "证据不足" in system_message
    assert "You are the scan analyzer" not in analyzer_source


def test_scan_prompt_contains_strict_json_schema_example():
    messages = build_scan_messages(_bundle())
    combined = "\n".join(message["content"] for message in messages)

    assert "json" in combined.lower()
    assert '"primary_stack": "java-spring"' in combined
    assert '"gate": "hard"' in combined
    assert "primary_stack" in combined
    assert "confidence" in combined


def test_scan_prompt_contains_stack_decision_rules():
    messages = build_scan_messages(_bundle())
    combined = "\n".join(message["content"] for message in messages)

    assert "栈判断" in combined
    assert "spring-boot-starter" in combined
    assert "DemoController" in combined
    assert "ASP.NET Core" in combined


def test_scan_prompt_explains_coverage_and_priority_evidence():
    bundle = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        priority_files=[{"path": "pom.xml", "kind": "build", "priority": "critical", "bucket": "build"}],
        test_files=[{"path": "quality/checks/UserFlowSpec.cs", "kind": "test", "priority": "high", "bucket": "test"}],
        api_entrypoints=[
            {
                "path": "src/api/UserController.java",
                "kind": "api_entrypoint",
                "priority": "critical",
                "bucket": "api_entrypoint",
            }
        ],
        coverage={
            "detected_file_count": 50,
            "selected_evidence_count": 3,
            "bucket_coverage": [],
            "warnings": [{"code": "source_sampling_truncated", "message": "source skipped"}],
        },
    )

    combined = "\n".join(message["content"] for message in build_scan_messages(bundle))

    assert "coverage" in combined.lower()
    assert "priority_files" in combined
    assert "test_files" in combined
    assert "api_entrypoints" in combined
    assert "不要因为缺少标准 tests 目录就断定没有测试" in combined


def test_scan_prompt_omits_null_evidence_fields():
    bundle = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[{"path": "src/App.java", "kind": "file"}],
    )

    combined = "\n".join(message["content"] for message in build_scan_messages(bundle))

    assert '"summary":null' not in combined
    assert '"reason":null' not in combined
    assert '"bucket":null' not in combined


def test_call_deepseek_requests_json_object_response(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "{}"}}]}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("harness_builder_agent.tools.deepseek_client.urllib.request.urlopen", fake_urlopen)

    content = call_deepseek(
        [{"role": "user", "content": "return json"}],
        config=DeepSeekConfig(api_key="sk-test", model="deepseek-test", timeout_seconds=12),
    )

    assert content == "{}"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert captured["timeout"] == 12
