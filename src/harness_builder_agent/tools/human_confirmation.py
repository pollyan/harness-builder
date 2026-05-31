from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire

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


def build_questionnaire(context_inputs: dict[str, Any], scan_metadata: dict[str, Any]) -> dict[str, Any]:
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
    for warning in scan_metadata.get("warnings", []):
        code = warning.get("code", "unknown")
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
