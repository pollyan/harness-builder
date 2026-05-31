from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire
from harness_builder_agent.tools.risk_signals import high_impact_risk_areas, risk_slug

SUMMARY_LIMIT = 1200


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
            action = resolution.get("suggested_next_action") or "请人工确认该追问。"
            rationale = resolution.get("rationale") or "LLM 二次自检未提供理由。"
            reason = f"{reason} LLM 二次自检：{status}；建议：{action}；理由：{rationale}"
        questions.append(
            {
                "interaction_type": "scan_followup_confirmation",
                "interaction_id": str(followup.get("interaction_id") or "confirm:scan-followup:unknown"),
                "question": str(followup.get("question") or "是否需要补充扫描不确定性？"),
                "options": ["补充或修正相关信息", "暂时接受当前不确定性"],
                "confidence": str(followup.get("confidence") or "low"),
                "reason": reason,
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
    return (
        "# Human Input Needed\n\n"
        "## 已提供上下文\n\n"
        + "\n".join(context_lines)
        + "\n\n## 待确认问题\n\n"
        + "\n".join(question_lines)
        + ("\n\n" + decision_markdown if decision_markdown else "")
        + "\n\n## 下一步建议\n\n"
        "- 如需补充团队规范，请使用 `init --context <file>` 重新生成 Harness。\n"
        "- 候选 Guides / Sensors 在维护者确认前保持 candidate 状态。\n"
    )
