from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire
from harness_builder_agent.tools.risk_signals import high_impact_risk_areas, risk_slug
from harness_builder_agent.tools.scan_followup_guidance import scan_followup_answer_guidance_text
from harness_builder_agent.tools.scan_self_check_actions import scan_self_check_action_hint

SUMMARY_LIMIT = 1200
SCAN_CONFIRMATION_TYPES = {
    "scan_warning_confirmation",
    "risk_area_confirmation",
    "evidence_expansion_confirmation",
    "scan_followup_confirmation",
}


def read_context_inputs(paths: list[Path]) -> dict[str, Any]:
    contexts = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        summary = text[:SUMMARY_LIMIT]
        contexts.append(
            {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "summary": summary,
                "truncated": len(text) > SUMMARY_LIMIT,
            }
        )
    return ContextInputs(contexts=contexts).model_dump(mode="json")


def build_questionnaire(
    context_inputs: dict[str, Any],
    scan_metadata: dict[str, Any],
    risk_areas: list[dict[str, Any]] | None = None,
    interaction_decisions: Any | None = None,
) -> dict[str, Any]:
    contexts = context_inputs.get("contexts", [])
    context_reason = (
        "当前 init 已收到外部团队上下文，请确认这些文档可以作为 Harness 生成依据。"
        if contexts
        else "当前 init 未收到外部团队上下文。"
    )
    questions = [
        {
            "interaction_type": "context_confirmation",
            "interaction_id": "confirm:team-context",
            "question": "是否有组织级架构规范、代码规范或测试策略需要加入 Harness？",
            "options": ["提供 --context 文档后重新运行 init", "暂时保持候选状态"],
            "confidence": "medium" if contexts else "low",
            "reason": context_reason,
        },
        {
            "interaction_type": "candidate_asset_confirmation",
            "interaction_id": "confirm:guide-candidates",
            "question": "是否将候选 Guides 提升为团队确认规则？",
            "options": ["保持 candidate", "人工确认后提升为 confirmed"],
            "confidence": "medium",
            "reason": "Guides 当前由扫描、武器库和模型建议生成，尚未经过维护者确认。",
        },
        {
            "interaction_type": "sensor_gate_confirmation",
            "interaction_id": "confirm:sensor-gates",
            "question": "当前 hard gate sensors 是否在开发机和 CI 中稳定可靠？",
            "options": ["保持当前 hard gate", "人工调整后再确认"],
            "confidence": "medium",
            "reason": "Sensor 命令来自扫描推断，需要维护者确认长期稳定性。",
        },
    ]
    for signal in high_impact_risk_areas(risk_areas or []):
        questions.append(
            {
                "interaction_type": "risk_area_confirmation",
                "interaction_id": f"confirm:high-risk:{risk_slug(signal.path)}",
                "question": f"是否将 `{signal.path}` 作为待确认高风险边界处理？",
                "options": ["保持待确认并进入 standard workflow / 人工升级", "人工确认后调整风险边界"],
                "confidence": "low",
                "reason": f"{signal.confirmation_reason} 扫描原因：{signal.reason}",
            }
        )
    evidence_expansion = scan_metadata.get("evidence_expansion")
    if isinstance(evidence_expansion, dict) and evidence_expansion.get("confidence") == "low":
        requested = _format_items(evidence_expansion.get("requested_paths", []))
        read = _format_items(evidence_expansion.get("read_paths", []))
        focus = _format_items(evidence_expansion.get("risk_focus", []))
        rationale = str(evidence_expansion.get("rationale") or "LLM evidence planner 标记补读计划置信度较低。")
        questions.append(
            {
                "interaction_type": "evidence_expansion_confirmation",
                "interaction_id": "confirm:evidence-expansion",
                "question": f"LLM 深度补充读取的路径是否代表真实关键模块或风险边界？{requested}",
                "options": ["确认这些路径可作为关键 evidence", "人工补充或修正关键路径"],
                "confidence": "low",
                "reason": f"规划原因：{rationale}；关注点：{focus}；实际读取：{read}",
            }
        )
    represented_warning_codes: set[str] = set()
    if isinstance(evidence_expansion, dict) and evidence_expansion.get("confidence") == "low":
        represented_warning_codes.add("llm_evidence_plan_low_confidence")
    self_check_resolutions = _self_check_resolutions_by_interaction_id(scan_metadata.get("self_check"))
    for followup in scan_metadata.get("followup_questions", []):
        if not isinstance(followup, dict):
            continue
        represented_warning_codes.update(_warning_codes_represented_by_followup(str(followup.get("trigger") or "")))
        affects = _format_plain_items(followup.get("affects", []))
        reason = f"{followup.get('reason') or '扫描阶段存在需要补救的不确定性。'} 影响：{affects}"
        resolution = self_check_resolutions.get(str(followup.get("interaction_id") or ""))
        if resolution:
            status = resolution.get("status") or "needs_human_confirmation"
            action_type = resolution.get("suggested_action_type") or "maintainer_review"
            action = resolution.get("suggested_next_action") or "请人工确认该追问。"
            rationale = resolution.get("rationale") or "LLM 二次自检未提供理由。"
            action_hint = scan_self_check_action_hint(str(action_type))
            reason = (
                f"{reason} LLM 二次自检：{status}；action_type={action_type}；"
                f"动作提示：{action_hint}；建议：{action}；理由：{rationale}"
            )
        response_status, response_sources = _scan_supplement_followup_response(followup, interaction_decisions)
        supplement_note = _scan_supplement_followup_note(response_sources)
        if supplement_note:
            reason = f"{reason} {supplement_note}"
        questions.append(
            {
                "interaction_type": "scan_followup_confirmation",
                "interaction_id": str(followup.get("interaction_id") or "confirm:scan-followup:unknown"),
                "question": str(followup.get("question") or "是否需要补充扫描不确定性？"),
                "options": ["补充或修正相关信息", "暂时接受当前不确定性"],
                "confidence": str(followup.get("confidence") or "low"),
                "reason": reason,
                "response_status": response_status,
                "response_sources": response_sources,
            }
        )
    for warning in scan_metadata.get("warnings", []):
        code = warning.get("code", "unknown")
        if code in represented_warning_codes:
            continue
        questions.append(
            {
                "interaction_type": "scan_warning_confirmation",
                "interaction_id": f"confirm:scan-warning:{code}",
                "question": f"是否需要处理扫描警告：{warning.get('message', code)}？",
                "options": ["接受当前降级处理", "人工修正 Harness 资产"],
                "confidence": "low",
                "reason": warning.get("message", "扫描阶段产生 warning，需要人工确认。"),
            }
        )
    return Questionnaire(questions=questions).model_dump(mode="json")


def _format_items(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "无"
    return "、".join(f"`{item}`" for item in value[:5])


def _format_plain_items(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "无"
    return ", ".join(str(item) for item in value[:5])


def _self_check_resolutions_by_interaction_id(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    resolutions = value.get("resolutions")
    if not isinstance(resolutions, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in resolutions:
        if not isinstance(item, dict):
            continue
        interaction_id = str(item.get("interaction_id") or "")
        if interaction_id:
            result[interaction_id] = item
    return result


def _scan_supplement_followup_response(
    followup: dict[str, Any],
    interaction_decisions: Any | None,
) -> tuple[str, list[str]]:
    scan = _scan_confirmation_payload(interaction_decisions)
    if not scan or scan.get("review_status") != "pending_harness_maintainer_review":
        return "unaddressed", []
    snippets = _matching_scan_supplement_snippets(followup, scan)
    if not snippets:
        return "unaddressed", []
    return "partially_addressed_by_current_scan_supplement", snippets[:4]


def _scan_supplement_followup_note(response_sources: list[str]) -> str:
    if not response_sources:
        return ""
    return (
        "本轮 scan 补充可能已部分回应该追问："
        f"{'；'.join(response_sources)}；"
        "review_status=pending_harness_maintainer_review，仍需 Harness Maintainer 复核是否完全解决。"
    )


def _scan_confirmation_payload(interaction_decisions: Any | None) -> dict[str, Any]:
    if interaction_decisions is None:
        return {}
    if isinstance(interaction_decisions, dict):
        value = interaction_decisions.get("scan_confirmation", {})
        return value if isinstance(value, dict) else {}
    scan = getattr(interaction_decisions, "scan_confirmation", None)
    if scan is None:
        return {}
    if hasattr(scan, "model_dump"):
        return scan.model_dump(mode="json")
    return scan if isinstance(scan, dict) else {}


def _matching_scan_supplement_snippets(followup: dict[str, Any], scan: dict[str, Any]) -> list[str]:
    trigger = str(followup.get("trigger") or "")
    affects = {str(item).lower() for item in followup.get("affects", []) if isinstance(item, str)}
    snippets: list[str] = []

    primary_stack = str(scan.get("primary_stack_override") or "").strip()
    if primary_stack and trigger in {"unknown_stack", "stack_claim_without_evidence"}:
        snippets.append(f"stack={primary_stack}")

    modules = _dict_items(scan.get("modules"))
    if modules and (trigger in {"coverage_gap", "module_boundary_unclear"} or "guides" in affects):
        snippets.extend(f"module={item.get('path', '')}" for item in modules[:2] if item.get("path"))

    commands = _dict_items(scan.get("commands"))
    matching_commands = [
        item
        for item in commands
        if trigger == "test_evidence_missing" or "sensors" in affects
    ]
    snippets.extend(
        f"command={item.get('id', '')}:{item.get('command', '')}"
        for item in matching_commands[:2]
        if item.get("id") and item.get("command")
    )

    risk_areas = _dict_items(scan.get("risk_areas"))
    if risk_areas and (trigger in {"coverage_gap", "module_boundary_unclear"} or "workflow" in affects):
        snippets.extend(f"risk={item.get('path', '')}" for item in risk_areas[:2] if item.get("path"))

    return list(dict.fromkeys(snippets))


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _warning_codes_represented_by_followup(trigger: str) -> set[str]:
    return {
        "coverage_gap": {"source_sampling_truncated"},
        "test_evidence_missing": {"test_evidence_not_found"},
        "stack_claim_without_evidence": {"llm_stack_claim_without_evidence"},
    }.get(trigger, set())


def human_input_markdown(context_inputs: dict[str, Any], questionnaire: dict[str, Any], decision_markdown: str = "") -> str:
    context_lines = [
        f"- `{item['path']}`：{item['summary']}"
        for item in context_inputs.get("contexts", [])
    ] or ["- 暂未提供外部团队上下文。"]
    question_lines = [
        f"- `{item['interaction_id']}`：{item['question']}（confidence={item['confidence']}）"
        for item in questionnaire.get("questions", [])
    ]
    scan_confirmation_lines = _scan_confirmation_lines(questionnaire.get("questions", []))
    action_guidance_lines = _action_guidance_lines(questionnaire.get("questions", []))
    return (
        "# Human Input Needed\n\n"
        "## 已提供上下文\n\n"
        + "\n".join(context_lines)
        + "\n\n## 扫描待确认摘要\n\n"
        + "\n".join(scan_confirmation_lines)
        + "\n\n## 待确认问题\n\n"
        + "\n".join(question_lines)
        + "\n\n## 处理方式\n\n"
        + "\n".join(action_guidance_lines)
        + ("\n\n" + decision_markdown if decision_markdown else "")
        + "\n\n## 下一步建议\n\n"
        "- 如需补充团队规范，请使用 `init --context <file>` 重新生成 Harness。\n"
        "- 候选 Guides / Sensors 在维护者确认前保持 candidate 状态。\n"
    )


def _scan_confirmation_lines(questions: list[dict[str, Any]]) -> list[str]:
    scan_questions = [item for item in questions if item.get("interaction_type") in SCAN_CONFIRMATION_TYPES]
    if not scan_questions:
        return ["- 当前没有额外扫描待确认项；仍建议复核高影响判断。"]
    return [_scan_confirmation_line(item) for item in scan_questions]


def _scan_confirmation_line(item: dict[str, Any]) -> str:
    response_status = str(item.get("response_status") or "unaddressed")
    status_note = f"；response_status={response_status}" if item.get("interaction_type") == "scan_followup_confirmation" else ""
    sources = item.get("response_sources") if isinstance(item.get("response_sources"), list) else []
    source_note = f"；response_sources={_format_plain_items(sources)}" if sources else ""
    return (
        f"- `{item['interaction_id']}`：{item['question']}"
        f"（confidence={item['confidence']}；reason={item['reason']}{status_note}{source_note}）"
    )


def _action_guidance_lines(questions: list[dict[str, Any]]) -> list[str]:
    if not questions:
        return [
            "- 当前没有待确认问题；仍建议运行 `harness-builder-agent benchmark --repo <repo>` 验收生成资产。",
            "- Harness Builder 不执行 Runtime，也不创建 `.ai/task-runs`。",
        ]
    lines = [_action_guidance_line(item) for item in questions]
    lines.extend(
        [
            "- 需要重新进入向导时运行 `harness-builder-agent init --repo <repo>`；处理扫描修正时可在 guided summary 使用 `back` 返回 scan 步骤。",
            "- 处理完成后运行 `harness-builder-agent benchmark --repo <repo>` 生成 `.ai/benchmark-report.yaml`，再回到 guided `init` 查看 Maintenance triage。",
            "- Harness Builder 不执行 Runtime，也不创建 `.ai/task-runs`；任务级 workflow 过程数据由宿主 AI Coding Runtime 生成。",
        ]
    )
    return lines


def _action_guidance_line(question: dict[str, Any]) -> str:
    interaction_id = str(question.get("interaction_id", "confirm:unknown"))
    interaction_type = str(question.get("interaction_type", "unknown"))
    if interaction_type == "scan_warning_confirmation":
        return f"- `{interaction_id}`：{scan_warning_action_hint(scan_warning_code_from_interaction_id(interaction_id))}"
    if interaction_type == "scan_followup_confirmation":
        return f"- `{interaction_id}`：{_scan_followup_action_guidance(interaction_id, question)}"
    guidance_by_type = {
        "context_confirmation": "用 `harness-builder-agent init --repo <repo> --context <file>` 补充团队规范、架构约束或测试策略。",
        "candidate_asset_confirmation": "用 `review-candidate --candidate-id <id> --decision accepted|deferred|rejected|applied` 治理 review-only Guide / Sensor 候选。",
        "sensor_gate_confirmation": "先在目标仓库和 CI 中确认命令稳定性，再调整 Sensor / gate 语义并运行 benchmark 验收。",
        "risk_area_confirmation": "在 guided scan correction 中补充 `risk=路径|原因`，让风险区进入 Guide、Sensor 和 workflow routing 叙事。",
        "evidence_expansion_confirmation": "查看 `.ai/scan-metadata.yaml` 的 evidence expansion，必要时用 `--context <file>` 或 scan correction 补充关键路径。",
    }
    guidance = guidance_by_type.get(
        interaction_type,
        "在 `.ai/questionnaire.yaml` 中保留该问题，待 Harness Maintainer 人工确认后再更新对应 Harness 资产。",
    )
    return f"- `{interaction_id}`：{guidance}"


def _scan_followup_action_guidance(interaction_id: str, question: dict[str, Any]) -> str:
    response_status = str(question.get("response_status") or "unaddressed")
    if response_status == "reviewed_resolved_by_harness_maintainer":
        return (
            "已由 Harness Maintainer 标记为 resolved；该状态只表示人工复核完成，不表示 Builder 自动重扫或验证了事实。"
            f" 如需重新打开，运行 `harness-builder-agent review-human-input --interaction-id {interaction_id} --decision reopened --rationale \"<reason>\"`。"
        )
    supplement = "；当前 scan supplement 已部分回应，建议先人工复核是否足够关闭" if response_status == "partially_addressed_by_current_scan_supplement" else ""
    guidance = scan_followup_answer_guidance_text(question)
    return (
        f"建议补充：{guidance} "
        "重新进入 guided `init` 按该建议补充；这些补充不会自动关闭追问，也不会被伪装成已验证扫描 evidence"
        f"{supplement}。复核完成后运行 `harness-builder-agent review-human-input --interaction-id {interaction_id} --decision resolved --rationale \"<reason>\"` 标记。"
    )


def scan_warning_code_from_interaction_id(interaction_id: str) -> str:
    prefix = "confirm:scan-warning:"
    if interaction_id.startswith(prefix):
        return interaction_id[len(prefix):] or "unknown"
    return "unknown"


def scan_warning_action_hint(code: str) -> str:
    hints = {
        "test_evidence_not_found": "补充测试命令：`command=ID|命令|test|hard|来源|置信度`，或用 `--context <file>` 补充测试策略。",
        "command_without_evidence": "补充带真实 source 的验证命令，例如 `command=ID|命令|test|hard|docs/testing.md|high`。",
        "command_low_confidence_hard_gate": "低置信度命令已降级为 soft gate；如要作为 hard gate，请补充 medium/high 置信度和真实 source。",
        "llm_stack_claim_without_evidence": "补充 `stack=<value>` 或通过 `--context <file>` 说明技术栈判断依据。",
        "source_sampling_truncated": "查看 `.ai/scan-report.md` / `.ai/scan-metadata.yaml`，必要时补充 `module=路径|类型|名称` 或 `risk=路径|原因`。",
        "llm_evidence_plan_low_confidence": "复核 `.ai/scan-metadata.yaml` 中的 evidence expansion，并补充关键模块、风险路径或团队上下文。",
    }
    return hints.get(code, "查看 warning reason 和 evidence，用 scan correction 或 `--context <file>` 补充事实。")
