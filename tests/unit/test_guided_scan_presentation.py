from pathlib import Path

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.guided_scan_presentation import (
    guided_scan_progress,
    risk_attention_lines,
    show_scan_attention_summary,
    show_llm_evidence_expansion,
    show_scan_maturity_snapshot,
    uncertainty_attention_lines,
    verification_gap_lines,
    show_scan_progress_failed,
    show_scan_progress_start,
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


def test_scan_progress_start_shows_llm_config_and_ordered_phase_plan(monkeypatch, tmp_path: Path, capsys):
    monkeypatch.setenv("HARNESS_BUILDER_LLM_MODEL", "deepseek-test")
    monkeypatch.setenv("HARNESS_BUILDER_LLM_TIMEOUT_SECONDS", "75")

    show_scan_progress_start(tmp_path)

    output = capsys.readouterr().out
    assert "LLM 扫描配置" in output
    assert "provider: DeepSeek" in output
    assert "model: deepseek-test" in output
    assert "timeout: 75s" in output
    assert "预计 LLM 调用：evidence planner、scan analyzer，必要时 scan self-check" in output
    assert "扫描阶段计划" in output
    assert "1. 收集仓库 evidence" in output
    assert "2. 请求 LLM 规划补充 evidence" in output
    assert "5. 调和扫描结果" in output
    assert "正在请求 LLM 做结构化扫描" not in output


def test_guided_scan_progress_completed_prints_evidence_and_prompt_diagnostics(capsys):
    guided_scan_progress(
        ScanProgressEvent(
            phase="collect-evidence",
            status="completed",
            message="Collected repository evidence.",
            details={
                "evidence_file_count": 1686,
                "selected_evidence_count": 388,
                "llm_input_chars": 1_159_745,
            },
        )
    )

    output = capsys.readouterr().out
    assert "已完成：收集仓库 evidence" in output
    assert "发现 1686 个文件" in output
    assert "选中 388 个 evidence" in output
    assert "预计 LLM 输入约 1.1MB" in output
    assert "检测到大仓库扫描" in output


def test_scan_progress_failed_prints_phase_diagnostics_and_retry_hint(tmp_path: Path, capsys):
    show_scan_progress_failed(
        TimeoutError("The read operation timed out"),
        error_message="The read operation timed out",
        failed_phase="plan-evidence-expansion",
        failed_phase_details={
            "llm_input_chars": 1_159_745,
            "model": "deepseek-v4-pro",
            "timeout_seconds": 60,
        },
        trace_path=tmp_path / ".ai" / "runs" / "run-1" / "trace.yaml",
        repo=tmp_path,
    )

    output = capsys.readouterr().out
    assert "失败阶段：LLM evidence planner" in output
    assert "DeepSeek 请求在 60s 内未返回" in output
    assert "当前模型：deepseek-v4-pro" in output
    assert "本次 LLM 输入估算：约 1.1MB" in output
    assert "Trace：" in output
    assert "HARNESS_BUILDER_LLM_TIMEOUT_SECONDS=180" in output


def test_scan_attention_summary_turns_followups_into_answer_guidance(capsys):
    inventory = ProjectInventory(
        repo_name="demo",
        root_path="/tmp/demo",
        primary_stack="unknown",
        modules=[],
        stack_extensions={
            "scan_metadata": {
                "followup_questions": [
                    {
                        "interaction_id": "confirm:scan-followup:coverage-source-java",
                        "trigger": "coverage_gap",
                        "question": "哪些 Java 目录需要补充扫描？",
                        "reason": "抽样不足。",
                        "confidence": "low",
                        "affects": ["guides"],
                    },
                    {
                        "interaction_id": "confirm:scan-followup:stack-node",
                        "trigger": "stack_claim_without_evidence",
                        "question": "是否存在 Node 子模块？",
                        "reason": "缺少 stack evidence。",
                        "confidence": "low",
                        "affects": ["workflow"],
                    },
                    {
                        "interaction_id": "confirm:scan-followup:unknown-stack",
                        "trigger": "unknown_stack",
                        "question": "真实主技术栈是什么？",
                        "reason": "primary stack unknown。",
                        "confidence": "low",
                        "affects": ["maturity"],
                    },
                    {
                        "interaction_id": "confirm:scan-followup:module-boundary",
                        "trigger": "module_boundary_unclear",
                        "question": "主要模块路径和职责是什么？",
                        "reason": "模块边界不清。",
                        "confidence": "low",
                        "affects": ["guides"],
                    },
                    {
                        "interaction_id": "confirm:scan-followup:test-evidence",
                        "trigger": "test_evidence_missing",
                        "question": "真实测试入口是什么？",
                        "reason": "缺少测试 evidence。",
                        "confidence": "low",
                        "affects": ["sensors"],
                    },
                ]
            }
        },
    )

    show_scan_attention_summary(inventory, CommandCatalog(commands=[]))

    output = capsys.readouterr().out
    assert "深度追问回答建议" in output
    assert "`confirm:scan-followup:coverage-source-java`" in output
    assert "module=src/main/java|backend|核心模块" in output
    assert "risk=src/main/java/payments|支付或权限高风险" in output
    assert "`confirm:scan-followup:stack-node`" in output
    assert "stack=java-spring" in output
    assert "`confirm:scan-followup:test-evidence`" in output
    assert "command=unit_test|mvn test|test|hard|pom.xml|high" in output
    assert "不会自动关闭追问" in output
