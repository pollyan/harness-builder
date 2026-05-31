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
