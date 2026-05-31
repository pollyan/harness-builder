# Existing Harness 维护入口分组标题中文化实施计划

## 目标

把已有 Harness 维护入口的主要分组标题改成中文优先、英文稳定 marker 括注的形式，降低 Maintainer 首次扫读维护入口时的理解成本。

## 实施步骤

1. TDD：先修改 existing Harness 只读 exit integration test，断言以下中文标题存在：
   - `质量门禁信号（Benchmark signals）`
   - `Workflow 路由信号（Workflow routing signals）`
   - `经验 / 审查信号（Experience / review signals）`
   - `维护优先级（Maintenance triage）`
   - `维护建议（Maintenance triage guidance）`
   - `推荐动作快捷选择（Maintenance action shortcuts）`
2. 运行 targeted integration，确认当前失败。
3. 修改 `src/harness_builder_agent/tools/interactive_init.py` 中 existing Harness 维护入口的 section headers。
4. 运行 targeted integration，确认输出和资产不变断言通过。
5. 更新 `docs/evolution-log.md`，记录 Gap Analysis、用户故事、取舍、sub agent 限制、验证和 Gate。
6. 运行 `git diff --check` 和 `scripts/test-fast.sh`。
7. 本地中文 commit；不 push，除非形成完整工作包并通过 full regression。

## 验证命令

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_without_overwriting_assets -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_existing_harness_can_exit_with_numbered_action -q
git diff --check
scripts/test-fast.sh
```

## 非目标

- 不翻译每一条 key=value 机器信号。
- 不改变 Maintenance triage 排序或 action shortcuts。
- 不改变 existing Harness 动作执行语义。
- 不修改 schema、benchmark、LLM、Runtime 边界。
