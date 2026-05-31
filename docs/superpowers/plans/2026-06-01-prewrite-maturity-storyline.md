# Prewrite Maturity Storyline 实施计划

目标：在首次 guided `init` 的写入前 preview 中补一段稳定的 L0-L4 成熟度叙事主线，说明当前等级、写入后基线、用户补充影响和未完成质量 / Runtime 边界。

## Steps

1. 红测：unit
   - 修改 `tests/unit/test_interactive_init_preview.py`。
   - 增加有 scan / team rules / workflow note 输入时的 storyline 输出断言。
   - 增加无用户补充时的 baseline storyline 输出断言。
   - 先运行目标 unit，确认缺少 `成熟度叙事主线` 导致失败。

2. 实现
   - 修改 `src/harness_builder_agent/tools/prewrite_preview.py`。
   - 新增 `_show_maturity_storyline()`，由 `show_prewrite_maturity_preview()` 在推荐补齐动作后调用。
   - helper 只消费已有 `planned`、`current_level`、`scan_overrides`、`inline_contexts` 和 `workflow_confirmation`，不改 maturity algorithm。

3. 目标验证
   - 运行新增 unit。
   - 运行完整 `tests/unit/test_interactive_init_preview.py`。
   - 运行相关 guided init integration，确认 prewrite preview 顺序和 transcript 关键断言仍通过。
   - 运行完整 `tests/integration/test_init_on_fixture_projects.py`。

4. 文档记录
   - 更新 `docs/evolution-log.md`，记录 Gap Analysis、用户故事、取舍、验证和 Gate 结论。
   - 本轮行为已在 README / init workflow 的既有描述范围内，不新增长期规则，除非实现过程中发现事实源冲突。

5. 最终验证与提交
   - `git diff --check`
   - `scripts/test-fast.sh`
   - 中文 commit message。
