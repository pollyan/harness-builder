from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GenerationTrace:
    repo: Path
    command: str
    run_id: str
    run_dir: Path
    events: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def start(cls, repo: Path, command: str, run_id: str | None = None) -> "GenerationTrace":
        root = repo.resolve()
        trace_run_id = run_id or f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{command}"
        run_dir = root / ".ai" / "runs" / trace_run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return cls(repo=root, command=command, run_id=trace_run_id, run_dir=run_dir)

    def event(self, stage: str, event_type: str, message: str, details: dict[str, Any] | None = None) -> None:
        payload = {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "command": self.command,
            "stage": stage,
            "event_type": event_type,
            "message": message,
            "details": details or {},
        }
        self.events.append(payload)
        with (self.run_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def artifact(self, path: Path, kind: str) -> None:
        rel = path.resolve().relative_to(self.repo).as_posix()
        item = {"path": rel, "kind": kind}
        if item not in self.artifacts:
            self.artifacts.append(item)

    def finish(self, status: str, summary: dict[str, Any] | None = None) -> None:
        stages = []
        for event in self.events:
            if event["stage"] not in stages:
                stages.append(event["stage"])
        trace = {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "command": self.command,
            "status": status,
            "repo_name": self.repo.name,
            "stages": stages,
            "summary": summary or {},
        }
        (self.run_dir / "trace.yaml").write_text(yaml.safe_dump(trace, sort_keys=False, allow_unicode=True), encoding="utf-8")
        artifacts = {"schema_version": "1.0", "run_id": self.run_id, "artifacts": self.artifacts}
        (self.run_dir / "artifacts.yaml").write_text(yaml.safe_dump(artifacts, sort_keys=False, allow_unicode=True), encoding="utf-8")
        (self.run_dir / "decision-log.md").write_text(self._decision_log(status, summary or {}, stages), encoding="utf-8")

    def _decision_log(self, status: str, summary: dict[str, Any], stages: list[str]) -> str:
        summary_lines = "\n".join(f"- `{key}`: `{value}`" for key, value in summary.items()) or "- No summary fields recorded."
        artifact_lines = "\n".join(f"- `{item['path']}` ({item['kind']})" for item in self.artifacts) or "- No artifacts recorded."
        warning_lines = "\n".join(
            f"- `{event['stage']}` {event['event_type']}: {event['message']}"
            for event in self.events
            if event["event_type"] in {"warning", "failed"}
        ) or "- No warning or failed events recorded."
        return (
            "# Generation Decision Log\n\n"
            f"- Run: `{self.run_id}`\n"
            f"- Command: `{self.command}`\n"
            f"- Status: `{status}`\n"
            f"- Stages: {', '.join(f'`{stage}`' for stage in stages) if stages else '`none`'}\n\n"
            "## Summary\n\n"
            f"{summary_lines}\n\n"
            "## Artifacts\n\n"
            f"{artifact_lines}\n\n"
            "## Warnings And Failures\n\n"
            f"{warning_lines}\n"
        )

