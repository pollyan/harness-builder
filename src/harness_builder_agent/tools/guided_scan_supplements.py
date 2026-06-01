from __future__ import annotations

from collections.abc import Callable

from harness_builder_agent.schemas.command_catalog import CommandDefinition
from harness_builder_agent.tools.prewrite_preview import GuidedScanOverrides


ALLOWED_STACKS = {"java-spring", "dotnet-aspnet", "node", "python-flask", "unknown"}
ALLOWED_COMMAND_TYPES = {"build", "test", "lint", "typecheck", "other"}
ALLOWED_COMMAND_GATES = {"hard", "soft"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}

StackResolver = Callable[[str], str]


def parse_guided_scan_supplement(
    answer: str,
    *,
    current_stack: str,
    stack_resolver: StackResolver | None = None,
) -> GuidedScanOverrides:
    overrides = GuidedScanOverrides()
    for part in [item.strip() for item in answer.split(";") if item.strip()]:
        key, separator, value = part.partition("=")
        if not separator:
            overrides.notes.append(part)
            continue

        key = key.strip().lower()
        value = value.strip()
        if key == "stack":
            _apply_stack_fragment(overrides, part, value, current_stack=current_stack, stack_resolver=stack_resolver)
        elif key == "module":
            _apply_module_fragment(overrides, part, value)
        elif key == "command":
            _apply_command_fragment(overrides, part, value)
        elif key == "risk":
            _apply_risk_fragment(overrides, part, value)
        else:
            overrides.notes.append(part)
    return overrides


def _apply_stack_fragment(
    overrides: GuidedScanOverrides,
    part: str,
    value: str,
    *,
    current_stack: str,
    stack_resolver: StackResolver | None,
) -> None:
    resolved = value
    if resolved not in ALLOWED_STACKS and stack_resolver is not None:
        resolved = stack_resolver(value).strip() or current_stack
    if resolved in ALLOWED_STACKS:
        overrides.primary_stack = resolved
        overrides.notes.append(f"用户将主要技术栈修正为：{resolved}")
        return
    overrides.notes.append(
        f"结构化 stack 片段未解析：{part}；未进入 primary stack override，只作为自然语言补充保留。"
    )


def _apply_module_fragment(overrides: GuidedScanOverrides, part: str, value: str) -> None:
    fields = [item.strip() for item in value.split("|")]
    if len(fields) >= 3 and all(fields[:3]):
        overrides.modules.append({"path": fields[0], "kind": fields[1], "name": fields[2]})
        overrides.notes.append(f"用户补充模块：{fields[0]}（{fields[1]}，{fields[2]}）")
        return
    overrides.notes.append(f"结构化 module 片段未解析：{part}；未进入 project inventory，只作为自然语言补充保留。")


def _apply_command_fragment(overrides: GuidedScanOverrides, part: str, value: str) -> None:
    fields = [item.strip() for item in value.split("|")]
    if (
        len(fields) >= 6
        and all(fields[:5])
        and fields[2] in ALLOWED_COMMAND_TYPES
        and fields[3] in ALLOWED_COMMAND_GATES
    ):
        confidence = fields[5] if fields[5] in ALLOWED_CONFIDENCE else "medium"
        overrides.commands.append(
            CommandDefinition(
                id=fields[0],
                command=fields[1],
                type=fields[2],
                gate=fields[3],
                source=fields[4],
                confidence=confidence,
            )
        )
        overrides.notes.append(f"用户补充验证命令：{fields[1]}，gate={fields[3]}")
        return
    overrides.notes.append(f"结构化 command 片段未解析：{part}；未进入 command catalog，只作为自然语言补充保留。")


def _apply_risk_fragment(overrides: GuidedScanOverrides, part: str, value: str) -> None:
    fields = [item.strip() for item in value.split("|", 1)]
    if len(fields) == 2 and all(fields):
        overrides.risk_areas.append({"path": fields[0], "reason": fields[1]})
        overrides.notes.append(f"用户补充风险区域：{fields[0]}，{fields[1]}")
        return
    overrides.notes.append(f"结构化 risk 片段未解析：{part}；未进入 risk hints，只作为自然语言补充保留。")
