from __future__ import annotations

from types import SimpleNamespace

import pytest

from harness_builder_agent.tools.guided_candidate_review import review_candidates


class FakeCandidateReport:
    def __init__(self, candidates: list[dict[str, object]]) -> None:
        self._candidates = candidates

    def model_dump(self, *, mode: str) -> dict[str, object]:
        assert mode == "json"
        return {"candidates": self._candidates}


def _weapon_selection():
    return SimpleNamespace(
        guide_weapons=[
            SimpleNamespace(
                title="项目边界",
                guidance="说明主要模块和上下文。",
                evidence_hints=["pom.xml", "src/main/java"],
            )
        ],
        sensor_weapons=[
            SimpleNamespace(
                title="验证入口",
                guidance="声明测试命令和失败处理。",
                gate="hard",
            )
        ],
    )


def _commands():
    return SimpleNamespace(
        commands=[
            SimpleNamespace(
                command="mvn test",
                source="pom.xml",
                gate="hard",
            )
        ]
    )


def test_review_candidates_renders_baseline_and_returns_empty_when_no_llm_candidates(capsys: pytest.CaptureFixture[str]):
    prompts: list[str] = []

    def prompt(message: str, **_kwargs: object) -> str:
        prompts.append(message)
        return "k"

    decisions = review_candidates(FakeCandidateReport([]), _weapon_selection(), _commands(), prompt=prompt)

    assert decisions == []
    assert prompts == []
    output = capsys.readouterr().out
    assert "建议生成的规则" in output
    assert "- 项目边界：说明主要模块和上下文。 来源线索：pom.xml, src/main/java" in output
    assert "建议生成的传感器" in output
    assert "- 验证入口：声明测试命令和失败处理。 建议 gate=`hard`" in output
    assert "- 现有命令 `mvn test`：来自 `pom.xml`，当前 gate=`hard`" in output
    assert "模型没有提出额外候选项。" in output


def test_review_candidates_records_accept_reject_edit_and_default_keep(capsys: pytest.CaptureFixture[str]):
    responses = iter(["a", "r", "e", "需要先确认 CI 稳定性。", ""])
    prompt_calls: list[tuple[str, dict[str, object]]] = []

    def prompt(message: str, **kwargs: object) -> str:
        prompt_calls.append((message, kwargs))
        return next(responses)

    report = FakeCandidateReport(
        [
            {
                "id": "llm-guide-architecture-001",
                "title": "架构边界",
                "candidate_type": "guide",
                "rationale": "补充模块职责。",
                "evidence": ["src/main/java"],
            },
            {
                "id": "llm-guide-risk-001",
                "title": "风险模块",
                "candidate_type": "guide",
                "rationale": "标记支付风险。",
                "evidence": [],
            },
            {
                "id": "llm-sensor-command-001",
                "title": "CI 测试",
                "candidate_type": "sensor",
                "rationale": "确认测试入口。",
                "evidence": ["pom.xml"],
            },
            {
                "id": "llm-sensor-keep-001",
                "title": "保持候选",
                "candidate_type": "sensor",
                "rationale": "等待后续确认。",
                "evidence": ["README.md"],
            },
        ]
    )

    decisions = review_candidates(report, _weapon_selection(), _commands(), prompt=prompt)

    assert [(item.candidate_id, item.decision, item.notes) for item in decisions] == [
        ("llm-guide-architecture-001", "accepted", "用户在 guided init 中接受。"),
        ("llm-guide-risk-001", "rejected", "用户在 guided init 中拒绝。"),
        ("llm-sensor-command-001", "edited", "需要先确认 CI 稳定性。"),
        ("llm-sensor-keep-001", "kept", "保持候选，等待后续确认。"),
    ]
    assert prompt_calls == [
        ("你的选择", {"default": "k"}),
        ("你的选择", {"default": "k"}),
        ("你的选择", {"default": "k"}),
        ("请输入备注", {"default": "", "show_default": False}),
        ("你的选择", {"default": "k"}),
    ]
    output = capsys.readouterr().out
    assert "逐项审查模型候选" in output
    assert "`llm-guide-architecture-001`：架构边界" in output
    assert "类型：规则 Guide" in output
    assert "类型：传感器 Sensor" in output
    assert "依据：暂无" in output
    assert "成熟度影响：补齐 Guides 上下文" in output
    assert "成熟度影响：补齐 Guides 上下文、Risk Control 风险控制" in output
    assert "成熟度影响：补齐 Sensors 验证、Verification 验证成熟度" in output
    assert "审查边界：保持 review-only；接受只记录确认，不会自动写入正式 Guide 或 Sensor。" in output


def test_review_candidates_explains_no_enhancement_as_audit_boundary(capsys: pytest.CaptureFixture[str]):
    def prompt(_message: str, **_kwargs: object) -> str:
        return ""

    report = FakeCandidateReport(
        [
            {
                "id": "llm-guide-no-enhancement-001",
                "title": "未发现明确模型增强建议",
                "candidate_type": "guide",
                "rationale": "LLM scan proposal 未提供 architecture_signals、risk_areas 或 command_candidates。",
                "evidence": ["java-spring"],
            }
        ]
    )

    decisions = review_candidates(report, _weapon_selection(), _commands(), prompt=prompt)

    assert decisions[0].decision == "kept"
    output = capsys.readouterr().out
    assert "成熟度影响：未发现明确增强项；保留候选审计边界，提醒 Maintainer 复核 LLM scan 是否遗漏 Guide / Sensor 线索。" in output
    assert "审查边界：保持 review-only；接受只记录确认，不会自动写入正式 Guide 或 Sensor。" in output
