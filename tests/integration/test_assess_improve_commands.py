from __future__ import annotations

import shutil
import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app
from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
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


def _prepared_harness_repo(tmp_path: Path, fixture_name: str, primary_stack: str, monkeypatch) -> Path:
    repo = tmp_path / fixture_name
    shutil.copytree(FIXTURES / fixture_name, repo)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, primary_stack))
    runner = CliRunner()
    init_result = runner.invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert init_result.exit_code == 0, init_result.output
    return repo


def _latest_trace(repo: Path) -> dict:
    runs = sorted((repo / ".ai" / "runs").iterdir())
    assert runs
    return yaml.safe_load((runs[-1] / "trace.yaml").read_text(encoding="utf-8"))


def test_assess_generates_maturity_score_from_current_harness(tmp_path: Path, monkeypatch):
    repo = _prepared_harness_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    (repo / ".ai" / "maturity-evidence.yaml").unlink()

    result = CliRunner().invoke(app, ["assess", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    score = yaml.safe_load((repo / ".ai" / "maturity-score.yaml").read_text(encoding="utf-8"))
    report = (repo / ".ai" / "maturity-report.md").read_text(encoding="utf-8")
    assert score["schema_version"] == "1.0"
    assert score["overall_level"].startswith("L")
    assert "workflow" in score["dimension_scores"]
    assert score["dimension_scores"]["observability"] == "L1"
    expected_dimensions = {
        "guides",
        "sensors",
        "workflow",
        "risk_control",
        "repair_loop",
        "observability",
        "experience",
        "verification_sophistication",
        "governance_auditability",
    }
    assert set(score["dimensions"]) == expected_dimensions
    assert score["target_next_level"] == "L3"
    assert score["dimensions"]["guides"]["evidence"]
    assert score["dimensions"]["sensors"]["next_level_requirements"]
    assert score["next_steps"]
    assert score["evidence"]
    assert score["blocking_reasons"]
    assert score["recommended_next_steps"]
    evidence_pack = yaml.safe_load((repo / ".ai" / "maturity-evidence.yaml").read_text(encoding="utf-8"))
    assert evidence_pack["schema_version"] == "1.0"
    assert evidence_pack["primary_stack"] == "java-spring"
    assert evidence_pack["harness_assets"]["workflow_skill_count"] == 3
    assert evidence_pack["harness_assets"]["workflow_routing_rule_count"] == 3
    assert evidence_pack["harness_assets"]["has_standard_escalation_rule"] is True
    assert evidence_pack["observability"]["generation_run_count"] >= 1
    assert "## 证据" in report
    assert "## 维度详情" in report
    assert "## 下一等级要求" in report
    assert not (repo / ".ai" / "task-runs").exists()
    trace = _latest_trace(repo)
    assert trace["command"] == "assess"
    assert trace["status"] == "completed"
    assert "maturity" in trace["stages"]
    artifacts = yaml.safe_load((repo / ".ai" / "runs" / trace["run_id"] / "artifacts.yaml").read_text(encoding="utf-8"))
    assert {"path": ".ai/maturity-evidence.yaml", "kind": "maturity_evidence"} in artifacts["artifacts"]


def test_improve_generates_reviewable_improvement_candidates(tmp_path: Path, monkeypatch):
    repo = _prepared_harness_repo(tmp_path, "mini-dotnet-webapi", "dotnet-aspnet", monkeypatch)
    runner = CliRunner()
    assess_result = runner.invoke(app, ["assess", "--repo", str(repo)])
    assert assess_result.exit_code == 0, assess_result.output
    (repo / ".ai" / "maturity-evidence.yaml").unlink()

    result = runner.invoke(app, ["improve", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    assert (repo / ".ai" / "maturity-evidence.yaml").exists()
    candidates = yaml.safe_load((repo / ".ai" / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    pending = (repo / ".ai" / "experience" / "pending-improvements.md").read_text(encoding="utf-8")
    evolution = (repo / ".ai" / "evolution-plan.md").read_text(encoding="utf-8")
    experience_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert candidates["schema_version"] == "1.0"
    assert candidates["candidates"]
    first = candidates["candidates"][0]
    assert first["candidate_type"] in {"guide_update", "sensor_update", "workflow_policy_update", "maturity_action"}
    assert first["suggested_target"].startswith(".ai/")
    assert first["human_confirmation_required"] is True
    assert first["target_dimension"]
    assert first["source_next_step"] or first["source_blocking_cap"]
    assert first["acceptance_checks"]
    assert ".ai/maturity-evidence.yaml" in first["evidence_sources"]
    assert "## 待确认改进候选" in pending
    assert "Acceptance checks" in pending
    assert experience_index["pending_improvement_count"] >= 1
    assert "## 优先级路线图" in evolution
    assert "Maturity dimension" in evolution
    trace = _latest_trace(repo)
    assert trace["command"] == "improve"
    assert trace["status"] == "completed"
    assert "improvement" in trace["stages"]


def test_assess_handles_empty_command_catalog_by_lowering_sensor_maturity(tmp_path: Path, monkeypatch):
    repo = _prepared_harness_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    (repo / ".ai" / "command-catalog.yaml").write_text("schema_version: '1.0'\ncommands: []\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["assess", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    score = yaml.safe_load((repo / ".ai" / "maturity-score.yaml").read_text(encoding="utf-8"))
    assert score["schema_version"] == "1.0"
    assert score["overall_level"] == "L0"
    assert score["dimension_scores"]["sensors"] == "L0"
    assert score["dimensions"]["sensors"]["level"] == "L0"
    assert any(cap["id"] == "no-executable-sensors" and cap["active"] for cap in score["blocking_caps"])
    assert any(step["target_dimension"] == "sensors" for step in score["next_steps"])
    assert "验证命令数量：0" in score["evidence"]


def test_improve_candidates_are_reviewable_and_target_ai_assets(tmp_path: Path, monkeypatch):
    repo = _prepared_harness_repo(tmp_path, "mini-dotnet-webapi", "dotnet-aspnet", monkeypatch)

    result = CliRunner().invoke(app, ["improve", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    candidates = yaml.safe_load((repo / ".ai" / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    assert candidates["candidates"]
    assert all(item["human_confirmation_required"] is True for item in candidates["candidates"])
    assert all(item["suggested_target"].startswith(".ai/") for item in candidates["candidates"])


def test_review_maturity_writes_llm_review_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepared_harness_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    runner = CliRunner()
    assess_result = runner.invoke(app, ["assess", "--repo", str(repo)])
    assert assess_result.exit_code == 0, assess_result.output
    improve_result = runner.invoke(app, ["improve", "--repo", str(repo)])
    assert improve_result.exit_code == 0, improve_result.output
    (repo / ".ai" / "experience" / "experience-summary.yaml").write_text(
        yaml.safe_dump(
            {
                "summary": "Sensor coverage is the repeated signal.",
                "findings": [
                    {
                        "id": "sensor-coverage-gap",
                        "kind": "sensor_feedback",
                        "title": "Sensor coverage gap",
                        "summary": "Pending improvements point to missing sensor coverage.",
                        "evidence_sources": [".ai/experience/pending-improvements.md"],
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    def fake_review(score, evidence_pack, candidates, experience_summary=None):
        assert experience_summary is not None
        assert experience_summary.findings[0].id == "sensor-coverage-gap"
        return MaturityReviewReport(
            summary="Candidates are aligned.",
            reviewer_model="deepseek-test",
            candidate_reviews=[
                {
                    "candidate_id": candidates.candidates[0].id,
                    "decision": "support",
                    "rationale": "Candidate is grounded in maturity evidence.",
                    "suggested_acceptance_checks": ["Run benchmark."],
                    "evidence_sources": [".ai/maturity-evidence.yaml"],
                }
            ],
        )

    monkeypatch.setattr("harness_builder_agent.tools.review_maturity.review_maturity_with_llm", fake_review)

    result = runner.invoke(app, ["review-maturity", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    review = yaml.safe_load((repo / ".ai" / "review" / "maturity-review.yaml").read_text(encoding="utf-8"))
    markdown = (repo / ".ai" / "review" / "maturity-review.md").read_text(encoding="utf-8")
    assert review["schema_version"] == "1.0"
    assert review["candidate_reviews"][0]["decision"] == "support"
    assert "# Maturity Review" in markdown
    assert "## Candidate Reviews" in markdown
    trace = _latest_trace(repo)
    assert trace["command"] == "review-maturity"


def test_generate_asset_candidates_writes_review_only_drafts(tmp_path: Path, monkeypatch):
    repo = _prepared_harness_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    runner = CliRunner()
    assess_result = runner.invoke(app, ["assess", "--repo", str(repo)])
    assert assess_result.exit_code == 0, assess_result.output
    improve_result = runner.invoke(app, ["improve", "--repo", str(repo)])
    assert improve_result.exit_code == 0, improve_result.output

    def fake_review(score, evidence_pack, candidates, experience_summary=None):
        return MaturityReviewReport(
            summary="Candidates are aligned.",
            candidate_reviews=[
                {
                    "candidate_id": candidates.candidates[0].id,
                    "decision": "support",
                    "rationale": "Candidate is grounded in maturity evidence.",
                }
            ],
        )

    monkeypatch.setattr("harness_builder_agent.tools.review_maturity.review_maturity_with_llm", fake_review)
    review_result = runner.invoke(app, ["review-maturity", "--repo", str(repo)])
    assert review_result.exit_code == 0, review_result.output
    formal_guide_before = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    (repo / ".ai" / "experience" / "experience-summary.yaml").write_text(
        yaml.safe_dump(
            {
                "summary": "Workflow gaps are repeated.",
                "findings": [
                    {
                        "id": "workflow-gap-routing",
                        "kind": "workflow_gap",
                        "title": "Workflow routing gap",
                        "summary": "Experience findings point to missing routing rules.",
                        "evidence_sources": [".ai/experience/experience-summary.yaml"],
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    def fake_asset_candidates(score, evidence_pack, improvement_candidates, maturity_review, experience_summary=None):
        assert experience_summary is not None
        assert experience_summary.findings[0].kind == "workflow_gap"
        return AssetCandidateReport(
            candidates=[
                {
                    "id": "guide-project-context-scope",
                    "kind": "guide",
                    "source_candidate_id": improvement_candidates.candidates[0].id,
                    "source_review_decision": "support",
                    "suggested_path": ".ai/guides/project-context.md",
                    "title": "Scope project context guide",
                    "rationale": "Candidate is grounded in maturity review.",
                    "draft_content": "## Candidate Addition\n\nAdd task loading scope.",
                    "evidence_sources": [".ai/maturity-evidence.yaml"],
                    "acceptance_checks": ["Benchmark content:guides-quality passes."],
                    "risk_level": "medium",
                }
            ]
        )

    monkeypatch.setattr(
        "harness_builder_agent.tools.generate_asset_candidates.generate_asset_candidates_with_llm",
        fake_asset_candidates,
    )

    result = runner.invoke(app, ["generate-asset-candidates", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    asset_report = yaml.safe_load((repo / ".ai" / "review" / "asset-candidates.yaml").read_text(encoding="utf-8"))
    guide_md = (repo / ".ai" / "review" / "asset-candidate-guides.md").read_text(encoding="utf-8")
    experience_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert asset_report["schema_version"] == "1.0"
    assert asset_report["candidates"][0]["review_status"] == "pending_harness_maintainer_review"
    assert "# Asset Candidate Guides" in guide_md
    assert "Scope project context guide" in guide_md
    assert (repo / ".ai" / "review" / "asset-candidate-sensors.md").exists()
    assert (repo / ".ai" / "review" / "asset-candidate-workflows.md").exists()
    assert experience_index["asset_candidate_count"] == 1
    assert (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8") == formal_guide_before
    trace = _latest_trace(repo)
    assert trace["command"] == "generate-asset-candidates"


def test_summarize_experience_writes_review_only_summary(tmp_path: Path, monkeypatch):
    repo = _prepared_harness_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    runner = CliRunner()
    assess_result = runner.invoke(app, ["assess", "--repo", str(repo)])
    assert assess_result.exit_code == 0, assess_result.output
    improve_result = runner.invoke(app, ["improve", "--repo", str(repo)])
    assert improve_result.exit_code == 0, improve_result.output
    formal_guide_before = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")

    def fake_summary(index, sources):
        assert ".ai/experience/pending-improvements.md" in sources
        return ExperienceSummaryReport(
            summary="Sensor coverage is the main experience signal.",
            findings=[
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
            warnings=["Runtime task-runs are absent."],
        )

    monkeypatch.setattr("harness_builder_agent.tools.summarize_experience.summarize_experience_with_llm", fake_summary)

    result = runner.invoke(app, ["summarize-experience", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    summary = yaml.safe_load((repo / ".ai" / "experience" / "experience-summary.yaml").read_text(encoding="utf-8"))
    markdown = (repo / ".ai" / "experience" / "experience-summary.md").read_text(encoding="utf-8")
    evidence_pack = yaml.safe_load((repo / ".ai" / "maturity-evidence.yaml").read_text(encoding="utf-8"))
    assert summary["review_status"] == "pending_harness_maintainer_review"
    assert summary["findings"][0]["kind"] == "sensor_feedback"
    assert "# Experience Summary" in markdown
    assert "## Findings" in markdown
    assert evidence_pack["experience"]["has_experience_summary"] is True
    assert evidence_pack["experience"]["experience_summary_finding_count"] == 1
    assert not (repo / ".ai" / "task-runs").exists()
    assert (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8") == formal_guide_before
    trace = _latest_trace(repo)
    assert trace["command"] == "summarize-experience"
