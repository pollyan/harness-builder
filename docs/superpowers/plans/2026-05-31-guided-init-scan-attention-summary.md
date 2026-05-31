# Guided Init 扫描关注点分组 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让首次 guided `init` 在扫描结果对齐前展示风险、不确定性、验证缺口和建议补充，帮助用户判断该修正哪里。

**Architecture:** 在 `interactive_init.py` 的 CLI 渲染层消费现有 `ProjectInventory.stack_extensions` 与 `CommandCatalog`，不改 scan schema、LLM prompt、写入契约或非交互路径。测试放在现有 guided init integration 文件中，用 fake scan 数据覆盖关注点摘要。

**Tech Stack:** Python、Typer、pytest、Typer `CliRunner`、Pydantic schemas。

---

### Task 1: 写 RED 测试

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: 扩展 happy path 基础分组断言**

在 `test_init_default_guided_mode_accepts_happy_path` 中增加：

```python
    assert "风险区域" in result.output
    assert "不确定性" in result.output
    assert "验证缺口" in result.output
    assert "建议补充" in result.output
    assert result.output.index("扫描发现") < result.output.index("风险区域")
    assert result.output.index("建议补充") < result.output.index("团队规则")
```

- [ ] **Step 2: 新增低置信度/缺口场景测试**

新增测试：

```python
def test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)

    def scan_with_attention_points(repo_path: Path):
        inventory = ProjectInventory(
            repo_name=repo_path.name,
            root_path=str(repo_path),
            primary_stack="java-spring",
            stacks=["java", "spring-boot"],
            modules=[{"name": "app", "path": ".", "kind": "backend"}],
            evidence=[{"path": "pom.xml", "reason": "build config"}],
            stack_extensions={
                "risk_areas": [{"path": "src/main/resources/application.yml", "reason": "配置变更影响运行环境"}],
                "needs_human_confirmation": True,
                "scan_warnings": [
                    {
                        "code": "test_evidence_not_found",
                        "message": "No dedicated test evidence bucket was found; test strategy needs human confirmation.",
                        "severity": "warning",
                        "evidence": [],
                    }
                ],
                "llm_scan_proposal": {"confidence": "low"},
            },
        )
        commands = CommandCatalog(
            commands=[
                {
                    "id": "integration_test",
                    "command": "mvn -Pintegration test",
                    "type": "test",
                    "gate": "soft",
                    "source": "pom.xml",
                    "confidence": "low",
                }
            ]
        )
        return inventory, commands

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", scan_with_attention_points)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="\n\n\n\n\n\n\nconfirm\n")

    assert result.exit_code == 0, result.output
    assert "风险区域" in result.output
    assert "src/main/resources/application.yml" in result.output
    assert "配置变更影响运行环境" in result.output
    assert "不确定性" in result.output
    assert "需要人工确认" in result.output
    assert "LLM 扫描置信度为 low" in result.output
    assert "No dedicated test evidence bucket was found" in result.output
    assert "mvn -Pintegration test" in result.output
    assert "验证缺口" in result.output
    assert "暂未确认 hard gate" in result.output
    assert "低置信度验证命令" in result.output
    assert "建议补充" in result.output
    assert "真实可执行的 hard gate 命令" in result.output
    assert result.output.index("风险区域") < result.output.index("团队规则")
```

- [ ] **Step 3: 运行 RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path tests/integration/test_init_on_fixture_projects.py::test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps -q
```

Expected: 失败，因为当前没有关注点分组。

### Task 2: 实现扫描关注点摘要

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [ ] **Step 1: 在 `_show_scan_findings()` 末尾调用摘要**

在验证命令展示后加入：

```python
    _show_scan_attention_summary(inventory, commands)
```

- [ ] **Step 2: 新增摘要渲染函数**

新增以下函数，放在 `_show_scan_findings()` 后：

```python
def _show_scan_attention_summary(inventory: ProjectInventory, commands: CommandCatalog) -> None:
    typer.echo("\n风险区域")
    for line in _risk_attention_lines(inventory):
        typer.echo(f"- {line}")
    typer.echo("\n不确定性")
    for line in _uncertainty_attention_lines(inventory, commands):
        typer.echo(f"- {line}")
    typer.echo("\n验证缺口")
    for line in _verification_gap_lines(commands):
        typer.echo(f"- {line}")
    typer.echo("\n建议补充")
    for line in _human_followup_lines(inventory, commands):
        typer.echo(f"- {line}")
```

- [ ] **Step 3: 新增推导 helper**

按 spec 实现 `_risk_attention_lines()`、`_uncertainty_attention_lines()`、`_verification_gap_lines()`、`_human_followup_lines()`。只读访问 `stack_extensions`，对缺失字段返回空列表或正向说明；不要抛出 KeyError。

### Task 3: 更新文档与演进记录

**Files:**
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/evolution-log.md`

- [ ] **Step 1: 更新 init workflow**

在 Scan reconcile 或写入前成熟度预览之前补充 guided 扫描结果展示规则：扫描发现必须分组展示风险区域、不确定性、验证缺口和建议补充，且这些内容发生在收集用户扫描补充之前。

- [ ] **Step 2: 更新 evolution log**

在顶部新增 `2026-05-31 Guided Init 扫描关注点分组`，记录 gap、用户故事、决策、sub agent 使用、验收结果和下一轮候选 gap。

### Task 4: 验证并提交

**Files:** all changed files.

- [ ] **Step 1: 运行 targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path tests/integration/test_init_on_fixture_projects.py::test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps -q
```

Expected: `2 passed`.

- [ ] **Step 2: 运行 guided init integration**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
```

Expected: all tests passed.

- [ ] **Step 3: commit 前快速回归**

Run:

```bash
scripts/test-fast.sh
```

Expected: all tests passed.

- [ ] **Step 4: commit、full regression、push**

Run:

```bash
git add src/harness_builder_agent/tools/interactive_init.py tests/integration/test_init_on_fixture_projects.py docs/engineering/init-workflow.md docs/evolution-log.md docs/superpowers/specs/2026-05-31-guided-init-scan-attention-summary-design.md docs/superpowers/plans/2026-05-31-guided-init-scan-attention-summary.md
git commit -m "增加guided-init扫描关注点分组"
scripts/test-full.sh
git push --no-verify origin main
```

Expected: push 前 full regression 通过后推送。
