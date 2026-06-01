from __future__ import annotations

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates


def test_build_llm_enhancement_candidates_from_scan_proposal():
    inventory = ProjectInventory(
        repo_name="demo",
        root_path="/tmp/demo",
        primary_stack="java-spring",
        stack_extensions={
            "llm_scan_proposal": {
                "architecture_signals": ["Controller layer is present"],
                "risk_areas": [{"path": "src/main/resources/application.yml", "reason": "Database config risk"}],
                "command_candidates": [
                    {
                        "id": "unit_test",
                        "command": "mvn test",
                        "type": "test",
                        "gate": "hard",
                        "source": "pom.xml",
                        "confidence": "high",
                    }
                ],
            }
        },
    )
    commands = CommandCatalog(commands=[CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml")])

    report = build_llm_enhancement_candidates(inventory, commands)

    assert isinstance(report, WeaponLibraryCandidateReport)
    assert report.schema_version == "1.0"
    assert report.source == "llm_scan_proposal"
    assert {item.candidate_type for item in report.candidates} == {"guide", "sensor"}
    assert all(item.status == "candidate" for item in report.candidates)
    assert all(item.human_confirmation_required is True for item in report.candidates)
    by_id = {item.id: item for item in report.candidates}
    assert by_id["llm-guide-architecture-001"].maturity_dimensions == ["guides"]
    assert by_id["llm-guide-architecture-001"].maturity_impact_summary == "补齐 Guides 上下文。"
    assert by_id["llm-guide-risk-001"].maturity_dimensions == ["guides", "risk_control"]
    assert by_id["llm-guide-risk-001"].maturity_impact_summary == "补齐 Guides 上下文、Risk Control 风险控制。"
    assert by_id["llm-sensor-command-001"].maturity_dimensions == ["sensors", "verification_sophistication"]
    assert by_id["llm-sensor-command-001"].maturity_impact_summary == "补齐 Sensors 验证、Verification 验证成熟度。"
    assert all(item.review_boundary == "review_only_no_formal_asset_change" for item in report.candidates)


def test_build_llm_enhancement_candidates_records_no_enhancement_audit_boundary():
    inventory = ProjectInventory(repo_name="demo", root_path="/tmp/demo", primary_stack="unknown")
    commands = CommandCatalog(commands=[])

    report = build_llm_enhancement_candidates(inventory, commands)

    candidate = report.candidates[0]
    assert candidate.id == "llm-guide-no-enhancement-001"
    assert candidate.maturity_dimensions == []
    assert candidate.maturity_impact_summary == (
        "未发现明确增强项；保留候选审计边界，提醒 Maintainer 复核 LLM scan 是否遗漏 Guide / Sensor 线索。"
    )
    assert candidate.next_stage_contribution == "保持 review-only 审计入口，不声明成熟度提升。"
    assert candidate.review_boundary == "review_only_no_formal_asset_change"
