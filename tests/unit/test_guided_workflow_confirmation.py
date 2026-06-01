from __future__ import annotations

from harness_builder_agent.tools import interactive_init


def test_guided_workflow_confirmation_shows_standard_escalation(monkeypatch, capsys):
    monkeypatch.setattr(interactive_init.typer, "prompt", lambda *args, **kwargs: "")

    confirmation = interactive_init._show_workflows()

    output = capsys.readouterr().out
    assert "standard" in output
    assert "高风险" in output
    assert "跨模块" in output
    assert "安全" in output
    assert confirmation.shown_workflows == ["lightweight", "bugfix", "standard"]
    assert confirmation.confirmed is True
    assert confirmation.routing_policy_effect == "not_applicable"
