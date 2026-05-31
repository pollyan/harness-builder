from __future__ import annotations

from pathlib import Path

import typer

from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.interaction_decisions import accepted_interactive_decisions, default_non_interactive_decisions
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates
from harness_builder_agent.tools.scan_repo import scan_repository
from harness_builder_agent.tools.write_assets import write_initial_assets


def run_non_interactive_init(repo: Path, context_paths: list[Path], trace: GenerationTrace) -> Path:
    trace.event("scan", "started", "Repository scan started.")
    inventory, commands = scan_repository(repo)
    trace.event(
        "scan",
        "completed",
        "Repository scan completed.",
        {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
    )
    decisions = default_non_interactive_decisions(str(repo), context_paths=[str(path) for path in context_paths])
    output_dir = write_initial_assets(
        repo,
        inventory,
        commands,
        trace=trace,
        context_paths=context_paths,
        interaction_decisions=decisions,
    )
    trace.finish("completed", {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)})
    return output_dir


def run_guided_init(repo: Path, context_paths: list[Path], trace: GenerationTrace) -> Path:
    typer.echo(f"仓库: {repo}")
    if not typer.confirm("继续生成 Harness?", default=True):
        trace.finish("failed", {"cancelled": True})
        raise typer.Abort()

    trace.event("scan", "started", "Repository scan started.")
    inventory, commands = scan_repository(repo)
    trace.event(
        "scan",
        "completed",
        "Repository scan completed.",
        {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
    )

    typer.echo("扫描结论")
    typer.echo(f"- primary_stack: {inventory.primary_stack}")
    typer.echo(f"- stacks: {', '.join(inventory.stacks)}")
    typer.echo(f"- commands: {len(commands.commands)}")
    if not typer.confirm("接受扫描结论?", default=True):
        trace.finish("failed", {"cancelled": True})
        raise typer.Abort()

    inline_contexts: list[str] = []
    if typer.confirm("是否补充团队 context?", default=False):
        inline = typer.prompt("请输入团队 context 摘要", default="")
        if inline.strip():
            inline_contexts.append(inline.strip())

    candidate_report = build_llm_enhancement_candidates(inventory, commands)
    candidate_ids = [item.id for item in candidate_report.candidates]
    typer.echo(f"候选 Guide/Sensor: {len(candidate_ids)}")
    candidate_choice = typer.prompt("候选处理方式: a=全部接受, k=保持候选", default="k").strip().lower()
    accept_candidates = candidate_choice == "a"

    if not typer.confirm("确认写入 Harness 资产?", default=True):
        trace.finish("failed", {"cancelled": True})
        raise typer.Abort()

    decisions = accepted_interactive_decisions(
        str(repo),
        context_paths=[str(path) for path in context_paths],
        inline_contexts=inline_contexts,
        candidate_ids=candidate_ids,
        accept_candidates=accept_candidates,
    )
    output_dir = write_initial_assets(
        repo,
        inventory,
        commands,
        trace=trace,
        context_paths=context_paths,
        interaction_decisions=decisions,
    )
    trace.finish("completed", {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)})
    return output_dir
