# Guided 团队规则输入引导增强实施计划

## 目标

把首次 guided `init` 的团队规则输入从一段宽泛例子增强为分组提示，并抽到独立模块，保持后续 interaction decisions、Guides、human-input-needed 和 completion summary 行为不变。

## 步骤

1. TDD：新增 `tests/unit/test_guided_team_rules.py`
   - 先导入不存在的 `guided_team_rules`，确认 RED。
   - 覆盖分组提示输出。
   - 覆盖有输入返回单条规则。
   - 覆盖空输入返回空列表。
2. 更新 guided init integration
   - 在 `test_guided_init_records_scan_notes_and_team_rules_in_assets` 中断言分组提示出现在 prompt 前、团队规则理解前。
   - 继续断言原 `context_confirmation` 行为不变。
3. 实现 `src/harness_builder_agent/tools/guided_team_rules.py`
   - 新增 `collect_team_rules(prompt=typer.prompt)`。
   - 输出分组提示并复用原 prompt 文案。
4. 更新 `interactive_init.py`
   - 导入 `collect_team_rules as _collect_team_rules`。
   - 删除内联 `_collect_team_rules()` 实现。
5. 验证
   - `.venv/bin/python -m pytest tests/unit/test_guided_team_rules.py -q`
   - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_records_scan_notes_and_team_rules_in_assets -q`
   - `.venv/bin/python -m compileall src/harness_builder_agent/tools/interactive_init.py src/harness_builder_agent/tools/guided_team_rules.py`
   - `git diff --check`
   - `scripts/test-fast.sh`
6. 更新 `docs/evolution-log.md`
   - 记录 Gap Analysis 摘要、用户故事、取舍、验证结果和 Self-Harness Gate。
7. 本地 commit
   - commit message：`增强 guided 团队规则输入引导`
   - 本轮不 push；push 仍以 full regression 通过和完整工作包为边界。

## 非目标

- 不修改 `ContextConfirmation` schema。
- 不把团队规则拆成多个机器字段。
- 不修改 asset writer、benchmark、LLM 或 Runtime 分工。
- 不改变已有团队规则输入如何进入 Guides、human-input-needed、interaction decisions 或 completion summary。
