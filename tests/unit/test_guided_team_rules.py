from __future__ import annotations

import pytest

from harness_builder_agent.tools.guided_team_rules import collect_team_rules


def test_collect_team_rules_guides_user_with_constraint_categories(capsys: pytest.CaptureFixture[str]):
    prompt_calls: list[tuple[str, dict[str, object]]] = []

    def prompt(message: str, **kwargs: object) -> str:
        prompt_calls.append((message, kwargs))
        return "Controller 只能调用 Service；配置变更必须说明回滚方式。"

    rules = collect_team_rules(prompt=prompt)

    assert rules == ["Controller 只能调用 Service；配置变更必须说明回滚方式。"]
    assert prompt_calls == [("可以输入一段规则说明；暂时没有则直接回车", {"default": "", "show_default": False})]
    output = capsys.readouterr().out
    assert "团队规则" in output
    assert "建议优先补充这些隐性约束" in output
    assert "架构边界 / 模块分层" in output
    assert "测试策略 / 必跑验证" in output
    assert "安全合规 / 数据权限" in output
    assert "发布回滚 / 环境限制" in output
    assert "禁止修改 / 只读区域" in output
    assert "这些内容会进入 Guides 与 human-input-needed" in output


def test_collect_team_rules_returns_empty_when_user_skips(capsys: pytest.CaptureFixture[str]):
    prompt_calls: list[tuple[str, dict[str, object]]] = []

    def prompt(message: str, **kwargs: object) -> str:
        prompt_calls.append((message, kwargs))
        return "   "

    rules = collect_team_rules(prompt=prompt)

    assert rules == []
    assert prompt_calls == [("可以输入一段规则说明；暂时没有则直接回车", {"default": "", "show_default": False})]
    assert "建议优先补充这些隐性约束" in capsys.readouterr().out
