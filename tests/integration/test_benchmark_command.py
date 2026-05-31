from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.benchmark import _content_checks, _quality_scores, _schema_checks, run_benchmark
from harness_builder_agent.tools.scan_repo import scan_repository

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _fake_scan(repo: Path, primary_stack: str):
    if primary_stack == "java-spring":
        response = {
            "primary_stack": "java-spring",
            "stacks": ["java", "maven", "spring-boot"],
            "modules": [{"name": "app", "path": ".", "kind": "backend"}],
            "architecture_signals": [],
            "risk_areas": [],
            "command_candidates": [
                {"id": "unit_test", "command": "mvn test", "type": "test", "gate": "hard", "source": "pom.xml", "confidence": "high"}
            ],
            "configs": [],
            "ci_files": [],
            "confidence": "high",
            "needs_human_confirmation": False,
            "reasoning_summary": "Java Spring project.",
        }
    else:
        response = {
            "primary_stack": "dotnet-aspnet",
            "stacks": ["dotnet", "aspnet-core"],
            "modules": [{"name": "MiniApi", "path": "src", "kind": "backend"}],
            "architecture_signals": [],
            "risk_areas": [],
            "command_candidates": [
                {
                    "id": "unit_test",
                    "command": "dotnet test",
                    "type": "test",
                    "gate": "hard",
                    "source": "mini-dotnet-webapi.sln",
                    "confidence": "high",
                }
            ],
            "configs": [],
            "ci_files": [],
            "confidence": "high",
            "needs_human_confirmation": False,
            "reasoning_summary": ".NET ASP.NET project.",
        }
    return scan_repository(repo, llm_caller=lambda _messages: json.dumps(response))


def _latest_trace(repo: Path) -> dict:
    runs = sorted((repo / ".ai" / "runs").iterdir())
    assert runs
    return yaml.safe_load((runs[-1] / "trace.yaml").read_text(encoding="utf-8"))


def _write_valid_workflow_recommendation(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    (review / "workflow-routing-recommendation.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "task_id": "task-1",
                "task_brief": "Fix a regression in login validation.",
                "recommended_workflow": "bugfix",
                "matched_rule_ids": ["bugfix-intent"],
                "risk_level": "medium",
                "confidence": "high",
                "rationale": "The task is a defect repair and should use the bugfix workflow.",
                "required_guides": [".ai/guides/project-context.md"],
                "required_sensors": [".ai/sensors/verification.md"],
                "human_confirmation_required": False,
                "review_status": "pending_harness_maintainer_review",
                "evidence_sources": [".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (review / "workflow-routing-recommendation.md").write_text(
        "# Workflow Routing Recommendation\n\n"
        "## Task\n\nFix a regression in login validation.\n\n"
        "## Recommended Workflow\n\nbugfix\n\n"
        "## Matched Routing Rules\n\n- bugfix-intent\n\n"
        "## Required Harness Assets\n\n- .ai/guides/project-context.md\n\n"
        "## Review Boundary\n\npending_harness_maintainer_review\n",
        encoding="utf-8",
    )


def _write_valid_asset_candidates(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    improvements = yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    source_id = improvements["candidates"][0]["id"]
    (review / "asset-candidates.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_maturity_review",
                "candidates": [
                    {
                        "id": "workflow-routing-policy-review",
                        "kind": "workflow_policy",
                        "source_candidate_id": source_id,
                        "source_review_decision": "support",
                        "suggested_path": ".ai/harness-config.yaml",
                        "title": "Review workflow routing policy",
                        "rationale": "Workflow recommendation evidence suggests a routing policy review.",
                        "draft_content": "workflow_routing:\n  rules:\n    - id: standard-escalation",
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                        "acceptance_checks": ["Benchmark content:workflow-routing-policy passes."],
                        "risk_level": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    for filename, title in {
        "asset-candidate-guides.md": "Asset Candidate Guides",
        "asset-candidate-sensors.md": "Asset Candidate Sensors",
        "asset-candidate-workflows.md": "Asset Candidate Workflows",
    }.items():
        (review / filename).write_text(
            f"# {title}\n\n"
            "## Review workflow routing policy\n\n"
            "### Rationale\n\nReview rationale.\n\n"
            "### Draft Content\n\nDraft only.\n\n"
            "### Evidence Sources\n\n- .ai/maturity-evidence.yaml\n\n"
            "### Acceptance Checks\n\n- Benchmark content:workflow-routing-policy passes.\n",
            encoding="utf-8",
        )


def _write_valid_maturity_review(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    improvements = yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    source_id = improvements["candidates"][0]["id"]
    (review / "maturity-review.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "summary": "Candidates are aligned with maturity evidence.",
                "reviewer_model": "deepseek-test",
                "candidate_reviews": [
                    {
                        "candidate_id": source_id,
                        "decision": "support",
                        "rationale": "Candidate is grounded in maturity evidence.",
                        "risks": [],
                        "suggested_acceptance_checks": ["Run benchmark."],
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                    }
                ],
                "missing_candidates": [],
                "global_risks": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (review / "maturity-review.md").write_text(
        "# Maturity Review\n\n"
        "## Summary\n\nCandidates are aligned.\n\n"
        "## Candidate Reviews\n\n- candidate: support\n\n"
        "## Missing Candidates\n\n- None.\n\n"
        "## Global Risks\n\n- None.\n",
        encoding="utf-8",
    )


def _write_valid_experience_summary(ai: Path) -> None:
    experience = ai / "experience"
    experience.mkdir(parents=True, exist_ok=True)
    (experience / "experience-summary.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_experience_summary",
                "review_status": "pending_harness_maintainer_review",
                "summary": "Sensor coverage is the main experience signal.",
                "findings": [
                    {
                        "id": "sensor-coverage-gap",
                        "kind": "sensor_feedback",
                        "title": "Sensor coverage gap",
                        "summary": "Pending improvements point to missing sensor coverage.",
                        "evidence_sources": [".ai/experience/pending-improvements.md"],
                        "confidence": "high",
                        "suggested_follow_up": "Draft a reviewed sensor candidate.",
                    }
                ],
                "warnings": ["Runtime task-runs are absent."],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (experience / "experience-summary.md").write_text(
        "# Experience Summary\n\n"
        "## Summary\n\nSensor coverage is the main experience signal.\n\n"
        "## Findings\n\n### Sensor coverage gap\n\n- evidence: `.ai/experience/pending-improvements.md`\n\n"
        "## Warnings\n\n- Runtime task-runs are absent.\n",
        encoding="utf-8",
    )


def _prepare_passed_benchmark_repo(tmp_path: Path, monkeypatch, fixture_name: str = "mini-spring-boot", profile: str = "java-spring") -> Path:
    repo = tmp_path / fixture_name
    shutil.copytree(FIXTURES / fixture_name, repo)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, profile))
    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", profile])
    assert result.exit_code == 0, result.output
    return repo


def test_benchmark_generates_report_for_java_fixture(tmp_path: Path, monkeypatch):
    repo = tmp_path / "mini-spring-boot"
    shutil.copytree(FIXTURES / "mini-spring-boot", repo)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    assert report["profile"] == "java-spring"
    assert report["status"] == "passed"
    assert report["quality_status"] in {"passed", "degraded"}
    assert "scan_quality" in report["quality_scores"]
    assert "guide_quality" in report["quality_scores"]
    assert "sensor_quality" in report["quality_scores"]
    assert "workflow_quality" in report["quality_scores"]
    assert report["quality_summary"]["total_score"] >= 0
    assert report["checks"]
    assert all(check["passed"] for check in report["checks"])
    check_ids = {check["id"] for check in report["checks"]}
    assert "exists:scan-metadata.yaml" in check_ids
    assert "exists:llm-scan-proposal.json" in check_ids
    assert "content:workflow-skills" in check_ids
    assert "content:workflow-skill-config-reference" in check_ids
    assert "content:workflow-routing-policy" in check_ids
    assert "content:maturity-routing-evidence" in check_ids
    assert "content:workflow-recommendation-review" in check_ids
    assert "content:maturity-review-artifact" in check_ids
    assert "content:asset-candidate-review" in check_ids
    assert "content:experience-summary-artifact" in check_ids
    assert "content:guides-quality" in check_ids
    assert "content:stack-specific-guides" in check_ids
    assert "content:sensors-quality" in check_ids
    assert "content:weapon-library-selection" in check_ids
    assert "content:hard-gate-command-evidence" in check_ids
    assert "content:harness-map-workflow-skill" not in check_ids
    assert "content:hard-gate-sensors-passed" not in check_ids
    assert "schema:harness-map" not in check_ids
    assert "schema:sensor-report" not in check_ids
    assert "schema:scan-metadata" in check_ids
    assert "schema:llm-scan-proposal" in check_ids
    assert "schema:weapon-library-selection" in check_ids
    assert "schema:benchmark-report" in check_ids
    assert "schema:maturity-score" in check_ids
    assert "schema:maturity-evidence" in check_ids
    assert "schema:improvement-candidates" in check_ids
    assert "schema:experience-index" in check_ids
    assert "exists:runs-trace" in check_ids
    assert "schema:generation-trace" in check_ids
    assert "content:generation-trace" in check_ids
    assert "schema:runtime-summary" not in check_ids
    assert "content:runtime-workflow-trace" not in check_ids
    assert "schema:questionnaire" in check_ids
    assert "content:human-confirmation" in check_ids
    assert "exists:review/llm-enhancement-candidates.md" in check_ids
    assert "schema:weapon-library-candidates" in check_ids
    assert "content:llm-enhancement-candidates" in check_ids
    assert not (repo / ".ai" / "task-runs").exists()
    trace = _latest_trace(repo)
    assert trace["command"] == "benchmark"
    assert trace["status"] == "completed"
    assert "benchmark" in trace["stages"]


def test_benchmark_generates_report_for_dotnet_fixture(tmp_path: Path, monkeypatch):
    repo = tmp_path / "mini-dotnet-webapi"
    shutil.copytree(FIXTURES / "mini-dotnet-webapi", repo)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, "dotnet-aspnet"))

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "dotnet-aspnet"])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    assert report["profile"] == "dotnet-aspnet"
    assert report["status"] == "passed"
    check_ids = {check["id"] for check in report["checks"]}
    assert "content:hard-gate-command-evidence" in check_ids
    assert "schema:benchmark-report" in check_ids


def test_benchmark_fails_when_hard_gate_command_lacks_evidence(tmp_path: Path, monkeypatch):
    repo = tmp_path / "mini-spring-boot"
    shutil.copytree(FIXTURES / "mini-spring-boot", repo)

    def fake_scan_without_source(repo_path: Path):
        inventory, commands = _fake_scan(repo_path, "java-spring")
        commands.commands[0].source = ""
        return inventory, commands

    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", fake_scan_without_source)

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 1, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    hard_gate_check = next(check for check in report["checks"] if check["id"] == "content:hard-gate-command-evidence")
    assert hard_gate_check["passed"] is False


def test_benchmark_schema_checks_fail_when_project_inventory_is_invalid(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    (ai / "project-inventory.json").write_text("{not valid json", encoding="utf-8")

    checks = _schema_checks(ai)

    project_inventory = next(check for check in checks if check["id"] == "schema:project-inventory")
    assert project_inventory["passed"] is False
    assert project_inventory["error"]


def test_benchmark_content_checks_fail_when_guide_required_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    (ai / "guides" / "project-context.md").write_text("# Project Context\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    guide_check = next(check for check in checks if check["id"] == "content:guides-quality")
    stack_check = next(check for check in checks if check["id"] == "content:stack-specific-guides")
    assert guide_check["passed"] is False
    assert stack_check["passed"] is False


def test_benchmark_quality_degrades_when_guide_lacks_evidence_reference(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    guide = ai / "guides" / "project-context.md"
    guide.write_text(guide.read_text(encoding="utf-8").replace("## 来源证据", "## 来源说明"), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    scores = _quality_scores(ai, inventory)

    item = scores["guide_quality"]["evidence_reference"]
    assert item["score"] < 5
    assert item["passed"] is False
    assert item["reasons"]


def test_benchmark_degrades_command_reliability_for_low_confidence_hard_gate(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    catalog_path = ai / "command-catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    catalog["commands"][0]["confidence"] = "low"
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    scores = _quality_scores(ai, inventory)

    item = scores["scan_quality"]["command_reliability"]
    assert item["score"] < 4
    assert item["passed"] is False
    assert item["reasons"]


def test_benchmark_content_checks_fail_when_workflow_skill_file_is_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    (ai / "skills" / "standard" / "SKILL.md").unlink()
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    workflow_skill = next(check for check in checks if check["id"] == "content:workflow-skills")
    harness_map_skill = next(check for check in checks if check["id"] == "content:workflow-skill-config-reference")
    assert workflow_skill["passed"] is False
    assert harness_map_skill["passed"] is False


def test_benchmark_content_checks_fail_when_standard_routing_rule_is_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    config_path = ai / "harness-config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["workflow_routing"]["rules"] = [
        rule for rule in config["workflow_routing"]["rules"] if rule["id"] != "standard-escalation"
    ]
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    routing_policy = next(check for check in checks if check["id"] == "content:workflow-routing-policy")
    assert routing_policy["passed"] is False
    assert "missing_standard_escalation" in routing_policy["errors"]


def test_benchmark_content_checks_fail_when_maturity_routing_evidence_is_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    evidence_path = ai / "maturity-evidence.yaml"
    evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    evidence["harness_assets"]["workflow_routing_rules"] = []
    evidence_path.write_text(yaml.safe_dump(evidence, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    routing_evidence = next(check for check in checks if check["id"] == "content:maturity-routing-evidence")
    assert routing_evidence["passed"] is False
    assert "missing_routing_evidence_detail" in routing_evidence["errors"]


def test_benchmark_records_absent_workflow_recommendation_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is True
    assert recommendation["present"] is False


def test_benchmark_records_absent_asset_candidates_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is True
    assert asset_candidates["present"] is False


def test_benchmark_records_absent_maturity_review_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is True
    assert review["present"] is False


def test_benchmark_accepts_valid_maturity_review_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is True
    assert review["present"] is True
    assert review["candidate_review_count"] == 1


def test_benchmark_fails_maturity_review_with_unknown_candidate(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    path = ai / "review" / "maturity-review.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidate_reviews"][0]["candidate_id"] = "missing-candidate"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "unknown_candidate_id" in review["errors"]


def test_benchmark_fails_maturity_review_with_outside_ai_evidence(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    path = ai / "review" / "maturity-review.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidate_reviews"][0]["evidence_sources"] = ["README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "evidence_source_outside_ai" in review["errors"]


def test_benchmark_fails_maturity_review_when_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    (ai / "review" / "maturity-review.md").write_text("# Maturity Review\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "missing_markdown_sections" in review["errors"]


def test_benchmark_accepts_valid_asset_candidate_review_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is True
    assert asset_candidates["present"] is True
    assert asset_candidates["candidate_count"] == 1


def test_benchmark_fails_asset_candidate_with_unknown_source_candidate(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    path = ai / "review" / "asset-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["source_candidate_id"] = "missing-candidate"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "unknown_source_candidate_id" in asset_candidates["errors"]


def test_benchmark_fails_asset_candidate_with_outside_ai_evidence(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    path = ai / "review" / "asset-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["evidence_sources"] = ["README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "evidence_source_outside_ai" in asset_candidates["errors"]


def test_benchmark_fails_asset_candidate_when_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    (ai / "review" / "asset-candidate-workflows.md").write_text("# Asset Candidate Workflows\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "missing_markdown_sections" in asset_candidates["errors"]


def test_benchmark_accepts_valid_workflow_recommendation_review_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is True
    assert recommendation["present"] is True
    assert recommendation["recommended_workflow"] == "bugfix"


def test_benchmark_fails_when_workflow_recommendation_references_unknown_workflow(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    path = ai / "review" / "workflow-routing-recommendation.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["recommended_workflow"] = "release"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "unknown_recommended_workflow" in recommendation["errors"]


def test_benchmark_fails_when_workflow_recommendation_references_unknown_rule(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    path = ai / "review" / "workflow-routing-recommendation.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["matched_rule_ids"] = ["missing-rule"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "unknown_matched_rule_ids" in recommendation["errors"]


def test_benchmark_fails_when_workflow_recommendation_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    (ai / "review" / "workflow-routing-recommendation.md").write_text("# Workflow Routing Recommendation\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "missing_markdown_sections" in recommendation["errors"]


def test_benchmark_accepts_valid_experience_summary_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is True
    assert summary["present"] is True
    assert summary["finding_count"] == 1


def test_benchmark_fails_experience_summary_with_outside_ai_evidence(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    path = ai / "experience" / "experience-summary.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["findings"][0]["evidence_sources"] = ["README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is False
    assert "evidence_source_outside_ai" in summary["errors"]


def test_benchmark_fails_experience_summary_when_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    (ai / "experience" / "experience-summary.md").write_text("# Experience Summary\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is False
    assert "missing_markdown_sections" in summary["errors"]
