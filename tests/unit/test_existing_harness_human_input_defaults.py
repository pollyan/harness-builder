from __future__ import annotations

from harness_builder_agent.tools.interactive_init import _review_human_input_default_interaction_id
from harness_builder_agent.tools.maintenance_triage import MaintenanceAction


def test_review_human_input_default_uses_pending_scan_followup_detail():
    actions = [
        MaintenanceAction(
            priority=10,
            action="benchmark",
            reason="benchmark_not_run",
            source=".ai/benchmark-report.yaml",
            next_action="benchmark",
        ),
        MaintenanceAction(
            priority=25,
            action="review-human-input",
            reason="human_input_scan_followups_pending",
            source=".ai/questionnaire.yaml",
            next_action="review-human-input",
            count=1,
            detail="confirm:scan-followup:test-evidence",
        ),
    ]

    assert _review_human_input_default_interaction_id(actions) == "confirm:scan-followup:test-evidence"


def test_review_human_input_default_is_absent_without_pending_scan_followup():
    actions = [
        MaintenanceAction(
            priority=20,
            action="review-candidate",
            reason="asset_candidates_pending",
            source=".ai/review/asset-candidates.yaml",
            next_action="review-candidate",
            count=1,
        )
    ]

    assert _review_human_input_default_interaction_id(actions) is None
