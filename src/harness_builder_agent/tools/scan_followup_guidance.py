from __future__ import annotations


def scan_followup_answer_guidance_lines(questions: list[dict[str, object]], limit: int = 5) -> list[str]:
    if not questions:
        return []

    shown = questions[:limit]
    lines = [scan_followup_answer_guidance_line(question) for question in shown]
    remaining = len(questions) - len(shown)
    if remaining > 0:
        lines.append(f"还有 {remaining} 个深度追问可按同样方式补充；完整问题会进入 `.ai/questionnaire.yaml`。")
    lines.append(
        "边界：这些补充只会进入本轮 scan supplement 并可能部分回应追问，"
        "不会自动关闭追问；复核完成仍需使用 `review-human-input` 标记。"
    )
    return lines


def scan_followup_answer_guidance_line(question: dict[str, object]) -> str:
    interaction_id = str(question.get("interaction_id") or "confirm:scan-followup:unknown")
    return f"`{interaction_id}`：{scan_followup_answer_guidance_text(question)}"


def scan_followup_answer_guidance_text(question: dict[str, object]) -> str:
    trigger = _followup_trigger(question)
    if trigger == "coverage_gap":
        return (
            "可补充关键目录或风险路径，例如 `module=src/main/java|backend|核心模块`，"
            "或 `risk=src/main/java/payments|支付或权限高风险`；也可以自然语言说明入口文件。"
        )
    if trigger in {"stack_claim_without_evidence", "unknown_stack"}:
        return (
            "可补充真实技术栈，例如 `stack=java-spring`；如果只是子模块，"
            "请用自然语言说明它的边界和是否影响 Workflow。"
        )
    if trigger == "module_boundary_unclear":
        return (
            "可补充模块边界，例如 `module=src/main/java|backend|核心模块`；"
            "如果该模块高风险，也可以补充 `risk=src/main/java/payments|支付或权限高风险`。"
        )
    if trigger == "test_evidence_missing":
        return (
            "可补充真实验证入口，例如 `command=unit_test|mvn test|test|hard|pom.xml|high`；"
            "如果当前只能人工运行，请自然语言说明 soft gate 边界。"
        )
    return (
        "可用自然语言说明真实工程边界，也可以按需补充 `stack=...`、"
        "`module=路径|类型|名称`、`command=ID|命令|类型|gate|来源|置信度` 或 `risk=路径|原因`。"
    )


def _followup_trigger(question: dict[str, object]) -> str:
    trigger = str(question.get("trigger") or "").strip()
    if trigger:
        return trigger

    interaction_id = str(question.get("interaction_id") or "")
    if "coverage" in interaction_id:
        return "coverage_gap"
    if "test-evidence" in interaction_id:
        return "test_evidence_missing"
    if "unknown-stack" in interaction_id:
        return "unknown_stack"
    if "stack-" in interaction_id:
        return "stack_claim_without_evidence"
    if "module-boundary" in interaction_id:
        return "module_boundary_unclear"
    return ""
