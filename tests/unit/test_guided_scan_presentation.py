from pathlib import Path

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.guided_scan_presentation import (
    guided_scan_progress,
    risk_attention_lines,
    show_llm_evidence_expansion,
    show_scan_maturity_snapshot,
    uncertainty_attention_lines,
    verification_gap_lines,
)
from harness_builder_agent.tools.scan_repo import ScanProgressEvent


def test_show_llm_evidence_expansion_highlights_low_confidence(capsys):
    inventory = ProjectInventory(
        repo_name="demo",
        root_path="/tmp/demo",
        primary_stack="java-spring",
        stack_extensions={
            "scan_metadata": {
                "evidence_expansion": {
                    "requested_paths": ["src/main/java/App.java"],
                    "risk_focus": ["核心入口"],
                    "read_paths": ["src/main/java/App.java"],
                    "rationale": "需要确认入口和风险边界。",
                    "confidence": "low",
                }
            }
        },
    )

    show_llm_evidence_expansion(inventory)

    output = capsys.readouterr().out
    assert "LLM 深度补充" in output
    assert "`src/main/java/App.java`" in output
    assert "置信度：low，需要人工确认" in output


def test_scan_attention_line_helpers_explain_risk_uncertainty_and_verification_gap():
    inventory = ProjectInventory(
        repo_name="demo",
        root_path="/tmp/demo",
        primary_stack="unknown",
        modules=[],
        stack_extensions={
            "needs_human_confirmation": True,
            "llm_scan_proposal": {"confidence": "low"},
            "risk_areas": [{"path": "src/main/java/payments", "reason": "支付权限风险"}],
            "scan_warnings": [{"code": "test_evidence_not_found"}],
        },
    )
    commands = CommandCatalog(
        commands=[
            CommandDefinition(
                id="unit",
                command="mvn test",
                type="test",
                gate="hard",
                source="",
                confidence="low",
            )
        ]
    )

    assert any("高风险" in line and "src/main/java/payments" in line for line in risk_attention_lines(inventory))
    assert any("LLM 扫描置信度为 low" in line for line in uncertainty_attention_lines(inventory, commands))
    assert any("当前扫描未找到明确测试证据" in line for line in uncertainty_attention_lines(inventory, commands))
    assert any("hard gate 证据不足" in line for line in verification_gap_lines(commands))


def test_show_scan_maturity_snapshot_keeps_l0_storyline(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    inventory = ProjectInventory(repo_name="demo", root_path=str(repo), primary_stack="java-spring")
    commands = CommandCatalog(commands=[])

    show_scan_maturity_snapshot(repo, inventory, commands)

    output = capsys.readouterr().out
    assert "扫描后的成熟度初评" in output
    assert "当前从 L0 起步" in output
    assert "按当前扫描写入后预计建立" in output
    assert "建议优先补充" in output


def test_guided_scan_progress_renders_started_and_completed(capsys):
    guided_scan_progress(
        ScanProgressEvent(phase="collect-evidence", status="started", message="Collecting repository evidence.")
    )
    guided_scan_progress(
        ScanProgressEvent(phase="collect-evidence", status="completed", message="Collected repository evidence.")
    )

    output = capsys.readouterr().out
    assert "- 当前阶段：收集仓库 evidence" in output
    assert "  已完成：收集仓库 evidence" in output
