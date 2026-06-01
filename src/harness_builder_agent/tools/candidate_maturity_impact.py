from __future__ import annotations

from typing import Any, Literal


MaturityDimension = Literal["guides", "risk_control", "sensors", "verification_sophistication"]

REVIEW_ONLY_BOUNDARY = "review_only_no_formal_asset_change"


def candidate_maturity_impact_fields(item: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(item.get("id", ""))
    title = str(item.get("title", ""))
    rationale = str(item.get("rationale", ""))
    evidence = [str(value) for value in item.get("evidence", [])]
    haystack = " ".join([candidate_id, title, rationale, *evidence]).lower()

    if "no-enhancement" in candidate_id:
        return {
            "maturity_dimensions": [],
            "maturity_impact_summary": "未发现明确增强项；保留候选审计边界，提醒 Maintainer 复核 LLM scan 是否遗漏 Guide / Sensor 线索。",
            "next_stage_contribution": "保持 review-only 审计入口，不声明成熟度提升。",
            "review_boundary": REVIEW_ONLY_BOUNDARY,
        }

    if item.get("candidate_type") == "sensor":
        dimensions: list[MaturityDimension] = ["sensors", "verification_sophistication"]
        contribution = "把待确认验证命令或验证活动留在人工审查队列，避免直接提升 hard gate。"
    else:
        dimensions = ["guides"]
        if any(token in haystack for token in ("risk", "风险", "auth", "鉴权", "权限", "payment", "支付", "security", "安全")):
            dimensions.append("risk_control")
            contribution = "把风险区域或约束候选留给 Maintainer 审查，后续可连接 Guide、Sensor 和 Workflow 升级。"
        else:
            contribution = "把 LLM 发现的上下文候选留给 Maintainer 审查，后续可补齐项目 Guide 基线。"

    return {
        "maturity_dimensions": dimensions,
        "maturity_impact_summary": f"补齐 {maturity_dimension_labels(dimensions)}。",
        "next_stage_contribution": contribution,
        "review_boundary": REVIEW_ONLY_BOUNDARY,
    }


def candidate_maturity_impact_lines(item: dict[str, Any]) -> list[str]:
    fields = candidate_maturity_impact_fields(item)
    return [
        f"成熟度影响：{fields['maturity_impact_summary']}",
        f"下一阶段贡献：{fields['next_stage_contribution']}",
        "审查边界：保持 review-only；接受只记录确认，不会自动写入正式 Guide 或 Sensor。",
    ]


def maturity_dimension_labels(dimensions: list[str]) -> str:
    labels = {
        "guides": "Guides 上下文",
        "risk_control": "Risk Control 风险控制",
        "sensors": "Sensors 验证",
        "verification_sophistication": "Verification 验证成熟度",
    }
    return "、".join(labels.get(item, item) for item in dimensions)
