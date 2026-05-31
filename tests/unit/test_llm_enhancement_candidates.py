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
