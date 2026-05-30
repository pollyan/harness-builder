from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.write_assets import write_initial_assets


def _inventory(repo: Path) -> ProjectInventory:
    return ProjectInventory(
        repo_name=repo.name,
        root_path=str(repo),
        primary_stack="java-spring",
        stacks=["java", "maven", "spring-boot"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
        evidence=[{"path": "pom.xml", "reason": "maven build file"}],
        stack_extensions={
            "scan_metadata": {
                "schema_version": "1.0",
                "llm_status": "succeeded",
                "prompt_version": "test",
                "evidence_file_count": 1,
                "warnings": [],
            },
            "llm_scan_proposal": {
                "schema_version": "1.0",
                "primary_stack": "java-spring",
                "stacks": ["java", "maven"],
                "modules": [{"name": "app", "path": ".", "kind": "backend"}],
                "architecture_signals": ["Controller layer is present"],
                "risk_areas": [{"path": "src/main/resources/application.yml", "reason": "database config risk"}],
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
                "configs": [],
                "ci_files": [],
                "confidence": "high",
                "needs_human_confirmation": False,
                "reasoning_summary": "Maven project.",
            },
        },
    )


def _commands() -> CommandCatalog:
    return CommandCatalog(commands=[CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml")])


def test_write_initial_assets_generates_core_guides_sensors_skills_candidates_and_trace(tmp_path: Path):
    context = tmp_path / "team-rules.md"
    context.write_text("团队规则：Controller 只能调用 Service。", encoding="utf-8")
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    ai = write_initial_assets(tmp_path, _inventory(tmp_path), _commands(), trace=trace, context_paths=[context])
    trace.finish("completed", {"primary_stack": "java-spring"})

    assert (ai / "project-inventory.json").exists()
    assert (ai / "command-catalog.yaml").exists()
    assert (ai / "harness-config.yaml").exists()
    assert (ai / "scan-metadata.yaml").exists()
    assert (ai / "llm-scan-proposal.json").exists()
    assert (ai / "weapon-library-selection.yaml").exists()
    assert (ai / "guides" / "project-context.md").exists()
    assert (ai / "sensors" / "verification.md").exists()
    assert (ai / "skills" / "lightweight" / "SKILL.md").exists()
    assert (ai / "skills" / "bugfix" / "SKILL.md").exists()

    guide = (ai / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "## 当前项目事实" in guide
    assert "## 来源证据" in guide
    assert "java-spring.guide." in guide

    sensor = (ai / "sensors" / "verification.md").read_text(encoding="utf-8")
    assert "## 已发现的验证命令" in sensor
    assert "## 失败处理策略" in sensor
    assert "common.sensor." in sensor

    human_input = (ai / "human-input-needed.md").read_text(encoding="utf-8")
    assert "团队规则" in human_input

    candidates = yaml.safe_load((ai / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    assert candidates["source"] == "llm_scan_proposal"
    assert candidates["candidates"]
    assert all(item["status"] == "candidate" for item in candidates["candidates"])
    assert all(item["human_confirmation_required"] is True for item in candidates["candidates"])

    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/project-inventory.json" in artifact_paths
    assert ".ai/guides/project-context.md" in artifact_paths
    assert ".ai/sensors/verification.md" in artifact_paths
