from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app
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


def test_fixture_cli_end_to_end_for_java_and_dotnet(tmp_path: Path, monkeypatch):
    cases = [
        ("mini-spring-boot", "java-spring"),
        ("mini-dotnet-webapi", "dotnet-aspnet"),
    ]
    runner = CliRunner()

    for fixture_name, profile in cases:
        repo = tmp_path / fixture_name
        shutil.copytree(FIXTURES / fixture_name, repo)
        monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path, stack=profile: _fake_scan(repo_path, stack))
        monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path, stack=profile: _fake_scan(repo_path, stack))

        init_result = runner.invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
        assert init_result.exit_code == 0, init_result.output

        assess_result = runner.invoke(app, ["assess", "--repo", str(repo)])
        assert assess_result.exit_code == 0, assess_result.output

        improve_result = runner.invoke(app, ["improve", "--repo", str(repo)])
        assert improve_result.exit_code == 0, improve_result.output

        benchmark_result = runner.invoke(app, ["benchmark", "--repo", str(repo), "--profile", profile])
        assert benchmark_result.exit_code == 0, benchmark_result.output

        assert not (repo / ".ai" / "task-runs").exists()
        assert (repo / ".ai" / "scan-metadata.yaml").exists()
        assert (repo / ".ai" / "llm-scan-proposal.json").exists()
        assert (repo / ".ai" / "skills" / "lightweight" / "SKILL.md").exists()
        assert (repo / ".ai" / "skills" / "bugfix" / "SKILL.md").exists()
        assert (repo / ".ai" / "skills" / "standard" / "SKILL.md").exists()
        assert (repo / ".ai" / "maturity-score.yaml").exists()
        assert (repo / ".ai" / "init-summary.md").exists()
        assert (repo / ".ai" / "improvement-candidates.yaml").exists()
        report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
        assert report["status"] == "passed"
        check_ids = {check["id"] for check in report["checks"]}
        assert "content:workflow-skills" in check_ids
        assert "content:guides-quality" in check_ids
        assert "content:sensors-quality" in check_ids
        assert "content:hard-gate-command-evidence" in check_ids
        assert "content:runtime-workflow-trace" not in check_ids
