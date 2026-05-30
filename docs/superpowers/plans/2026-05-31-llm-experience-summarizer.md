# LLM Experience Summarizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit `summarize-experience` command that uses LLM judgment to create review-only Experience Summary artifacts.

**Architecture:** Add a Pydantic schema for summary reports, an LLM parser/generator module, and a deterministic orchestration layer that gathers existing Experience/review evidence, writes schema-valid YAML and Markdown, refreshes Experience Index, and records trace artifacts. Maturity evidence then records summary availability and finding count without making benchmark require the new command.

**Tech Stack:** Python, Pydantic v2, PyYAML, Typer, pytest, DeepSeek client wrapper.

---

## Files

- Create: `src/harness_builder_agent/schemas/experience_summary.py`
- Create: `src/harness_builder_agent/tools/llm_experience_summarizer.py`
- Create: `src/harness_builder_agent/tools/summarize_experience.py`
- Modify: `src/harness_builder_agent/cli.py`
- Modify: `src/harness_builder_agent/schemas/maturity_evidence.py`
- Modify: `src/harness_builder_agent/tools/maturity_evidence.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Create: `tests/unit/test_llm_experience_summarizer.py`
- Modify: `tests/unit/test_maturity_evidence.py`
- Modify: `tests/integration/test_assess_improve_commands.py`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/engineering/llm-contracts.md`
- Modify: `docs/superpowers/plans/2026-05-31-llm-experience-summarizer.md`

## Task 1: Experience Summary Schema

- [ ] **Step 1: Write failing schema tests**

In `tests/unit/test_schema_contracts.py`, import `ExperienceSummaryReport` and add:

```python
def test_experience_summary_report_records_review_only_findings():
    report = ExperienceSummaryReport.model_validate(
        {
            "summary": "Repeated sensor gaps are blocking maturity improvement.",
            "findings": [
                {
                    "id": "sensor-feedback-coverage-gap",
                    "kind": "sensor_feedback",
                    "title": "Coverage gap blocks confidence",
                    "summary": "Pending improvements repeatedly mention missing sensor coverage.",
                    "evidence_sources": [".ai/experience/pending-improvements.md"],
                    "confidence": "medium",
                    "suggested_follow_up": "Create a reviewed sensor candidate.",
                }
            ],
            "warnings": ["Runtime task-runs are absent."],
        }
    )

    assert report.schema_version == "1.0"
    assert report.source == "llm_experience_summary"
    assert report.review_status == "pending_harness_maintainer_review"
    assert report.findings[0].kind == "sensor_feedback"
```

Add:

```python
def test_experience_summary_report_rejects_invalid_kind():
    with pytest.raises(ValidationError):
        ExperienceSummaryReport.model_validate(
            {
                "summary": "Invalid.",
                "findings": [
                    {
                        "id": "bad",
                        "kind": "not_allowed",
                        "title": "Bad",
                        "summary": "Bad.",
                        "evidence_sources": [".ai/experience/pending-improvements.md"],
                    }
                ],
            }
        )
```

- [ ] **Step 2: Run schema tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_experience_summary_report_records_review_only_findings tests/unit/test_schema_contracts.py::test_experience_summary_report_rejects_invalid_kind -q
```

Expected: fail because `experience_summary.py` does not exist.

- [ ] **Step 3: Implement schema**

Create `src/harness_builder_agent/schemas/experience_summary.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExperienceFinding(BaseModel):
    id: str
    kind: Literal["repair_pattern", "sensor_feedback", "team_preference", "workflow_gap", "risk_signal", "improvement_signal"]
    title: str
    summary: str
    evidence_sources: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    suggested_follow_up: str | None = None


class ExperienceSummaryReport(BaseModel):
    schema_version: str = "1.0"
    source: str = "llm_experience_summary"
    review_status: Literal["pending_harness_maintainer_review"] = "pending_harness_maintainer_review"
    summary: str
    findings: list[ExperienceFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Run schema tests and confirm pass**

Run the same pytest command. Expected: pass.

## Task 2: LLM Parser and Prompt Builder

- [ ] **Step 1: Write failing parser tests**

Create `tests/unit/test_llm_experience_summarizer.py`:

```python
import json

import pytest

from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.tools.llm_experience_summarizer import (
    build_experience_summary_messages,
    parse_experience_summary_response,
    summarize_experience_with_llm,
)


def _index() -> ExperienceIndex:
    return ExperienceIndex(
        experience_files={"pending-improvements.md": True},
        pending_improvement_count=1,
        asset_candidate_count=1,
        maturity_review_count=1,
        runtime_task_run_count=0,
    )


def _sources() -> dict[str, str]:
    return {
        ".ai/experience/pending-improvements.md": "- missing sensor coverage",
        ".ai/review/maturity-review.yaml": "summary: revise sensor candidate",
    }


def test_summarize_experience_with_llm_returns_schema_valid_summary():
    def caller(messages):
        assert "experience_index" in messages[-1]["content"]
        return json.dumps(
            {
                "summary": "Sensor coverage is the main repeated issue.",
                "findings": [
                    {
                        "id": "sensor-coverage-gap",
                        "kind": "sensor_feedback",
                        "title": "Sensor coverage gap",
                        "summary": "Pending improvements and review both mention sensor coverage.",
                        "evidence_sources": [".ai/experience/pending-improvements.md"],
                        "confidence": "high",
                        "suggested_follow_up": "Draft a reviewed sensor candidate.",
                    }
                ],
            }
        )

    report = summarize_experience_with_llm(_index(), _sources(), caller=caller)

    assert report.review_status == "pending_harness_maintainer_review"
    assert report.findings[0].kind == "sensor_feedback"


def test_parse_experience_summary_response_rejects_invalid_json():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_experience_summary_response("not json", set(_sources()))


def test_parse_experience_summary_response_rejects_non_ai_evidence_path():
    with pytest.raises(ValueError, match="under .ai/"):
        parse_experience_summary_response(
            json.dumps(
                {
                    "summary": "Bad path.",
                    "findings": [
                        {
                            "id": "bad",
                            "kind": "risk_signal",
                            "title": "Bad",
                            "summary": "Bad.",
                            "evidence_sources": ["README.md"],
                        }
                    ],
                }
            ),
            set(_sources()),
        )


def test_parse_experience_summary_response_rejects_unknown_evidence_source():
    with pytest.raises(ValueError, match="unknown evidence_sources"):
        parse_experience_summary_response(
            json.dumps(
                {
                    "summary": "Unknown source.",
                    "findings": [
                        {
                            "id": "unknown",
                            "kind": "risk_signal",
                            "title": "Unknown",
                            "summary": "Unknown.",
                            "evidence_sources": [".ai/experience/missing.md"],
                        }
                    ],
                }
            ),
            set(_sources()),
        )


def test_build_experience_summary_messages_includes_review_only_boundary():
    messages = build_experience_summary_messages(_index(), _sources())
    content = messages[-1]["content"]
    assert "Return one JSON object only" in content
    assert "Do not modify formal Guides" in content
```

- [ ] **Step 2: Run parser tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_experience_summarizer.py -q
```

Expected: fail because `llm_experience_summarizer.py` does not exist.

- [ ] **Step 3: Implement LLM module**

Create `src/harness_builder_agent/tools/llm_experience_summarizer.py` with:

```python
from __future__ import annotations

import json
import re
from collections.abc import Callable

from pydantic import ValidationError

from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig

EXPERIENCE_SUMMARY_PROMPT_VERSION = "llm-experience-summary-v1"


def summarize_experience_with_llm(
    index: ExperienceIndex,
    sources: dict[str, str],
    caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
) -> ExperienceSummaryReport:
    messages = build_experience_summary_messages(index, sources)
    content = caller(messages) if caller else call_deepseek(messages, config=config)
    if not content.strip():
        raise ValueError("DeepSeek experience summary response is empty")
    return parse_experience_summary_response(content, set(sources))


def build_experience_summary_messages(index: ExperienceIndex, sources: dict[str, str]) -> list[dict[str, str]]:
    schema_contract = """
Return one JSON object only. Do not include markdown commentary.

Field contract:
- schema_version: "1.0".
- source: "llm_experience_summary".
- review_status: "pending_harness_maintainer_review".
- summary: concise summary for a Harness Maintainer.
- findings[].kind must be repair_pattern, sensor_feedback, team_preference, workflow_gap, risk_signal, or improvement_signal.
- findings[].evidence_sources must reference provided .ai evidence paths.
- findings[].confidence must be low, medium, or high.

Do not modify formal Guides, Sensors, Workflow Skills, or harness-config.
Do not claim any candidate has been applied.
Use warnings when Runtime task-run evidence is absent or evidence is sparse.
""".strip()
    payload = {
        "prompt_version": EXPERIENCE_SUMMARY_PROMPT_VERSION,
        "experience_index": index.model_dump(mode="json"),
        "sources": sources,
    }
    return [
        {
            "role": "system",
            "content": "You summarize Harness Builder Experience evidence into strict JSON review-only findings.",
        },
        {
            "role": "user",
            "content": f"{schema_contract}\n\nExperience input JSON:\n{json.dumps(payload, ensure_ascii=False)}",
        },
    ]


def parse_experience_summary_response(content: str, evidence_sources: set[str]) -> ExperienceSummaryReport:
    raw = _extract_json_text(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek experience summary response must be valid JSON") from exc
    try:
        report = ExperienceSummaryReport.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"DeepSeek experience summary response failed schema validation: {exc}") from exc
    bad_paths = sorted({source for finding in report.findings for source in finding.evidence_sources if not source.startswith(".ai/")})
    if bad_paths:
        raise ValueError(f"DeepSeek experience summary evidence_sources must be under .ai/: {', '.join(bad_paths)}")
    unknown = sorted({source for finding in report.findings for source in finding.evidence_sources if source not in evidence_sources})
    if unknown:
        raise ValueError(f"DeepSeek experience summary referenced unknown evidence_sources: {', '.join(unknown)}")
    return report


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\\s*(.*?)```", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped
```

- [ ] **Step 4: Run parser tests and confirm pass**

Run the same pytest command. Expected: pass.

## Task 3: Command Orchestration

- [ ] **Step 1: Write failing integration test**

In `tests/integration/test_assess_improve_commands.py`, import `ExperienceSummaryReport` and add:

```python
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
```

- [ ] **Step 2: Run integration test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_summarize_experience_writes_review_only_summary -q
```

Expected: fail because the CLI command does not exist.

- [ ] **Step 3: Implement orchestrator and CLI**

Create `src/harness_builder_agent/tools/summarize_experience.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.experience_index import write_experience_index
from harness_builder_agent.tools.llm_experience_summarizer import summarize_experience_with_llm

SOURCE_PATHS = [
    ".ai/experience/pending-improvements.md",
    ".ai/experience/project-experience.md",
    ".ai/experience/repair-patterns.md",
    ".ai/experience/sensor-feedback.md",
    ".ai/experience/team-preferences.md",
    ".ai/experience/deprecated-experience.md",
    ".ai/review/maturity-review.yaml",
    ".ai/review/asset-candidates.yaml",
]


def summarize_experience(repo: Path) -> Path:
    root = repo.resolve()
    ai = root / ".ai"
    if not ai.exists():
        raise FileNotFoundError(f"Missing .ai harness directory: {ai}")
    if not (ai / "experience" / "experience-index.yaml").exists():
        write_experience_index(ai)
    index = ExperienceIndex.model_validate(yaml.safe_load((ai / "experience" / "experience-index.yaml").read_text(encoding="utf-8")))
    sources = _collect_sources(root)
    report = summarize_experience_with_llm(index, sources)
    _write_yaml(ai / "experience" / "experience-summary.yaml", report.model_dump(mode="json"))
    (ai / "experience" / "experience-summary.md").write_text(_summary_markdown(report), encoding="utf-8")
    write_experience_index(ai)
    assess_maturity(root)
    return ai


def _collect_sources(root: Path) -> dict[str, str]:
    sources: dict[str, str] = {}
    for rel in SOURCE_PATHS:
        path = root / rel
        if path.exists():
            sources[rel] = path.read_text(encoding="utf-8")[:12000]
    task_runs = root / ".ai" / "task-runs"
    if task_runs.exists():
        for run_dir in sorted(path for path in task_runs.iterdir() if path.is_dir()):
            sources[f".ai/task-runs/{run_dir.name}/"] = "\\n".join(sorted(item.name for item in run_dir.iterdir()))[:12000]
    return sources


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _summary_markdown(report: ExperienceSummaryReport) -> str:
    finding_sections = "\\n\\n".join(
        f"### {item.title}\\n\\n"
        f"- id: `{item.id}`\\n"
        f"- kind: `{item.kind}`\\n"
        f"- confidence: `{item.confidence}`\\n"
        f"- evidence: {', '.join(f'`{source}`' for source in item.evidence_sources) or 'none'}\\n\\n"
        f"{item.summary}\\n\\n"
        f"Follow-up: {item.suggested_follow_up or 'None.'}"
        for item in report.findings
    ) or "No findings."
    warnings = "\\n".join(f"- {item}" for item in report.warnings) or "- None."
    return (
        "# Experience Summary\\n\\n"
        f"- review status: `{report.review_status}`\\n"
        f"- source: `{report.source}`\\n\\n"
        "## Summary\\n\\n"
        f"{report.summary}\\n\\n"
        "## Findings\\n\\n"
        f"{finding_sections}\\n\\n"
        "## Warnings\\n\\n"
        f"{warnings}\\n"
    )
```

Modify `src/harness_builder_agent/cli.py` to import `summarize_experience` and add command:

```python
@app.command("summarize-experience")
def summarize_experience_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
    """Run LLM semantic summarization over review-only Experience evidence."""
    trace = GenerationTrace.start(repo, "summarize-experience")
    try:
        trace.event("experience-summary", "started", "LLM experience summary started.")
        output_dir = summarize_experience(repo)
        trace.artifact(output_dir / "experience" / "experience-summary.yaml", "experience_summary")
        trace.artifact(output_dir / "experience" / "experience-summary.md", "experience")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.event("experience-summary", "completed", "LLM experience summary completed.", {"artifact_count": 3})
        trace.finish("completed", {"artifact_count": 3})
    except Exception as exc:
        trace.event("experience-summary", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated experience summary in {output_dir / 'experience'}")
```

- [ ] **Step 4: Run integration test and confirm pass**

Run the same pytest command. Expected: pass.

## Task 4: Maturity Evidence and Docs

- [ ] **Step 1: Write failing maturity evidence assertions**

In `tests/unit/test_maturity_evidence.py`, extend the index-backed test by writing `.ai/experience/experience-summary.yaml`:

```python
_write_yaml(
    ai / "experience" / "experience-summary.yaml",
    {
        "summary": "Sensor coverage is the main signal.",
        "findings": [
            {
                "id": "sensor-coverage-gap",
                "kind": "sensor_feedback",
                "title": "Sensor coverage gap",
                "summary": "Pending improvements point to missing coverage.",
                "evidence_sources": [".ai/experience/pending-improvements.md"],
            }
        ],
    },
)
```

Assert:

```python
assert pack.experience.has_experience_summary is True
assert pack.experience.experience_summary_finding_count == 1
```

- [ ] **Step 2: Run maturity evidence test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_maturity_evidence.py::test_collect_maturity_evidence_uses_experience_index -q
```

Expected: fail because summary fields do not exist.

- [ ] **Step 3: Extend maturity evidence**

In `src/harness_builder_agent/schemas/maturity_evidence.py`, add to `ExperienceEvidence`:

```python
has_experience_summary: bool = False
experience_summary_finding_count: int = 0
```

In `src/harness_builder_agent/tools/maturity_evidence.py`:

1. Import `ExperienceSummaryReport`.
2. Add `.ai/experience/experience-summary.yaml` to `MATURITY_INPUTS`.
3. In `_experience`, after computing index fields, read and validate summary if present:

```python
summary = _experience_summary(ai)
...
has_experience_summary=summary is not None,
experience_summary_finding_count=len(summary.findings) if summary else 0,
```

Add helper:

```python
def _experience_summary(ai: Path) -> ExperienceSummaryReport | None:
    path = ai / "experience" / "experience-summary.yaml"
    if not path.exists():
        return None
    return ExperienceSummaryReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
```

- [ ] **Step 4: Update engineering docs**

In `docs/engineering/init-workflow.md`, add `.ai/experience/experience-summary.yaml` to optional semantic/machine Experience assets for explicit summarize command, and state benchmark does not require it yet.

In `docs/engineering/llm-contracts.md`, add `experience summary report` to machine-consumed LLM outputs and add parser test expectations.

- [ ] **Step 5: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_llm_experience_summarizer.py tests/unit/test_maturity_evidence.py tests/integration/test_assess_improve_commands.py -q
```

Expected: pass.

## Task 5: Verification and Commit

- [ ] **Step 1: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 2: Self-Harness Improvement Gate**

Record the gate result in this plan. Expected checks:

- New LLM output has Pydantic schema and parser tests.
- Explicit command has integration coverage and trace artifacts.
- Formal Harness assets are not overwritten.
- Benchmark is not changed because this command is optional and not part of `init` yet.
- Next likely gap is feeding Experience Summary into maturity review and asset candidate prompts.

- [ ] **Step 3: Commit**

Run:

```bash
git add src/harness_builder_agent/schemas/experience_summary.py src/harness_builder_agent/tools/llm_experience_summarizer.py src/harness_builder_agent/tools/summarize_experience.py src/harness_builder_agent/cli.py src/harness_builder_agent/schemas/maturity_evidence.py src/harness_builder_agent/tools/maturity_evidence.py tests/unit/test_schema_contracts.py tests/unit/test_llm_experience_summarizer.py tests/unit/test_maturity_evidence.py tests/integration/test_assess_improve_commands.py docs/engineering/init-workflow.md docs/engineering/llm-contracts.md docs/superpowers/specs/2026-05-31-llm-experience-summarizer-design.md docs/superpowers/plans/2026-05-31-llm-experience-summarizer.md
git commit -m "feat: add llm experience summarizer"
```

Expected: commit succeeds after pre-commit fast regression.
