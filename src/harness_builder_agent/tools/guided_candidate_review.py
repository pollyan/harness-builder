from __future__ import annotations

from collections.abc import Callable
from typing import Any

import typer

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.interaction_decision import CandidateDecision
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection


Prompt = Callable[..., str]


def review_candidates(
    report: Any,
    weapon_selection: WeaponLibrarySelection,
    commands: CommandCatalog,
    *,
    prompt: Prompt = typer.prompt,
) -> list[CandidateDecision]:
    typer.echo("\n建议生成的规则")
    typer.echo("这些规则会进入 Guide，影响后续 AI 如何理解项目边界和编码约束。")
    for weapon in weapon_selection.guide_weapons:
        typer.echo(f"- {weapon.title}：{weapon.guidance} 来源线索：{', '.join(weapon.evidence_hints) or '通用基线'}")

    typer.echo("\n建议生成的传感器")
    typer.echo("Sensor 用来描述验证活动。hard gate 失败时不应该声明任务完成，soft gate 则作为风险提示。")
    for weapon in weapon_selection.sensor_weapons:
        typer.echo(f"- {weapon.title}：{weapon.guidance} 建议 gate=`{weapon.gate}`")
    for command in commands.commands:
        typer.echo(f"- 现有命令 `{command.command}`：来自 `{command.source}`，当前 gate=`{command.gate}`")

    decisions: list[CandidateDecision] = []
    candidates = report.model_dump(mode="json")["candidates"]
    if not candidates:
        typer.echo("\n模型没有提出额外候选项。")
        return decisions

    typer.echo("\n逐项审查模型候选")
    typer.echo("选项：a=接受为确认项，r=拒绝，k=保持候选，e=补充备注后保持候选。直接回车等同于 k。")
    for item in candidates:
        typer.echo(f"\n- `{item['id']}`：{item['title']}")
        typer.echo(f"  类型：{'规则 Guide' if item['candidate_type'] == 'guide' else '传感器 Sensor'}")
        typer.echo(f"  作用：{item['rationale']}")
        typer.echo(f"  依据：{', '.join(str(value) for value in item.get('evidence', [])) or '暂无'}")
        for line in candidate_maturity_impact_lines(item):
            typer.echo(f"  {line}")
        choice = prompt("你的选择", default="k").strip().lower()
        if choice == "a":
            decisions.append(CandidateDecision(candidate_id=item["id"], decision="accepted", notes="用户在 guided init 中接受。"))
        elif choice == "r":
            note = "用户在 guided init 中拒绝。"
            decisions.append(CandidateDecision(candidate_id=item["id"], decision="rejected", notes=note))
        elif choice == "e":
            note = prompt("请输入备注", default="", show_default=False).strip()
            decisions.append(CandidateDecision(candidate_id=item["id"], decision="edited", notes=note))
        else:
            decisions.append(CandidateDecision(candidate_id=item["id"], decision="kept", notes="保持候选，等待后续确认。"))
    return decisions


def candidate_maturity_impact_lines(item: dict[str, Any]) -> list[str]:
    candidate_id = str(item.get("id", ""))
    title = str(item.get("title", ""))
    rationale = str(item.get("rationale", ""))
    evidence = [str(value) for value in item.get("evidence", [])]
    haystack = " ".join([candidate_id, title, rationale, *evidence]).lower()

    if "no-enhancement" in candidate_id:
        return [
            "成熟度影响：未发现明确增强项；保留候选审计边界，提醒 Maintainer 复核 LLM scan 是否遗漏 Guide / Sensor 线索。",
            "审查边界：保持 review-only；接受只记录确认，不会自动写入正式 Guide 或 Sensor。",
        ]

    if item.get("candidate_type") == "sensor":
        dimensions = ["Sensors 验证", "Verification 验证成熟度"]
        contribution = "把待确认验证命令或验证活动留在人工审查队列，避免直接提升 hard gate。"
    else:
        dimensions = ["Guides 上下文"]
        if any(token in haystack for token in ("risk", "风险", "auth", "鉴权", "权限", "payment", "支付", "security", "安全")):
            dimensions.append("Risk Control 风险控制")
            contribution = "把风险区域或约束候选留给 Maintainer 审查，后续可连接 Guide、Sensor 和 Workflow 升级。"
        else:
            contribution = "把 LLM 发现的上下文候选留给 Maintainer 审查，后续可补齐项目 Guide 基线。"

    return [
        f"成熟度影响：补齐 {'、'.join(dimensions)}。",
        f"下一阶段贡献：{contribution}",
        "审查边界：保持 review-only；接受只记录确认，不会自动写入正式 Guide 或 Sensor。",
    ]
