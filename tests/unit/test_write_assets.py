from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.interaction_decisions import accepted_interactive_decisions
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates
from harness_builder_agent.tools.write_assets import write_initial_assets


def _inventory(repo: Path) -> ProjectInventory:
    return ProjectInventory(
        repo_name=repo.name,
        root_path=str(repo),
        primary_stack="java-spring",
        stacks=["java", "maven", "spring-boot"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
        evidence=[{"path": "pom.xml", "reason": "maven build file"}],
        documents=[{"path": "README.md", "kind": "project documentation"}],
        configs=[{"path": "src/main/resources/application.yml", "kind": "spring configuration"}],
        ci_files=[{"path": ".github/workflows/ci.yml", "kind": "github actions"}],
        stack_extensions={
            "scan_metadata": {
                "schema_version": "1.0",
                "llm_status": "succeeded",
                "prompt_version": "test",
                "evidence_file_count": 1,
                "evidence_expansion": {
                    "schema_version": "1.0",
                    "planner_prompt_version": "llm-evidence-planner-v1",
                    "requested_paths": ["src/main/java/com/example/demo/DemoController.java"],
                    "risk_focus": ["controller routing"],
                    "rationale": "Controller route ownership needed deeper inspection.",
                    "confidence": "medium",
                    "read_paths": ["src/main/java/com/example/demo/DemoController.java"],
                    "read_file_count": 1,
                },
                "warnings": [],
            },
            "llm_scan_proposal": {
                "schema_version": "1.0",
                "primary_stack": "java-spring",
                "stacks": ["java", "maven"],
                "modules": [{"name": "app", "path": ".", "kind": "backend"}],
                "architecture_signals": ["Controller layer is present"],
                "risk_areas": [
                    {"path": "src/main/resources/application.yml", "reason": "database config risk"},
                    {"path": "docs/a.json", "reason": "可能包含明文 API key"},
                ],
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
            "risk_areas": [
                {"path": "src/main/resources/application.yml", "reason": "database config risk"},
                {"path": "docs/a.json", "reason": "可能包含明文 API key"},
            ],
        },
    )


def _commands() -> CommandCatalog:
    return CommandCatalog(commands=[CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml")])


def test_llm_enhancement_candidates_returns_schema_report(tmp_path: Path):
    report = build_llm_enhancement_candidates(_inventory(tmp_path), _commands())

    assert isinstance(report, WeaponLibraryCandidateReport)
    assert report.schema_version == "1.0"
    assert report.candidates
    assert all(candidate.status == "candidate" for candidate in report.candidates)


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
    assert "## 风险区域" in guide
    assert "## 验证入口" in guide
    assert "## 成熟度缺口关联" in guide
    assert "## 来源证据" in guide
    assert "## LLM 证据扩展" in guide
    assert "java-spring.guide." in guide
    assert "README.md" in guide
    assert ".github/workflows/ci.yml" in guide
    assert "src/main/java/com/example/demo/DemoController.java" in guide
    assert "controller routing" in guide
    assert "confidence=`medium`" in guide
    assert "read_file_count=1" in guide
    assert "Controller route ownership needed deeper inspection." in guide
    assert "src/main/resources/application.yml" in guide
    assert "mvn test" in guide

    sensor = (ai / "sensors" / "verification.md").read_text(encoding="utf-8")
    assert "## 已发现的验证命令" in sensor
    assert "## 风险与验证映射" in sensor
    assert "## 成熟度缺口关联" in sensor
    assert "## 失败处理策略" in sensor
    assert "common.sensor." in sensor
    assert "src/main/resources/application.yml" in sensor
    assert "mvn test" in sensor

    init_summary = (ai / "init-summary.md").read_text(encoding="utf-8")
    assert "## 本仓库关键事实" in init_summary
    assert "## 本次吸收的用户补充" in init_summary
    assert "## 资产如何补齐缺口" in init_summary
    assert "src/main/resources/application.yml" in init_summary
    assert "mvn test" in init_summary

    human_input = (ai / "human-input-needed.md").read_text(encoding="utf-8")
    assert "团队规则" in human_input
    assert "confirm:high-risk:docs-a-json" in human_input
    assert "高风险" in human_input
    assert "docs/a.json" in human_input

    config = yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8"))
    standard = next(rule for rule in config["workflow_routing"]["rules"] if rule["id"] == "standard-escalation")
    assert "risk_area:src/main/resources/application.yml" in standard["triggers"]
    assert "risk_area:docs/a.json" in standard["triggers"]
    assert "Scanned risk area `docs/a.json` requires standard workflow review" in standard["rationale"]

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


def test_write_initial_assets_persists_interaction_decisions_and_applies_candidate_status(tmp_path: Path):
    context = tmp_path / "team-rules.md"
    context.write_text("团队规则：Controller 只能调用 Service。", encoding="utf-8")
    trace = GenerationTrace.start(tmp_path, "init")
    decisions = accepted_interactive_decisions(
        str(tmp_path),
        context_paths=[str(context)],
        inline_contexts=["所有新增逻辑必须有测试"],
        candidate_ids=["llm-guide-architecture-001"],
        accept_candidates=True,
    )

    ai = write_initial_assets(
        tmp_path,
        _inventory(tmp_path),
        _commands(),
        trace=trace,
        context_paths=[context],
        interaction_decisions=decisions,
    )

    decision_payload = yaml.safe_load((ai / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decision_payload["mode"] == "interactive"
    assert decision_payload["final_confirmation"]["status"] == "confirmed"
    human_input = (ai / "human-input-needed.md").read_text(encoding="utf-8")
    assert "Interaction Decisions" in human_input
    assert "所有新增逻辑必须有测试" in human_input
    project_context = (ai / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "## 团队上下文" in project_context
    assert "Controller 只能调用 Service" in project_context
    assert "所有新增逻辑必须有测试" in project_context
    init_summary = (ai / "init-summary.md").read_text(encoding="utf-8")
    assert "所有新增逻辑必须有测试" in init_summary
    candidates = yaml.safe_load((ai / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in candidates["candidates"]}
    assert by_id["llm-guide-architecture-001"]["status"] == "confirmed"
    assert by_id["llm-guide-architecture-001"]["human_confirmation_required"] is False
