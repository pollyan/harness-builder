# LLM-first Scan Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace deterministic scan decisions with a DeepSeek-required, LLM-first scan layer while preserving the current `harness-builder-agent` CLI contract.

**Architecture:** Split scanning into Evidence Collector, DeepSeek Analyzer, Reconciler, and Scan Facade. Deterministic code only collects evidence; DeepSeek produces the strict scan proposal; Reconciler validates conflicts and writes auditable metadata. Tests use mock LLM in unit/integration/CI and real DeepSeek only in explicit acceptance tests.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, Typer, pytest, standard-library urllib.

---

## File Structure

- Create `src/harness_builder_agent/schemas/scan.py`: Pydantic contracts for evidence, LLM proposal, warnings, metadata.
- Create `src/harness_builder_agent/tools/evidence_collector.py`: deterministic fact collection only.
- Create `src/harness_builder_agent/tools/llm_config.py`: `.env` loading and DeepSeek config validation.
- Create `src/harness_builder_agent/tools/deepseek_client.py`: OpenAI-compatible DeepSeek chat call.
- Create `src/harness_builder_agent/tools/llm_scan_analyzer.py`: prompt construction, response parsing, strict proposal validation.
- Create `src/harness_builder_agent/tools/scan_reconciler.py`: convert proposal + evidence into `ProjectInventory`, `CommandCatalog`, metadata.
- Modify `src/harness_builder_agent/tools/scan_repo.py`: keep facade, delegate to the new layers, no fallback.
- Modify `src/harness_builder_agent/tools/write_assets.py`: write `scan-metadata.yaml` and `llm-scan-proposal.json`.
- Modify `src/harness_builder_agent/tools/benchmark.py`: require scan metadata/proposal and fail benchmark on hard gate sensor failed/skipped.
- Modify tests under `tests/unit`, `tests/integration`, `tests/e2e`; add explicit `tests/acceptance/test_real_llm_scan.py`.
- Modify `pyproject.toml`: keep default pytest away from `tests/acceptance`.
- Modify `README.md`: document mock CI tests and explicit real DeepSeek acceptance command.

---

### Task 1: Evidence Collector

**Files:**
- Create: `src/harness_builder_agent/schemas/scan.py`
- Create: `src/harness_builder_agent/tools/evidence_collector.py`
- Test: `tests/unit/test_evidence_collector.py`

- [ ] **Step 1: Write failing collector tests**

```python
from pathlib import Path

from harness_builder_agent.tools.evidence_collector import collect_evidence

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_collect_evidence_captures_key_files_without_stack_decision():
    bundle = collect_evidence(FIXTURES / "minimal-java-maven")

    assert bundle.repo_name == "minimal-java-maven"
    assert any(item.path == "pom.xml" for item in bundle.key_files)
    assert any(item.path == "frontend/package.json" for item in bundle.key_files)
    assert any(item.path == "app/src/main/resources/application.yml" for item in bundle.config_files)
    assert bundle.detected_file_count > 0
    assert "primary_stack" not in bundle.model_dump()


def test_collect_evidence_ignores_generated_and_dependency_dirs(tmp_path: Path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai" / "project-inventory.json").write_text("{}", encoding="utf-8")
    (tmp_path / "pom.xml").write_text("<project />", encoding="utf-8")

    bundle = collect_evidence(tmp_path)

    paths = {item.path for item in bundle.files}
    assert "pom.xml" in paths
    assert "node_modules/package.json" not in paths
    assert ".ai/project-inventory.json" not in paths
```

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m pytest tests/unit/test_evidence_collector.py -q`

Expected: fail because `evidence_collector` does not exist.

- [ ] **Step 3: Implement schemas and collector**

Implement `EvidenceFile`, `EvidenceBundle`, file walking, key file classification, short text summaries, and truncation metadata.

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m pytest tests/unit/test_evidence_collector.py -q`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/schemas/scan.py src/harness_builder_agent/tools/evidence_collector.py tests/unit/test_evidence_collector.py
git commit -m "feat: add scan evidence collector"
```

---

### Task 2: DeepSeek Analyzer

**Files:**
- Create: `src/harness_builder_agent/tools/llm_config.py`
- Create: `src/harness_builder_agent/tools/deepseek_client.py`
- Create: `src/harness_builder_agent/tools/llm_scan_analyzer.py`
- Test: `tests/unit/test_llm_scan_analyzer.py`

- [ ] **Step 1: Write failing analyzer tests**

```python
import pytest

from harness_builder_agent.schemas.scan import EvidenceBundle
from harness_builder_agent.tools.llm_scan_analyzer import analyze_evidence_with_llm, parse_llm_scan_response


def _bundle() -> EvidenceBundle:
    return EvidenceBundle(repo_name="demo", root_path="/tmp/demo", files=[], key_files=[], config_files=[], ci_files=[], source_samples=[])


def test_parse_llm_scan_response_accepts_json_fence():
    text = """```json
{"primary_stack":"java-spring","stacks":["java","maven"],"modules":[{"name":"app","path":".","kind":"backend"}],"architecture_signals":[],"risk_areas":[],"command_candidates":[{"id":"unit_test","command":"mvn test","type":"test","gate":"hard","source":"pom.xml","confidence":"high"}],"configs":[],"ci_files":[],"confidence":"high","needs_human_confirmation":false,"reasoning_summary":"Maven project."}
```"""

    proposal = parse_llm_scan_response(text)

    assert proposal.primary_stack == "java-spring"
    assert proposal.command_candidates[0].command == "mvn test"


def test_parse_llm_scan_response_rejects_bad_json():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_llm_scan_response("not json")


def test_analyze_evidence_requires_caller_response():
    def caller(_messages):
        return ""

    with pytest.raises(ValueError, match="empty"):
        analyze_evidence_with_llm(_bundle(), caller=caller)
```

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m pytest tests/unit/test_llm_scan_analyzer.py -q`

Expected: fail because analyzer does not exist.

- [ ] **Step 3: Implement config, client, analyzer**

Implement `.env` loading, required `DEEPSEEK_API_KEY`, OpenAI-compatible request, prompt construction, fenced JSON extraction, strict `LLMScanProposal` validation.

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m pytest tests/unit/test_llm_scan_analyzer.py -q`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/llm_config.py src/harness_builder_agent/tools/deepseek_client.py src/harness_builder_agent/tools/llm_scan_analyzer.py tests/unit/test_llm_scan_analyzer.py
git commit -m "feat: add strict deepseek scan analyzer"
```

---

### Task 3: Reconciler

**Files:**
- Create: `src/harness_builder_agent/tools/scan_reconciler.py`
- Test: `tests/unit/test_scan_reconciler.py`

- [ ] **Step 1: Write failing reconciler tests**

```python
import pytest

from harness_builder_agent.schemas.scan import EvidenceBundle, EvidenceFile, LLMCommandCandidate, LLMScanProposal
from harness_builder_agent.tools.scan_reconciler import ScanConflictError, reconcile_scan


def _proposal(command_source="pom.xml", gate="hard"):
    return LLMScanProposal(
        primary_stack="java-spring",
        stacks=["java", "maven"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
        architecture_signals=[],
        risk_areas=[],
        command_candidates=[
            LLMCommandCandidate(id="unit_test", command="mvn test", type="test", gate=gate, source=command_source, confidence="high")
        ],
        configs=[],
        ci_files=[],
        confidence="high",
        needs_human_confirmation=False,
        reasoning_summary="Maven project.",
    )


def test_reconcile_keeps_hard_gate_when_command_has_evidence():
    evidence = EvidenceBundle(repo_name="demo", root_path="/tmp/demo", files=[], key_files=[EvidenceFile(path="pom.xml", kind="build", summary="maven")])

    inventory, commands, metadata = reconcile_scan(evidence, _proposal())

    assert inventory.primary_stack == "java-spring"
    assert commands.commands[0].gate == "hard"
    assert metadata.warnings == []


def test_reconcile_downgrades_hard_gate_without_evidence():
    evidence = EvidenceBundle(repo_name="demo", root_path="/tmp/demo", files=[], key_files=[])

    _inventory, commands, metadata = reconcile_scan(evidence, _proposal(command_source="missing-pom.xml"))

    assert commands.commands[0].gate == "soft"
    assert commands.commands[0].confidence == "low"
    assert any("without evidence" in warning.message for warning in metadata.warnings)


def test_reconcile_vetoes_impossible_dotnet_claim():
    evidence = EvidenceBundle(repo_name="demo", root_path="/tmp/demo", files=[EvidenceFile(path="pom.xml", kind="build")], key_files=[EvidenceFile(path="pom.xml", kind="build")])
    proposal = _proposal()
    proposal.primary_stack = "dotnet-aspnet"
    proposal.stacks = ["dotnet"]

    with pytest.raises(ScanConflictError):
        reconcile_scan(evidence, proposal)
```

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py -q`

Expected: fail because reconciler does not exist.

- [ ] **Step 3: Implement reconciler**

Map proposal fields to `ProjectInventory` and `CommandCatalog`; enforce hard-gate evidence support; create `ScanMetadata`.

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py -q`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/scan_reconciler.py tests/unit/test_scan_reconciler.py
git commit -m "feat: reconcile llm scan proposals"
```

---

### Task 4: Scan Facade and Init Assets

**Files:**
- Modify: `src/harness_builder_agent/tools/scan_repo.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`
- Modify: `tests/unit/test_scan_repo.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: Write failing facade/init tests**

Add tests asserting:

```python
def test_scan_repository_uses_llm_proposal_and_writes_metadata(tmp_path):
    # call scan_repository(fixture, llm_caller=fake_llm)
    # assert inventory.stack_extensions["scan_metadata"]["llm_status"] == "succeeded"
    # assert inventory.primary_stack came from fake LLM, not deterministic path guesses
```

and init integration tests monkeypatch `harness_builder_agent.cli.scan_repository` to return the LLM-first output.

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m pytest tests/unit/test_scan_repo.py tests/integration/test_init_on_fixture_projects.py -q`

Expected: fail because facade does not support `llm_caller` and assets do not write metadata/proposal.

- [ ] **Step 3: Implement facade and asset writes**

`scan_repository(repo, llm_caller=None)` collects evidence, calls analyzer, reconciles, stores metadata/proposal in `inventory.stack_extensions`, and `write_initial_assets()` writes:

- `.ai/scan-metadata.yaml`
- `.ai/llm-scan-proposal.json`

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m pytest tests/unit/test_scan_repo.py tests/integration/test_init_on_fixture_projects.py -q`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/scan_repo.py src/harness_builder_agent/tools/write_assets.py tests/unit/test_scan_repo.py tests/integration/test_init_on_fixture_projects.py
git commit -m "feat: route init through llm-first scan facade"
```

---

### Task 5: Benchmark Hard Gate

**Files:**
- Modify: `src/harness_builder_agent/tools/benchmark.py`
- Modify: `tests/integration/test_benchmark_command.py`

- [ ] **Step 1: Write failing benchmark tests**

Add one passing case with mocked sensor result `passed`, and one failing case where a hard gate sensor result is `skipped` or `failed`.

- [ ] **Step 2: Verify RED**

Run: `.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q`

Expected: fail because benchmark does not currently fail on hard gate sensor results.

- [ ] **Step 3: Implement benchmark hard gate check**

Read `.ai/task-runs/demo-task-001/sensor-report.yaml`; add check `content:hard-gate-sensors-passed`; fail if any result is not `passed`.

- [ ] **Step 4: Verify GREEN**

Run: `.venv/bin/python -m pytest tests/integration/test_benchmark_command.py -q`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/benchmark.py tests/integration/test_benchmark_command.py
git commit -m "feat: enforce hard gate sensors in benchmark"
```

---

### Task 6: Real DeepSeek Acceptance

**Files:**
- Delete: `tests/e2e/test_real_llm_smoke.py`
- Create: `tests/acceptance/test_real_llm_scan.py`
- Modify: `pyproject.toml`
- Modify: `README.md`

- [ ] **Step 1: Write acceptance test**

Create a test that loads local `.env`, calls `scan_repository()` with real DeepSeek, and fails when `DEEPSEEK_API_KEY` is missing.

- [ ] **Step 2: Update default pytest scope**

Set pytest `testpaths` to `["tests/unit", "tests/integration", "tests/e2e"]` so acceptance tests run only when explicitly requested.

- [ ] **Step 3: Run acceptance explicitly**

Run: `.venv/bin/python -m pytest tests/acceptance/test_real_llm_scan.py -q`

Expected locally: pass when `.env` has a valid DeepSeek key; fail loudly if not.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml README.md tests/acceptance/test_real_llm_scan.py tests/e2e/test_real_llm_smoke.py
git commit -m "test: replace llm smoke with real scan acceptance"
```

---

### Task 7: Full Verification

**Files:**
- No planned source edits.

- [ ] **Step 1: Run default suite**

Run: `.venv/bin/python -m pytest -q`

Expected: all unit/integration/e2e tests pass without real DeepSeek.

- [ ] **Step 2: Run acceptance suite**

Run: `.venv/bin/python -m pytest tests/acceptance/test_real_llm_scan.py -q`

Expected: pass locally with configured DeepSeek key.

- [ ] **Step 3: Run real repository E2E**

Run: `.venv/bin/python -m pytest tests/e2e/test_real_repositories_e2e.py -q`

Expected: pass only if local toolchains satisfy sensor gates; otherwise benchmark should fail honestly and the failure should be reviewed rather than masked.

- [ ] **Step 4: Push**

```bash
git push origin main
```
