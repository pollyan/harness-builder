# Guided Init 用户补充复述与影响说明实施计划

## 目标

让首次 guided `init` 在写入前复述用户补充，并说明补充如何影响 Guides、Sensors、成熟度预览和 Workflow 说明。

## 文件职责

- `tests/integration/test_init_on_fixture_projects.py`：新增 guided transcript 集成测试，锁定最终确认摘要和落盘资产。
- `src/harness_builder_agent/tools/interactive_init.py`：新增用户补充影响摘要 helper，并在最终确认前输出。
- `docs/engineering/init-workflow.md`：固化 guided init 必须复述用户补充及影响说明。
- `docs/evolution-log.md`：记录本轮 gap、用户故事、取舍、验收和 Gate 结论。

## 实施步骤

1. 写失败测试。
   - 新增 `test_guided_init_restates_user_supplements_before_write_and_persists_them`。
   - 输入包含 scan note、团队规则、workflow note。
   - 断言 `最终确认` 之后包含“已吸收的用户补充”“补充影响”“批处理入口”“Controller 只能调用 Service”“bugfix 工作流适合缺陷修复”。
   - 断言落盘 decisions、project-context 和 human-input-needed 保留这些补充。

2. 实现补充影响摘要。
   - 在 `interactive_init.py` 中新增 `_supplement_summary_lines()` 和 `_show_supplement_impact_summary()`。
   - 在 `_confirm_summary()` 中输出具体补充内容和影响面。
   - 对 scan note、team context、workflow note 分别说明影响。

3. 保持既有结构化补充行为。
   - 不改变 `_apply_scan_overrides()` 的 inventory / commands / risk 写入逻辑。
   - 运行现有结构化补充测试确认未回退。

4. 更新长期文档和演进记录。
   - `docs/engineering/init-workflow.md` 增加“用户补充复述与影响说明”规则。
   - `docs/evolution-log.md` 新增本轮记录。

5. 验证。
   - 运行新增 integration 测试。
   - 运行相关 guided init integration。
   - 运行 `scripts/test-fast.sh` 后提交。
