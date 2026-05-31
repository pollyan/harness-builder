from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire, QuestionnaireQuestion
from harness_builder_agent.schemas.human_input_governance import (
    HumanInputDecision,
    HumanInputGovernanceDecision,
    HumanInputGovernanceLog,
)
from harness_builder_agent.schemas.interaction_decision import InteractionDecisions
from harness_builder_agent.tools.asset_writers.shared import write_text, write_yaml
from harness_builder_agent.tools.human_confirmation import human_input_markdown
from harness_builder_agent.tools.interaction_decisions import default_non_interactive_decisions, interaction_decisions_markdown


def review_human_input(
    repo: Path,
    interaction_id: str,
    decision: HumanInputDecision | str,
    rationale: str,
    reviewer: str = "harness-maintainer",
) -> Path:
    if decision not in {"resolved", "reopened"}:
        raise ValueError(f"Unsupported human input governance decision: {decision}")
    if not rationale.strip():
        raise ValueError("rationale is required for human input governance decisions")

    root = repo.resolve()
    ai = root / ".ai"
    questionnaire_path = ai / "questionnaire.yaml"
    if not questionnaire_path.exists():
        raise FileNotFoundError("missing .ai/questionnaire.yaml")

    questionnaire = Questionnaire.model_validate(yaml.safe_load(questionnaire_path.read_text(encoding="utf-8")) or {})
    question_index, question = _find_question(questionnaire, interaction_id)
    if question.interaction_type != "scan_followup_confirmation":
        raise ValueError("review-human-input only supports scan_followup_confirmation interactions")

    previous_status = question.response_status
    new_status = _new_response_status(question, decision)
    updated_questions = list(questionnaire.questions)
    updated_questions[question_index] = question.model_copy(update={"response_status": new_status})
    updated_questionnaire = questionnaire.model_copy(update={"questions": updated_questions})

    write_yaml(questionnaire_path, updated_questionnaire.model_dump(mode="json"))
    log = _load_log(ai / "review" / "human-input-governance.yaml")
    log.decisions.append(
        HumanInputGovernanceDecision(
            interaction_id=question.interaction_id,
            interaction_type="scan_followup_confirmation",
            decision=decision,
            previous_response_status=previous_status,
            new_response_status=new_status,
            rationale=rationale.strip(),
            reviewer=reviewer,
            decided_at=_utc_now(),
            response_sources=question.response_sources,
        )
    )
    _write_governance(ai, log)
    _refresh_human_input_markdown(ai, updated_questionnaire)
    return ai


def _find_question(questionnaire: Questionnaire, interaction_id: str) -> tuple[int, QuestionnaireQuestion]:
    for index, question in enumerate(questionnaire.questions):
        if question.interaction_id == interaction_id:
            return index, question
    raise ValueError(f"unknown human input interaction id: {interaction_id}")


def _new_response_status(question: QuestionnaireQuestion, decision: str) -> str:
    if decision == "resolved":
        return "reviewed_resolved_by_harness_maintainer"
    if question.response_sources:
        return "partially_addressed_by_current_scan_supplement"
    return "unaddressed"


def _refresh_human_input_markdown(ai: Path, questionnaire: Questionnaire) -> None:
    context_inputs = _load_context_inputs(ai)
    decisions = _load_interaction_decisions(ai)
    write_text(
        ai / "human-input-needed.md",
        human_input_markdown(
            context_inputs.model_dump(mode="json"),
            questionnaire.model_dump(mode="json"),
            interaction_decisions_markdown(decisions),
        ),
    )


def _load_context_inputs(ai: Path) -> ContextInputs:
    path = ai / "context-inputs.yaml"
    if not path.exists():
        return ContextInputs()
    return ContextInputs.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _load_interaction_decisions(ai: Path) -> InteractionDecisions:
    path = ai / "interaction-decisions.yaml"
    if not path.exists():
        return default_non_interactive_decisions(str(ai.parent))
    return InteractionDecisions.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _load_log(path: Path) -> HumanInputGovernanceLog:
    if not path.exists():
        return HumanInputGovernanceLog()
    return HumanInputGovernanceLog.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _write_governance(ai: Path, log: HumanInputGovernanceLog) -> None:
    write_yaml(ai / "review" / "human-input-governance.yaml", log.model_dump(mode="json"))
    write_text(ai / "review" / "human-input-governance.md", _governance_markdown(log))


def _governance_markdown(log: HumanInputGovernanceLog) -> str:
    decisions = "\n\n".join(_decision_markdown(item) for item in log.decisions) or "No decisions recorded."
    return (
        "# Human Input Governance\n\n"
        "## Decisions\n\n"
        f"{decisions}\n\n"
        "## Review Boundary\n\n"
        "- `resolved` 表示 Harness Maintainer 已人工复核该 scan follow-up；不表示 Builder 重新扫描或自动验证了事实。\n"
        "- 该治理动作只更新 `questionnaire.yaml`、`human-input-needed.md` 和本 review log，不修改正式 Harness 资产。\n"
        "- 如需改变 Guides、Sensors、Workflow routing 或扫描事实，应重新运行 guided `init`、治理候选或人工编辑后运行 benchmark。\n"
    )


def _decision_markdown(decision: HumanInputGovernanceDecision) -> str:
    sources = "\n".join(f"- `{item}`" for item in decision.response_sources) or "- None."
    return (
        f"### {decision.interaction_id}\n\n"
        f"- interaction type: `{decision.interaction_type}`\n"
        f"- decision: `{decision.decision}`\n"
        f"- previous response status: `{decision.previous_response_status}`\n"
        f"- new response status: `{decision.new_response_status}`\n"
        f"- reviewer: `{decision.reviewer}`\n"
        f"- decided at: `{decision.decided_at}`\n\n"
        "#### Rationale\n\n"
        f"{decision.rationale}\n\n"
        "#### Response Sources\n\n"
        f"{sources}"
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
