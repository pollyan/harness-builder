from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.interaction_decision import WorkflowConfirmation
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.init_summary import build_init_summary_markdown, render_init_completion_message
from harness_builder_agent.tools.interaction_decisions import accepted_interactive_decisions


def _score() -> MaturityReport:
    return MaturityReport(
        overall_level="L2",
        target_next_level="L3",
        dimension_scores={"Sensors": "L2"},
        blocking_reasons=["缺少真实 benchmark 质量验收。"],
        recommended_next_steps=["运行 benchmark 验证第一版 Harness。"],
    )


def _inventory(repo: Path) -> ProjectInventory:
    return ProjectInventory(
        repo_name=repo.name,
        root_path=str(repo),
        primary_stack="java-spring",
        stacks=["java", "maven"],
        modules=[{"name": "app", "path": "src/main/java", "kind": "backend"}],
        evidence=[{"path": "pom.xml", "reason": "maven build file"}],
        stack_extensions={
            "risk_areas": [
                {"path": "src/main/resources/application.yml", "reason": "数据库配置需要人工确认"}
            ]
        },
    )


def _inventory_with_scan_audit(repo: Path) -> ProjectInventory:
    inventory = _inventory(repo)
    inventory.stack_extensions["scan_metadata"] = {
        "evidence_expansion": {
            "schema_version": "1.0",
            "planner_prompt_version": "llm-evidence-planner-v1",
            "requested_paths": ["src/main/java/com/example/demo/DemoController.java"],
            "risk_focus": ["controller routing"],
            "rationale": "Controller route ownership needed deeper inspection.",
            "confidence": "medium",
            "read_paths": ["src/main/java/com/example/demo/DemoController.java"],
            "read_file_count": 1,
        },
        "coverage": {
            "schema_version": "1.0",
            "detected_file_count": 12,
            "selected_evidence_count": 4,
            "bucket_coverage": [
                {
                    "bucket": "test",
                    "total_count": 2,
                    "selected_count": 1,
                    "skipped_count": 1,
                    "selected_paths": ["src/test/java/com/example/demo/DemoControllerTest.java"],
                },
                {
                    "bucket": "api_entrypoint",
                    "total_count": 1,
                    "selected_count": 1,
                    "skipped_count": 0,
                    "selected_paths": ["src/main/java/com/example/demo/DemoController.java"],
                },
            ],
            "warnings": [],
        },
    }
    return inventory


def _commands() -> CommandCatalog:
    return CommandCatalog(
        commands=[
            CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml"),
        ]
    )


def test_init_summary_reports_existing_benchmark_status(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "maturity-score.yaml").write_text(yaml.safe_dump(_score().model_dump(mode="json")), encoding="utf-8")
    (ai / "benchmark-report.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "profile": "java-spring",
                "status": "failed",
                "quality_status": "degraded",
                "checks": [
                    {"id": "schema:project-inventory", "passed": True},
                    {"id": "content:guides-quality", "passed": False},
                ],
                "quality_scores": {},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    markdown = build_init_summary_markdown(_score(), ai=ai)
    message = render_init_completion_message(ai)

    assert "## Benchmark 健康度" in markdown
    assert "benchmark_status=failed" in markdown
    assert "quality_status=degraded" in markdown
    assert "failed_checks=1" in markdown
    assert ".ai/benchmark-report.yaml" in markdown
    assert "Benchmark 健康度" in message
    assert "benchmark_status=failed" in message
    assert "quality_status=degraded" in message
    assert "failed_checks=1" in message


def test_init_completion_message_is_cli_first_delivery_summary(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "guides").mkdir()
    (ai / "sensors").mkdir()
    (ai / "skills").mkdir()
    (ai / "maturity-score.yaml").write_text(yaml.safe_dump(_score().model_dump(mode="json")), encoding="utf-8")
    (ai / "questionnaire.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "questions": [
                    {
                        "interaction_type": "context_confirmation",
                        "interaction_id": "confirm:team-context",
                        "question": "是否有团队规则需要加入 Harness？",
                        "options": ["补充", "暂缓"],
                        "confidence": "medium",
                        "reason": "团队规则会影响 Guides。",
                    }
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    decisions = accepted_interactive_decisions(
        str(tmp_path),
        inline_contexts=["团队规则：Controller 只能调用 Service"],
        scan_notes=["配置变更必须说明回滚方式"],
        workflow_confirmation=WorkflowConfirmation(
            shown_workflows=["bugfix", "standard"],
            confirmed=True,
            notes=["权限变更必须走 standard workflow"],
        ),
    )
    (ai / "interaction-decisions.yaml").write_text(
        yaml.safe_dump(decisions.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    message = render_init_completion_message(ai)

    assert "== 初始化完成 ==" in message
    assert "本次已生成" in message
    assert "当前成熟度" in message
    assert "主要证据 / 缺口" in message
    assert "Benchmark 健康度" in message
    assert "benchmark_status=not_run" in message
    assert "本次吸收的用户补充" in message
    assert "配置变更必须说明回滚方式" in message
    assert "Controller 只能调用 Service" in message
    assert "权限变更必须走 standard workflow" in message
    assert ".ai/interaction-decisions.yaml" in message
    assert ".ai/init-summary.md" in message
    assert "团队规则和 Workflow 补充不会被伪装成扫描事实或正式 routing policy" in message
    assert "优先查看" in message
    assert "仍需人工确认" in message
    assert "是否有团队规则需要加入 Harness" in message
    assert "本终端摘要是本次 init 的主要交付说明" in message
    assert ".ai/init-summary.md" in message
    assert ".ai/sensors/verification.md" in message
    assert message.index("当前成熟度：") < message.index("本次已生成：")
    assert message.index("建议下一步：") < message.index("本次已生成：")
    assert message.index("Benchmark 健康度：") < message.index("本次已生成：")
    assert message.index("优先查看：") < message.index("本次已生成：")
    next_steps = message[message.index("建议下一步：") : message.index("\n\nBenchmark 健康度：")]
    assert "1. 先运行 `harness-builder-agent benchmark --repo" in next_steps
    assert "2. 处理 `.ai/human-input-needed.md#处理方式` 中的待确认问题" in next_steps
    assert "3. 运行 benchmark 验证第一版 Harness。" in next_steps


def test_init_completion_message_reports_no_user_supplements(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "maturity-score.yaml").write_text(yaml.safe_dump(_score().model_dump(mode="json")), encoding="utf-8")
    decisions = accepted_interactive_decisions(str(tmp_path), workflow_confirmation=WorkflowConfirmation(shown_workflows=["bugfix"]))
    (ai / "interaction-decisions.yaml").write_text(
        yaml.safe_dump(decisions.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    message = render_init_completion_message(ai)

    assert "本次吸收的用户补充" in message
    assert "本次未提供人工补充" in message
    assert "后续可在已有 Harness 维护入口继续补齐" in message


def test_init_completion_message_compacts_many_user_supplements(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "maturity-score.yaml").write_text(yaml.safe_dump(_score().model_dump(mode="json")), encoding="utf-8")
    decisions = accepted_interactive_decisions(
        str(tmp_path),
        inline_contexts=["团队规则一：Controller 只能调用 Service", "团队规则二：Repository 不跨聚合访问"],
        scan_notes=["扫描补充一：批处理入口在 jobs/", "扫描补充二：支付模块风险最高", "扫描补充三：迁移脚本需人工复核"],
        workflow_confirmation=WorkflowConfirmation(
            shown_workflows=["bugfix", "standard"],
            confirmed=True,
            notes=["Workflow 补充一：权限变更必须走 standard", "Workflow 补充二：跨模块任务必须人工确认"],
        ),
    )
    (ai / "interaction-decisions.yaml").write_text(
        yaml.safe_dump(decisions.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    message = render_init_completion_message(ai)

    assert "扫描补充：3 条；示例：扫描补充一：批处理入口在 jobs/" in message
    assert "团队规则：2 条；示例：团队规则一：Controller 只能调用 Service" in message
    assert "Workflow 补充：2 条；示例：Workflow 补充一：权限变更必须走 standard" in message
    assert "扫描补充二：支付模块风险最高" not in message
    assert "团队规则二：Repository 不跨聚合访问" not in message
    assert "Workflow 补充二：跨模块任务必须人工确认" not in message
    assert ".ai/interaction-decisions.yaml" in message
    assert "完整交付摘要见 `.ai/init-summary.md`" in message
    assert "团队规则和 Workflow 补充不会被伪装成扫描事实或正式 routing policy" in message


def test_init_completion_message_reports_missing_interaction_decisions(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "maturity-score.yaml").write_text(yaml.safe_dump(_score().model_dump(mode="json")), encoding="utf-8")

    message = render_init_completion_message(ai)

    assert "本次吸收的用户补充" in message
    assert "interaction_decisions=missing" in message
    assert ".ai/interaction-decisions.yaml" in message


def test_init_completion_message_prioritizes_failed_benchmark_report(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "maturity-score.yaml").write_text(yaml.safe_dump(_score().model_dump(mode="json")), encoding="utf-8")
    (ai / "benchmark-report.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "profile": "java-spring",
                "status": "failed",
                "quality_status": "failed",
                "checks": [
                    {"id": "content:hard-gate-command-evidence", "passed": False},
                    {"id": "schema:project-inventory", "passed": True},
                ],
                "quality_scores": {},
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    message = render_init_completion_message(ai)

    next_steps = message[message.index("建议下一步：") : message.index("\n\nBenchmark 健康度：")]
    assert "1. 先查看 `.ai/benchmark-report.yaml` 并处理 1 个 failed check，再重新运行 benchmark。" in next_steps
    assert "2. 运行 benchmark 验证第一版 Harness。" in next_steps


def test_init_summary_links_pending_confirmations_to_action_entry(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "questionnaire.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "questions": [
                    {
                        "interaction_type": "scan_warning_confirmation",
                        "interaction_id": "confirm:scan-warning:test_evidence_not_found",
                        "question": "是否需要补充测试入口？",
                        "options": ["补充 command", "保持待确认"],
                        "confidence": "low",
                        "reason": "No dedicated test evidence bucket was found.",
                    },
                    {
                        "interaction_type": "context_confirmation",
                        "interaction_id": "confirm:team-context",
                        "question": "是否有团队规则需要加入 Harness？",
                        "options": ["补充", "暂缓"],
                        "confidence": "medium",
                        "reason": "团队规则会影响 Guides。",
                    },
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (ai / "maturity-score.yaml").write_text(yaml.safe_dump(_score().model_dump(mode="json")), encoding="utf-8")

    markdown = build_init_summary_markdown(_score(), ai=ai)
    message = render_init_completion_message(ai)

    assert "## 待人工确认" in markdown
    assert ".ai/human-input-needed.md#处理方式" in markdown
    assert "confirm:scan-warning:test_evidence_not_found" in markdown
    assert "confirm:team-context" in markdown
    assert "scan_warning_action:test_evidence_not_found" in markdown
    assert "command=ID|命令|test|hard|来源|置信度" in markdown
    assert ".ai/human-input-needed.md#处理方式" in message
    assert "scan_warning_action:test_evidence_not_found" in message


def test_init_summary_records_repository_facts_user_supplements_and_asset_gap_links(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    decisions = accepted_interactive_decisions(
        str(tmp_path),
        inline_contexts=["团队规则：Controller 只能调用 Service"],
        scan_notes=["配置变更必须说明回滚方式"],
        workflow_confirmation=WorkflowConfirmation(
            shown_workflows=["bugfix", "standard"],
            confirmed=True,
            notes=["权限变更必须走 standard workflow"],
        ),
    )

    markdown = build_init_summary_markdown(
        _score(),
        ai=ai,
        inventory=_inventory(tmp_path),
        commands=_commands(),
        interaction_decisions=decisions,
    )

    assert "## 本仓库关键事实" in markdown
    assert "## 本次吸收的用户补充" in markdown
    assert "## 资产如何补齐缺口" in markdown
    assert "src/main/java" in markdown
    assert "src/main/resources/application.yml" in markdown
    assert "数据库配置需要人工确认" in markdown
    assert "mvn test" in markdown
    assert "配置变更必须说明回滚方式" in markdown
    assert "Controller 只能调用 Service" in markdown
    assert "权限变更必须走 standard workflow" in markdown


def test_init_summary_records_scan_evidence_audit(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()

    markdown = build_init_summary_markdown(
        _score(),
        ai=ai,
        inventory=_inventory_with_scan_audit(tmp_path),
        commands=_commands(),
    )

    assert "## 扫描证据审计" in markdown
    assert "requested_paths=`src/main/java/com/example/demo/DemoController.java`" in markdown
    assert "read_paths=`src/main/java/com/example/demo/DemoController.java`" in markdown
    assert "risk_focus=`controller routing`" in markdown
    assert "confidence=`medium`" in markdown
    assert "read_file_count=1" in markdown
    assert "Controller route ownership needed deeper inspection." in markdown
    assert "evidence_selected=4/12" in markdown
    assert "selected_paths=`src/test/java/com/example/demo/DemoControllerTest.java`" in markdown
    assert "selected_paths=`src/main/java/com/example/demo/DemoController.java`" in markdown
