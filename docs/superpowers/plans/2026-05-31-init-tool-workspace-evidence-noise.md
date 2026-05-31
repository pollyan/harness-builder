# Init 工具工作区 Evidence 降噪 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `init` evidence 收集忽略 `.claude` / `.opencode` 工具工作区，并把 Python 项目文件纳入关键 evidence。

**Architecture:** 在 `evidence_collector.py` 的目录过滤和 key file 判定层做窄改动，不改变 scan schema、LLM prompt、primary stack 枚举或 reconciler。Unit test 直接验证 `collect_evidence()` 输出，避免需要真实 LLM。

**Tech Stack:** Python、Pydantic schema、pytest。

---

### Task 1: 固定工具工作区 evidence 降噪行为

**Files:**
- Modify: `tests/unit/test_evidence_collector.py`
- Modify: `src/harness_builder_agent/tools/evidence_collector.py`
- Modify: `docs/evolution-log.md`
- Modify: `docs/todos/guided-init-ai4se-real-repo-findings.md`

- [ ] **Step 1: Write the failing unit test**

在 `tests/unit/test_evidence_collector.py` 中新增：

```python
def test_collect_evidence_ignores_ai_tool_workspaces_and_keeps_root_project_manifests(tmp_path: Path):
    _write(tmp_path / "package.json", '{"scripts":{"test":"npm test"}}')
    _write(tmp_path / "pyproject.toml", "[project]\nname='demo'\n")
    _write(tmp_path / "requirements.txt", "flask\n")
    _write(tmp_path / ".claude" / "worktrees" / "feature" / "package.json", '{"private":true}')
    _write(tmp_path / ".opencode" / "package.json", '{"private":true}')
    _write(tmp_path / "deploy-package" / ".opencode" / "package.json", '{"private":true}')

    bundle = collect_evidence(tmp_path)

    indexed_paths = {item.path for item in bundle.files}
    key_paths = {item.path for item in bundle.key_files}
    priority_paths = {item.path for item in bundle.priority_files}

    assert "package.json" in indexed_paths
    assert "pyproject.toml" in indexed_paths
    assert "requirements.txt" in indexed_paths
    assert ".claude/worktrees/feature/package.json" not in indexed_paths
    assert ".opencode/package.json" not in indexed_paths
    assert "deploy-package/.opencode/package.json" not in indexed_paths

    assert {"package.json", "pyproject.toml", "requirements.txt"}.issubset(key_paths)
    assert {"package.json", "pyproject.toml", "requirements.txt"}.issubset(priority_paths)
    assert all(not path.startswith(".claude/") for path in key_paths)
    assert all("/.opencode/" not in f"/{path}" for path in key_paths)
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_evidence_collector.py::test_collect_evidence_ignores_ai_tool_workspaces_and_keeps_root_project_manifests -q
```

Expected: fails because `.claude` / `.opencode` paths are indexed and Python project files are not all key files.

- [ ] **Step 3: Implement minimal evidence hygiene**

在 `src/harness_builder_agent/tools/evidence_collector.py` 中：

```python
IGNORED_DIRS = {
    ".git",
    ".ai",
    ".venv",
    ".claude",
    ".opencode",
    "node_modules",
    "target",
    "bin",
    "obj",
    "dist",
    "build",
    "__pycache__",
}

KEY_FILE_NAMES = {
    "pom.xml",
    "package.json",
    "global.json",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "poetry.lock",
}
```

不修改 `_bucket_for()` 的判定顺序；目录过滤已经确保工具 workspaces 不会进入 key file 判定。

- [ ] **Step 4: Run targeted test to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_evidence_collector.py::test_collect_evidence_ignores_ai_tool_workspaces_and_keeps_root_project_manifests -q
```

Expected: passes.

- [ ] **Step 5: Run evidence collector unit slice**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_evidence_collector.py -q
```

Expected: all evidence collector tests pass.

- [ ] **Step 6: Update stable docs**

在 `docs/evolution-log.md` 顶部新增本轮记录，说明：

- 关联 todo：`guided-init-ai4se-real-repo-findings.md`
- North Star 模块：CLI Experience、深度扫描、可解释 evidence。
- 用户故事、当前 gap、关键决策、非目标、验收方式、验证结果和下一轮候选 gap。

在 `docs/todos/guided-init-ai4se-real-repo-findings.md` 的状态区新增“已完成切片”，说明工具工作区 evidence 降噪已完成，剩余 skipped 中文化、多栈建模、高风险突出仍 open。

- [ ] **Step 7: Run required fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: fast regression passes before commit.
