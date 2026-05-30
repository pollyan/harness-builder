from __future__ import annotations

import json
from pathlib import Path

import yaml

from harness_builder_agent.tools.generation_trace import GenerationTrace


def test_generation_trace_writes_events_summary_and_artifacts(tmp_path: Path):
    trace = GenerationTrace.start(tmp_path, command="init", run_id="20260530-120000-init")

    trace.event("scan", "started", "Scan started.")
    trace.event("scan", "completed", "Scan completed.", {"primary_stack": "java-spring", "command_count": 1})
    trace.artifact(tmp_path / ".ai" / "project-inventory.json", "inventory")
    trace.finish("completed", {"primary_stack": "java-spring", "command_count": 1})

    run_dir = tmp_path / ".ai" / "runs" / "20260530-120000-init"
    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text().splitlines()]
    assert events[0]["schema_version"] == "1.0"
    assert events[0]["run_id"] == "20260530-120000-init"
    assert events[0]["command"] == "init"
    assert events[0]["stage"] == "scan"
    assert events[0]["event_type"] == "started"
    assert events[1]["details"]["primary_stack"] == "java-spring"

    trace_yaml = yaml.safe_load((run_dir / "trace.yaml").read_text())
    assert trace_yaml["schema_version"] == "1.0"
    assert trace_yaml["status"] == "completed"
    assert trace_yaml["summary"]["primary_stack"] == "java-spring"
    assert trace_yaml["stages"] == ["scan"]

    artifacts = yaml.safe_load((run_dir / "artifacts.yaml").read_text())
    assert artifacts["schema_version"] == "1.0"
    assert artifacts["artifacts"] == [{"path": ".ai/project-inventory.json", "kind": "inventory"}]

    decision_log = (run_dir / "decision-log.md").read_text()
    assert "java-spring" in decision_log
    assert "scan" in decision_log

