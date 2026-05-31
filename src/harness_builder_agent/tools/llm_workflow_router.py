from __future__ import annotations

import json
import re
from collections.abc import Callable

from pydantic import ValidationError

from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig
from harness_builder_agent.prompts.loader import load_prompt_sections

WORKFLOW_ROUTER_PROMPT_VERSION = "llm-workflow-router-v1"
WORKFLOW_ROUTER_PROMPT_RESOURCE = "llm_workflow_router_v1.md"


def recommend_workflow_with_llm(
    *,
    task_id: str,
    task_brief: str,
    config: HarnessConfig,
    evidence_pack: MaturityEvidencePack,
    caller: Callable[[list[dict[str, str]]], str] | None = None,
    llm_config: DeepSeekConfig | None = None,
) -> WorkflowRecommendationReport:
    messages = build_workflow_recommendation_messages(
        task_id=task_id,
        task_brief=task_brief,
        config=config,
        evidence_pack=evidence_pack,
    )
    content = caller(messages) if caller else call_deepseek(messages, config=llm_config)
    if not content.strip():
        raise ValueError("DeepSeek workflow recommendation response is empty")
    return parse_workflow_recommendation_response(
        content,
        configured_workflows=set(config.workflows),
        routing_rule_ids={rule.id for rule in config.workflow_routing.rules},
    )


def build_workflow_recommendation_messages(
    *,
    task_id: str,
    task_brief: str,
    config: HarnessConfig,
    evidence_pack: MaturityEvidencePack,
) -> list[dict[str, str]]:
    system_prompt, user_prompt = load_prompt_sections(WORKFLOW_ROUTER_PROMPT_RESOURCE)
    payload = {
        "prompt_version": WORKFLOW_ROUTER_PROMPT_VERSION,
        "task_id": task_id,
        "task_brief": task_brief,
        "harness_config": config.model_dump(mode="json"),
        "maturity_evidence": evidence_pack.model_dump(mode="json"),
    }
    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": f"{user_prompt}\n\nWorkflow routing input JSON:\n{json.dumps(payload, ensure_ascii=False)}",
        },
    ]


def parse_workflow_recommendation_response(
    content: str,
    *,
    configured_workflows: set[str],
    routing_rule_ids: set[str],
) -> WorkflowRecommendationReport:
    raw = _extract_json_text(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek workflow recommendation response must be valid JSON") from exc
    try:
        report = WorkflowRecommendationReport.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"DeepSeek workflow recommendation response failed schema validation: {exc}") from exc

    if report.recommended_workflow not in configured_workflows:
        raise ValueError(f"DeepSeek workflow recommendation referenced unknown recommended_workflow: {report.recommended_workflow}")
    unknown_rules = sorted(set(report.matched_rule_ids) - routing_rule_ids)
    if unknown_rules:
        raise ValueError(f"DeepSeek workflow recommendation referenced unknown matched_rule_ids: {', '.join(unknown_rules)}")
    bad_evidence_sources = [source for source in report.evidence_sources if not source.startswith(".ai/")]
    if bad_evidence_sources:
        raise ValueError(
            "DeepSeek workflow recommendation evidence_sources must be under .ai/: "
            + ", ".join(sorted(bad_evidence_sources))
        )
    return report


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped
