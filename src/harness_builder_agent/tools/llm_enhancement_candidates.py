from __future__ import annotations

from typing import Any

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
from harness_builder_agent.tools.candidate_maturity_impact import candidate_maturity_impact_fields


def build_llm_enhancement_candidates(inventory: ProjectInventory, commands: CommandCatalog) -> WeaponLibraryCandidateReport:
    proposal = inventory.stack_extensions.get("llm_scan_proposal", {})
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, tuple[str, ...]]] = set()

    for index, signal in enumerate(proposal.get("architecture_signals", []) or [], start=1):
        _append_candidate(
            candidates,
            seen,
            {
                "id": f"llm-guide-architecture-{index:03d}",
                "candidate_type": "guide",
                "status": "candidate",
                "title": "架构信号候选规则",
                "rationale": str(signal),
                "evidence": [str(signal)],
                "source": "llm_scan_proposal",
                "human_confirmation_required": True,
            },
        )

    for index, risk in enumerate(proposal.get("risk_areas", []) or [], start=1):
        path = str(risk.get("path", "unknown"))
        reason = str(risk.get("reason", "LLM scan detected risk area."))
        _append_candidate(
            candidates,
            seen,
            {
                "id": f"llm-guide-risk-{index:03d}",
                "candidate_type": "guide",
                "status": "candidate",
                "title": f"风险区域候选规则：{path}",
                "rationale": reason,
                "evidence": [path],
                "source": "llm_scan_proposal",
                "human_confirmation_required": True,
            },
        )

    command_ids = {command.id for command in commands.commands}
    for index, command in enumerate(proposal.get("command_candidates", []) or [], start=1):
        command_id = str(command.get("id", f"command-{index}"))
        command_text = str(command.get("command", ""))
        existing = command_id in command_ids
        _append_candidate(
            candidates,
            seen,
            {
                "id": f"llm-sensor-command-{index:03d}",
                "candidate_type": "sensor",
                "status": "candidate",
                "title": f"验证命令候选：{command_id}",
                "rationale": (
                    "该命令已进入 CommandCatalog，建议人工确认是否保留或提升 gate。"
                    if existing
                    else "LLM scan 提出了新的验证命令候选，建议人工确认后再采用。"
                ),
                "evidence": [command_text, str(command.get("source", ""))],
                "source": "llm_scan_proposal",
                "human_confirmation_required": True,
            },
        )

    if not candidates:
        candidate = {
            "id": "llm-guide-no-enhancement-001",
            "candidate_type": "guide",
            "status": "candidate",
            "title": "未发现明确模型增强建议",
            "rationale": "LLM scan proposal 未提供 architecture_signals、risk_areas 或 command_candidates。",
            "evidence": [inventory.primary_stack],
            "source": "llm_scan_proposal",
            "human_confirmation_required": True,
        }
        candidate.update(candidate_maturity_impact_fields(candidate))
        candidates.append(candidate)

    return WeaponLibraryCandidateReport(candidates=candidates)


def candidate_guides_markdown(report: dict[str, Any]) -> str:
    guide_candidates = [item for item in report["candidates"] if item["candidate_type"] == "guide"]
    return _candidates_markdown("Candidate Guides", guide_candidates)


def candidate_sensors_markdown(report: dict[str, Any]) -> str:
    sensor_candidates = [item for item in report["candidates"] if item["candidate_type"] == "sensor"]
    return _candidates_markdown("Candidate Sensors", sensor_candidates)


def enhancement_summary_markdown(report: dict[str, Any]) -> str:
    return _candidates_markdown("LLM Enhancement Candidates", report["candidates"])


def _append_candidate(candidates: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]], candidate: dict[str, Any]) -> None:
    key = (candidate["candidate_type"], candidate["title"], tuple(candidate["evidence"]))
    if key in seen:
        return
    seen.add(key)
    candidate.update(candidate_maturity_impact_fields(candidate))
    candidates.append(candidate)


def _candidates_markdown(title: str, candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        body = "- 暂无候选项。"
    else:
        body = "\n".join(
            f"- `{item['id']}`：{item['title']}；status=`{item['status']}`；source=`{item['source']}`；"
            f"maturity=`{item.get('maturity_impact_summary', '')}`；"
            f"next=`{item.get('next_stage_contribution', '')}`；"
            f"boundary=`{item.get('review_boundary', 'review_only_no_formal_asset_change')}`；"
            f"{item['rationale']}"
            for item in candidates
        )
    return (
        f"# {title}\n\n"
        "这些候选项来自 LLM scan proposal，只能作为 candidate，需人工确认后才能进入正式 Harness。\n\n"
        f"{body}\n"
    )
