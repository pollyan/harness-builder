from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness_builder_agent.tools.scan_repo import scan_repository

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _llm_response(primary_stack: str) -> str:
    if primary_stack == "java-spring":
        command = {"id": "unit_test", "command": "mvn test", "type": "test", "gate": "hard", "source": "pom.xml", "confidence": "high"}
        stacks = ["java", "maven", "spring-boot"]
        modules = [{"name": "app", "path": ".", "kind": "backend"}]
        summary = "Java Spring project."
    else:
        command = {
            "id": "unit_test",
            "command": "dotnet test",
            "type": "test",
            "gate": "hard",
            "source": "mini-dotnet-webapi.sln",
            "confidence": "high",
        }
        stacks = ["dotnet", "aspnet-core"]
        modules = [{"name": "MiniApi", "path": "src", "kind": "backend"}]
        summary = ".NET ASP.NET project."
    return json.dumps(
        {
            "primary_stack": primary_stack,
            "stacks": stacks,
            "modules": modules,
            "architecture_signals": [],
            "risk_areas": [],
            "command_candidates": [command],
            "configs": [],
            "ci_files": [],
            "confidence": "high",
            "needs_human_confirmation": False,
            "reasoning_summary": summary,
        }
    )


def test_scan_repository_uses_llm_for_java_spring_fixture():
    inventory, commands = scan_repository(FIXTURES / "mini-spring-boot", llm_caller=lambda _messages: _llm_response("java-spring"))

    assert inventory.repo_name == "mini-spring-boot"
    assert inventory.primary_stack == "java-spring"
    assert "spring-boot" in inventory.stacks
    assert inventory.stack_extensions["scan_metadata"]["llm_status"] == "succeeded"
    assert inventory.stack_extensions["llm_scan_proposal"]["primary_stack"] == "java-spring"
    assert any(command.id == "unit_test" and command.command == "mvn test" and command.gate == "hard" for command in commands.commands)


def test_scan_repository_uses_llm_for_dotnet_fixture():
    inventory, commands = scan_repository(FIXTURES / "mini-dotnet-webapi", llm_caller=lambda _messages: _llm_response("dotnet-aspnet"))

    assert inventory.repo_name == "mini-dotnet-webapi"
    assert inventory.primary_stack == "dotnet-aspnet"
    assert "aspnet-core" in inventory.stacks
    assert inventory.stack_extensions["scan_metadata"]["llm_status"] == "succeeded"
    assert any(command.id == "unit_test" and command.command == "dotnet test" and command.gate == "hard" for command in commands.commands)


def test_scan_repository_fails_when_llm_claim_conflicts_with_hard_evidence():
    with pytest.raises(ValueError, match="dotnet"):
        scan_repository(FIXTURES / "mini-spring-boot", llm_caller=lambda _messages: _llm_response("dotnet-aspnet"))


def test_scan_repository_uses_llm_evidence_plan_before_final_scan(tmp_path: Path):
    (tmp_path / "pom.xml").write_text("<project><artifactId>demo</artifactId></project>", encoding="utf-8")
    (tmp_path / "src").mkdir()
    for index in range(25):
        (tmp_path / "src" / f"Ordinary{index:02d}.java").write_text(f"class Ordinary{index:02d} {{}}", encoding="utf-8")
    (tmp_path / "src" / "zz_RefundRiskService.java").write_text(
        "class RefundRiskService { void refund() {} }",
        encoding="utf-8",
    )

    calls: list[str] = []

    def planner_caller(messages):
        calls.append("planner")
        combined = "\n".join(message["content"] for message in messages)
        content = messages[-1]["content"]
        assert "zz_RefundRiskService.java" in content
        assert '"path": "src/zz_RefundRiskService.java"' in content
        assert '"bucket": "source:.java"' in content
        assert '"reason": "Representative .java source sample."' in content
        assert "全量轻量 file manifest" in combined
        return json.dumps(
            {
                "schema_version": "1.0",
                "requested_paths": ["src/zz_RefundRiskService.java"],
                "risk_focus": ["refund flow"],
                "rationale": "The planner selected the hidden refund risk file from the full index.",
                "confidence": "high",
            }
        )

    def scan_caller(messages):
        calls.append("scan")
        content = messages[-1]["content"]
        assert '"llm_requested_files"' in content
        assert "RefundRiskService" in content
        return _llm_response("java-spring")

    inventory, _commands = scan_repository(
        tmp_path,
        llm_caller=scan_caller,
        evidence_planner_caller=planner_caller,
    )

    assert calls == ["planner", "scan"]
    assert inventory.primary_stack == "java-spring"
    metadata = inventory.stack_extensions["scan_metadata"]
    assert metadata["evidence_expansion"]["requested_paths"] == ["src/zz_RefundRiskService.java"]
    assert metadata["evidence_expansion"]["risk_focus"] == ["refund flow"]
    assert metadata["evidence_expansion"]["rationale"] == "The planner selected the hidden refund risk file from the full index."
    assert metadata["evidence_expansion"]["read_paths"] == ["src/zz_RefundRiskService.java"]
    assert metadata["evidence_expansion"]["read_file_count"] == 1


def test_scan_repository_reports_progress_for_each_stage(tmp_path: Path):
    (tmp_path / "pom.xml").write_text("<project><artifactId>demo</artifactId></project>", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Demo.java").write_text("class Demo {}", encoding="utf-8")
    events = []

    def planner_caller(_messages):
        return json.dumps(
            {
                "schema_version": "1.0",
                "requested_paths": ["src/Demo.java"],
                "risk_focus": [],
                "rationale": "Read source entry.",
                "confidence": "high",
            }
        )

    def scan_caller(_messages):
        return _llm_response("java-spring")

    scan_repository(
        tmp_path,
        llm_caller=scan_caller,
        evidence_planner_caller=planner_caller,
        progress=events.append,
    )

    assert [(event.phase, event.status) for event in events] == [
        ("collect-evidence", "started"),
        ("collect-evidence", "completed"),
        ("plan-evidence-expansion", "started"),
        ("plan-evidence-expansion", "completed"),
        ("expand-evidence", "started"),
        ("expand-evidence", "completed"),
        ("llm-scan", "started"),
        ("llm-scan", "completed"),
        ("reconcile-scan", "started"),
        ("reconcile-scan", "completed"),
    ]
    assert events[1].details["evidence_file_count"] >= 1
    assert events[5].details["requested_path_count"] == 1
    assert events[-1].details["command_count"] == 1
