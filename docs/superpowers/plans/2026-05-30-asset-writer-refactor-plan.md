# Asset Writer Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `write_assets.py` into focused asset writer modules while preserving the existing `write_initial_assets` contract and generated `.ai` outputs.

**Architecture:** Keep `write_assets.py` as the orchestration entry point. Move concrete file writing and Markdown builders into `src/harness_builder_agent/tools/asset_writers/` modules, with shared write/artifact utilities.

**Tech Stack:** Python 3.11+, Pydantic, PyYAML, pytest.

---

## File Structure

Create:

- `src/harness_builder_agent/tools/asset_writers/__init__.py`
- `src/harness_builder_agent/tools/asset_writers/shared.py`
- `src/harness_builder_agent/tools/asset_writers/core.py`
- `src/harness_builder_agent/tools/asset_writers/human_confirmation.py`
- `src/harness_builder_agent/tools/asset_writers/reports.py`
- `src/harness_builder_agent/tools/asset_writers/guides.py`
- `src/harness_builder_agent/tools/asset_writers/sensors.py`
- `src/harness_builder_agent/tools/asset_writers/skills.py`
- `src/harness_builder_agent/tools/asset_writers/candidates.py`
- `tests/unit/test_asset_writer_core.py`
- `tests/unit/test_asset_writer_shared.py`
- `tests/unit/test_asset_writer_human_confirmation.py`
- `tests/unit/test_asset_writer_guides.py`
- `tests/unit/test_asset_writer_sensors.py`
- `tests/unit/test_asset_writer_reports.py`
- `tests/unit/test_asset_writer_candidates.py`
- `tests/unit/test_asset_writer_skills.py`

Modify:

- `src/harness_builder_agent/tools/write_assets.py`
- `tests/unit/test_write_assets.py`
- `docs/todos/asset-writer-refactor.md`

---

### Task 1: Shared Writer Utilities

**Files:**
- Create: `src/harness_builder_agent/tools/asset_writers/__init__.py`
- Create: `src/harness_builder_agent/tools/asset_writers/shared.py`
- Create: `tests/unit/test_asset_writer_shared.py`

- [ ] **Step 1: Write failing test for shared utilities**

Create `tests/unit/test_asset_writer_shared.py`:

```python
from pathlib import Path

import yaml

from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_json, write_text, write_yaml
from harness_builder_agent.tools.generation_trace import GenerationTrace


def test_shared_writers_create_parent_directories_and_preserve_unicode(tmp_path: Path):
    write_text(tmp_path / "nested" / "guide.md", "中文规则\n")
    write_json(tmp_path / "nested" / "payload.json", {"name": "中文"})
    write_yaml(tmp_path / "nested" / "payload.yaml", {"name": "中文"})

    assert (tmp_path / "nested" / "guide.md").read_text(encoding="utf-8") == "中文规则\n"
    assert '"中文"' in (tmp_path / "nested" / "payload.json").read_text(encoding="utf-8")
    assert yaml.safe_load((tmp_path / "nested" / "payload.yaml").read_text(encoding="utf-8")) == {"name": "中文"}


def test_record_artifact_is_noop_without_trace_and_records_relative_path(tmp_path: Path):
    record_artifact(None, tmp_path / ".ai" / "guide.md", "guide")
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    record_artifact(trace, tmp_path / ".ai" / "guide.md", "guide")
    trace.finish("completed", {})

    artifacts = yaml.safe_load((tmp_path / ".ai" / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert artifacts["artifacts"] == [{"path": ".ai/guide.md", "kind": "guide"}]
```

- [ ] **Step 2: Verify test fails**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_shared.py -q
```

Expected: fail because `asset_writers.shared` does not exist.

- [ ] **Step 3: Write shared utility module**

Create `src/harness_builder_agent/tools/asset_writers/__init__.py`:

```python
"""Focused writers for initial Harness Builder assets."""
```

Create `src/harness_builder_agent/tools/asset_writers/shared.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.tools.generation_trace import GenerationTrace


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def record_artifact(trace: GenerationTrace | None, path: Path, kind: str) -> None:
    if trace:
        trace.artifact(path, kind)
```

- [ ] **Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_shared.py -q
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/asset_writers/__init__.py src/harness_builder_agent/tools/asset_writers/shared.py tests/unit/test_asset_writer_shared.py
git commit -m "refactor: add asset writer shared utilities"
```

---

### Task 2: Core Asset Writer

**Files:**
- Create: `src/harness_builder_agent/tools/asset_writers/core.py`
- Create: `tests/unit/test_asset_writer_core.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`

- [ ] **Step 1: Write failing test for core assets**

Create `tests/unit/test_asset_writer_core.py`:

```python
from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.core import llm_scan_proposal, scan_metadata, write_core_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace


def _inventory(root: Path) -> ProjectInventory:
    return ProjectInventory(
        repo_name="demo",
        root_path=str(root),
        primary_stack="java-spring",
        stacks=["java", "maven"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
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
                "stacks": ["java"],
                "modules": [],
                "architecture_signals": [],
                "risk_areas": [],
                "command_candidates": [],
                "configs": [],
                "ci_files": [],
                "confidence": "high",
                "needs_human_confirmation": False,
                "reasoning_summary": "test",
            },
        },
    )


def test_write_core_assets_writes_schema_files_and_artifacts(tmp_path: Path):
    ai = tmp_path / ".ai"
    inventory = _inventory(tmp_path)
    commands = CommandCatalog(commands=[CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml")])
    config = HarnessConfig.default()
    selection = WeaponLibrarySelection(primary_stack="java-spring", selected_stacks=["common", "java-spring"])
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    write_core_assets(ai, inventory, commands, config, scan_metadata(inventory), llm_scan_proposal(inventory), selection, trace)
    trace.finish("completed", {})

    assert (ai / "project-inventory.json").exists()
    assert (ai / "command-catalog.yaml").exists()
    assert (ai / "harness-config.yaml").exists()
    assert (ai / "scan-metadata.yaml").exists()
    assert (ai / "llm-scan-proposal.json").exists()
    assert (ai / "weapon-library-selection.yaml").exists()
    metadata = yaml.safe_load((ai / "scan-metadata.yaml").read_text(encoding="utf-8"))
    assert metadata["llm_status"] == "succeeded"
    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert ".ai/project-inventory.json" in {item["path"] for item in artifacts["artifacts"]}
```

- [ ] **Step 2: Verify test fails**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_core.py -q
```

Expected: fail because `asset_writers.core` does not exist.

- [ ] **Step 3: Implement core writer**

Create `src/harness_builder_agent/tools/asset_writers/core.py` by moving `_scan_metadata`, `_llm_scan_proposal`, and core file writes from `write_assets.py`.

Expose:

```python
def scan_metadata(inventory: ProjectInventory) -> dict[str, Any]: ...
def llm_scan_proposal(inventory: ProjectInventory) -> dict[str, Any]: ...
def write_core_assets(ai: Path, inventory: ProjectInventory, commands: CommandCatalog, config: HarnessConfig, scan_metadata_payload: dict[str, Any], llm_scan_proposal_payload: dict[str, Any], weapon_selection: WeaponLibrarySelection, trace: GenerationTrace | None = None) -> None: ...
```

- [ ] **Step 4: Update `write_assets.py` to call core writer**

Import:

```python
from harness_builder_agent.tools.asset_writers.core import llm_scan_proposal, scan_metadata, write_core_assets
```

Replace the core write block with:

```python
scan_metadata_payload = scan_metadata(inventory)
llm_scan_proposal_payload = llm_scan_proposal(inventory)
write_core_assets(ai, inventory, commands, config, scan_metadata_payload, llm_scan_proposal_payload, weapon_selection, trace)
```

Pass `scan_metadata_payload` to `build_questionnaire`.

- [ ] **Step 5: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_core.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py -q
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add src/harness_builder_agent/tools/asset_writers/core.py src/harness_builder_agent/tools/write_assets.py tests/unit/test_asset_writer_core.py
git commit -m "refactor: split core asset writer"
```

---

### Task 3: Human Confirmation Writer

**Files:**
- Create: `src/harness_builder_agent/tools/asset_writers/human_confirmation.py`
- Create: `tests/unit/test_asset_writer_human_confirmation.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`

- [ ] **Step 1: Write failing test for human confirmation assets**

Create `tests/unit/test_asset_writer_human_confirmation.py`:

```python
from pathlib import Path

import yaml

from harness_builder_agent.tools.asset_writers.human_confirmation import write_human_confirmation_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace


def test_write_human_confirmation_assets_writes_context_questionnaire_and_markdown(tmp_path: Path):
    ai = tmp_path / ".ai"
    context_inputs = {"contexts": [{"path": "team-rules.md", "content": "团队规则：必须分层。"}]}
    questionnaire = {"questions": [{"id": "architecture", "question": "架构是否分层？", "reason": "扫描需要确认"}]}
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    write_human_confirmation_assets(ai, context_inputs, questionnaire, trace)
    trace.finish("completed", {})

    assert yaml.safe_load((ai / "context-inputs.yaml").read_text(encoding="utf-8")) == context_inputs
    assert yaml.safe_load((ai / "questionnaire.yaml").read_text(encoding="utf-8")) == questionnaire
    markdown = (ai / "human-input-needed.md").read_text(encoding="utf-8")
    assert "团队规则" in markdown
    assert "架构是否分层" in markdown
    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert ".ai/human-input-needed.md" in {item["path"] for item in artifacts["artifacts"]}
```

- [ ] **Step 2: Verify test fails**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_human_confirmation.py -q
```

Expected: fail because `asset_writers.human_confirmation` does not exist.

- [ ] **Step 3: Implement writer**

Create:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text, write_yaml
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.human_confirmation import human_input_markdown


def write_human_confirmation_assets(
    ai: Path,
    context_inputs: dict[str, Any],
    questionnaire: dict[str, Any],
    trace: GenerationTrace | None = None,
) -> None:
    write_yaml(ai / "context-inputs.yaml", context_inputs)
    record_artifact(trace, ai / "context-inputs.yaml", "context_inputs")
    write_yaml(ai / "questionnaire.yaml", questionnaire)
    record_artifact(trace, ai / "questionnaire.yaml", "questionnaire")
    write_text(ai / "human-input-needed.md", human_input_markdown(context_inputs, questionnaire))
    record_artifact(trace, ai / "human-input-needed.md", "human_confirmation")
```

- [ ] **Step 4: Update orchestration**

Replace human confirmation writes in `write_assets.py` with `write_human_confirmation_assets(...)`.

- [ ] **Step 5: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_human_confirmation.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py -q
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add src/harness_builder_agent/tools/asset_writers/human_confirmation.py src/harness_builder_agent/tools/write_assets.py tests/unit/test_asset_writer_human_confirmation.py
git commit -m "refactor: split human confirmation writer"
```

---

### Task 4: Reports Writer

**Files:**
- Create: `src/harness_builder_agent/tools/asset_writers/reports.py`
- Create: `tests/unit/test_asset_writer_reports.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`

- [ ] **Step 1: Add failing report writer test**

Create `tests/unit/test_asset_writer_reports.py` first, before `reports.py` exists.

Expected failure command:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_reports.py -q
```

Expected: fail because `asset_writers.reports` does not exist.

- [ ] **Step 2: Move report builders**

Create `reports.py` with:

- `write_report_assets`
- `_scan_report`
- `_maturity_report`
- `_maturity_score`
- `_evolution_plan`

Move implementations unchanged from `write_assets.py`.

- [ ] **Step 3: Complete report writer test**

Create a test that writes reports and asserts:

```python
assert (ai / "scan-report.md").exists()
assert (ai / "maturity-report.md").exists()
assert (ai / "maturity-score.yaml").exists()
assert (ai / "evolution-plan.md").exists()
assert "## 证据" in (ai / "maturity-report.md").read_text(encoding="utf-8")
assert yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8"))["schema_version"] == "1.0"
```

- [ ] **Step 4: Update orchestration and run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_reports.py tests/unit/test_write_assets.py -q
scripts/test-fast.sh
```

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/asset_writers/reports.py src/harness_builder_agent/tools/write_assets.py tests/unit/test_asset_writer_reports.py
git commit -m "refactor: split report asset writer"
```

---

### Task 5: Guides Writer

**Files:**
- Create: `src/harness_builder_agent/tools/asset_writers/guides.py`
- Create: `tests/unit/test_asset_writer_guides.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`

- [ ] **Step 1: Add failing guide writer test**

Create `tests/unit/test_asset_writer_guides.py` first, before `guides.py` exists.

Expected failure command:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_guides.py -q
```

Expected: fail because `asset_writers.guides` does not exist.

- [ ] **Step 2: Move guide builders**

Create `guides.py` with:

- `write_guide_assets`
- `_frontmatter`
- `_guide`
- `_task_template`
- `_weapon_match_lines`
- `_guide_rule_lines`

Move implementations unchanged.

- [ ] **Step 3: Complete guide writer test**

Test should assert:

```python
assert "## 当前项目事实" in project_context
assert "## 来源证据" in project_context
assert "java-spring.guide." in project_context
assert "缺陷修复任务模板" in bugfix_template
assert "轻量级任务模板" in lightweight_template
```

- [ ] **Step 4: Update orchestration and run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_guides.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py -q
scripts/test-fast.sh
```

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/asset_writers/guides.py src/harness_builder_agent/tools/write_assets.py tests/unit/test_asset_writer_guides.py
git commit -m "refactor: split guide asset writer"
```

---

### Task 6: Sensors Writer

**Files:**
- Create: `src/harness_builder_agent/tools/asset_writers/sensors.py`
- Create: `tests/unit/test_asset_writer_sensors.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`

- [ ] **Step 1: Add failing sensor writer test**

Create `tests/unit/test_asset_writer_sensors.py` first, before `sensors.py` exists.

Expected failure command:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_sensors.py -q
```

Expected: fail because `asset_writers.sensors` does not exist.

- [ ] **Step 2: Move sensor builders**

Create `sensors.py` with:

- `write_sensor_assets`
- `_sensor_doc`
- `_test_strategy`
- `_missing_sensor_lines`
- `_weapon_match_lines`

Move implementations unchanged.

- [ ] **Step 3: Complete sensor writer test**

Test should assert:

```python
assert "## 已发现的验证命令" in verification
assert "## 缺失验证能力" in verification
assert "## 推荐验证活动" in verification
assert "## 失败处理策略" in verification
assert "mvn test" in test_strategy
```

- [ ] **Step 4: Update orchestration and run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_sensors.py tests/unit/test_write_assets.py tests/integration/test_benchmark_command.py -q
scripts/test-fast.sh
```

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/asset_writers/sensors.py src/harness_builder_agent/tools/write_assets.py tests/unit/test_asset_writer_sensors.py
git commit -m "refactor: split sensor asset writer"
```

---

### Task 7: Skills and Candidates Writers

**Files:**
- Create: `src/harness_builder_agent/tools/asset_writers/skills.py`
- Create: `src/harness_builder_agent/tools/asset_writers/candidates.py`
- Create: `tests/unit/test_asset_writer_skills.py`
- Create: `tests/unit/test_asset_writer_candidates.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`

- [ ] **Step 1: Add failing skills and candidates writer tests**

Create `tests/unit/test_asset_writer_skills.py` and `tests/unit/test_asset_writer_candidates.py` first.

Expected failure command:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_skills.py tests/unit/test_asset_writer_candidates.py -q
```

Expected: fail because `asset_writers.skills` and `asset_writers.candidates` do not exist.

- [ ] **Step 2: Move skill copy**

Create `skills.py` with:

- `write_skill_assets`

Move `_copy_workflow_skills` logic unchanged.

- [ ] **Step 3: Move candidate asset writes**

Create `candidates.py` with:

- `write_candidate_assets`

Move pending improvements, weapon library candidates, and review markdown writes.

- [ ] **Step 4: Complete tests**

Skills test asserts:

```python
assert (ai / "skills" / "lightweight" / "SKILL.md").exists()
assert (ai / "skills" / "bugfix" / "SKILL.md").exists()
```

Candidates test asserts:

```python
assert (ai / "experience" / "weapon-library-candidates.yaml").exists()
assert (ai / "review" / "llm-enhancement-candidates.md").exists()
assert all(item["human_confirmation_required"] is True for item in report["candidates"])
```

- [ ] **Step 5: Update orchestration and run tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_skills.py tests/unit/test_asset_writer_candidates.py tests/unit/test_write_assets.py -q
scripts/test-fast.sh
```

- [ ] **Step 6: Commit**

```bash
git add src/harness_builder_agent/tools/asset_writers/skills.py src/harness_builder_agent/tools/asset_writers/candidates.py src/harness_builder_agent/tools/write_assets.py tests/unit/test_asset_writer_skills.py tests/unit/test_asset_writer_candidates.py
git commit -m "refactor: split skill and candidate writers"
```

---

### Task 8: Cleanup `write_assets.py` and Mark Todo Implemented

**Files:**
- Modify: `src/harness_builder_agent/tools/write_assets.py`
- Modify: `docs/todos/asset-writer-refactor.md`

- [ ] **Step 1: Remove moved helpers**

Remove from `write_assets.py`:

- `_write_text`
- `_write_json`
- `_write_yaml`
- `_record_artifact`
- `_scan_report`
- `_scan_metadata`
- `_llm_scan_proposal`
- `_maturity_report`
- `_maturity_score`
- `_evolution_plan`
- `_guide`
- `_task_template`
- `_sensor_doc`
- `_test_strategy`
- `_copy_workflow_skills`
- `_weapon_match_lines`
- `_guide_rule_lines`
- `_missing_sensor_lines`

Keep `write_initial_assets` as orchestration.

- [ ] **Step 2: Run targeted and full tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_write_assets.py tests/unit/test_asset_writer_core.py tests/unit/test_asset_writer_guides.py tests/unit/test_asset_writer_sensors.py tests/unit/test_asset_writer_reports.py tests/unit/test_asset_writer_candidates.py tests/unit/test_asset_writer_skills.py -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py tests/e2e/test_fixture_end_to_end.py -q
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 3: Update todo**

Change status:

```markdown
- 状态：implemented
```

Add:

```markdown
## 实现结果

- 已将 core、human confirmation、reports、guides、sensors、skills、candidates 拆分到 `asset_writers/`。
- `write_initial_assets` 保持对外兼容，只负责高层编排。
- 已补充各 writer 的单元测试，并保留整体行为基线测试。
```

- [ ] **Step 4: Commit**

```bash
git add src/harness_builder_agent/tools/write_assets.py docs/todos/asset-writer-refactor.md
git commit -m "docs: mark asset writer refactor implemented"
```
