from harness_builder_agent.schemas.command_catalog import CommandDefinition
from harness_builder_agent.schemas.interaction_decision import WorkflowConfirmation
from harness_builder_agent.tools.guided_supplement_presentation import (
    scan_override_brief,
    show_scan_supplement_immediate_summary,
    show_scan_supplement_replacement_summary,
    show_supplement_impact_summary,
    show_team_rules_back_revision_notice,
    show_team_rules_cleared_summary,
    show_team_rules_immediate_summary,
    show_workflow_note_cleared_summary,
    show_workflow_note_immediate_summary,
)
from harness_builder_agent.tools.prewrite_preview import GuidedScanOverrides


def test_scan_supplement_immediate_summary_explains_structured_effects(capsys):
    overrides = GuidedScanOverrides(
        notes=["批处理入口在 jobs/"],
        modules=[{"path": "jobs", "kind": "batch", "name": "Batch jobs"}],
        commands=[
            CommandDefinition(
                id="batch-test",
                command="make test-batch",
                type="test",
                gate="hard",
                source="Makefile",
                confidence="high",
            )
        ],
        risk_areas=[{"path": "jobs/payments", "reason": "支付批处理风险高"}],
    )

    show_scan_supplement_immediate_summary(overrides)

    output = capsys.readouterr().out
    assert "扫描补充理解" in output
    assert "批处理入口在 jobs/" in output
    assert "结构化模块：`jobs`（batch，Batch jobs）" in output
    assert "结构化验证命令：`make test-batch`，gate=hard，source=`Makefile`" in output
    assert "结构化风险区域：`jobs/payments`，支付批处理风险高" in output
    assert "扫描补充影响" in output
    assert "不会被伪装成已验证扫描事实" in output


def test_scan_supplement_replacement_summary_uses_current_effective_overrides(capsys):
    previous = GuidedScanOverrides(notes=["旧补充"], modules=[{"path": "old", "kind": "module", "name": "Old"}])
    current = GuidedScanOverrides(primary_stack="node", commands=[
        CommandDefinition(
            id="unit",
            command="npm test",
            type="test",
            gate="hard",
            source="package.json",
            confidence="high",
        )
    ])

    show_scan_supplement_replacement_summary(previous, current)

    output = capsys.readouterr().out
    assert "扫描补充替换结果" in output
    assert "上一版补充：modules=old；notes=旧补充" in output
    assert "当前生效补充：stack=node；commands=unit" in output
    assert "上一版补充不会进入 project inventory、command catalog、Guides、Sensors 或 init summary" in output
    assert scan_override_brief(current) == "stack=node；commands=unit"


def test_team_rules_summary_back_and_clear_messages(capsys):
    show_team_rules_immediate_summary(["Controller 只能调用 Service"])
    show_team_rules_back_revision_notice(["旧团队规则一", "旧团队规则二", "旧团队规则三"])
    show_team_rules_cleared_summary()

    output = capsys.readouterr().out
    assert "团队规则理解" in output
    assert "团队规则：Controller 只能调用 Service" in output
    assert "团队规则返回修改" in output
    assert "上一版团队规则摘要：旧团队规则一；旧团队规则二；还有 1 条" in output
    assert "团队规则已清空" in output


def test_workflow_note_summary_and_clear_messages(capsys):
    confirmation = WorkflowConfirmation(notes=["权限变更必须走 standard workflow"])

    show_workflow_note_immediate_summary(confirmation)
    show_workflow_note_cleared_summary()

    output = capsys.readouterr().out
    assert "Workflow 补充理解" in output
    assert "权限变更必须走 standard workflow" in output
    assert "不直接修改正式 workflow routing policy" in output
    assert "Workflow 补充已清空" in output


def test_supplement_impact_summary_combines_scan_team_and_workflow(capsys):
    overrides = GuidedScanOverrides(
        notes=["支付模块风险最高"],
        modules=[{"path": "payments", "kind": "domain", "name": "Payments"}],
        risk_areas=[{"path": "payments", "reason": "资金风险"}],
    )
    workflow = WorkflowConfirmation(notes=["跨模块任务需要人工确认"])

    show_supplement_impact_summary(overrides, ["团队规则：先补测试"], workflow)

    output = capsys.readouterr().out
    assert "已吸收的用户补充" in output
    assert "扫描补充：支付模块风险最高" in output
    assert "团队规则：团队规则：先补测试" in output
    assert "Workflow 补充：跨模块任务需要人工确认" in output
    assert "补充影响" in output
    assert "补充风险 `payments` 会进入项目风险线索" in output
