from __future__ import annotations


def build_llm_hint_placeholder(manual_points: list[str]) -> dict:
    return {
        "enabled": False,
        "policy": "LLM 只能生成 hints 和人工校准建议，不得覆盖确定性事实源。",
        "hints": [
            {
                "type": "manual-calibration",
                "message": point,
                "confidence": "low",
                "evidence": [],
            }
            for point in manual_points
        ],
    }
