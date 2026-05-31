# Scan Supplement Prewrite Preview 实施计划

目标：让首次 guided `init` 的写入前 Harness 设计预览明确展示当前 scan 补充及其设计影响。

## Steps

1. 红测：integration
   - 修改 `tests/integration/test_init_on_fixture_projects.py`。
   - 在已有 scan 补充场景中断言 `写入前 Harness 设计预览` 包含 `扫描补充约束`、结构化模块、验证命令、风险区域、影响说明和“不伪装成已验证扫描事实”边界。
   - 在返回 scan 替换场景中断言最终 preview 只展示当前生效补充，不展示上一版补充。

2. 实现
   - 修改 `src/harness_builder_agent/tools/interactive_init.py`。
   - 将 `scan_overrides` 传入 `_show_prewrite_maturity_preview()`。
   - 新增 `_show_scan_supplement_preview_section()` 或等价 helper。
   - 当无 scan 补充时展示扫描基线说明；有补充时展示 stack / notes / modules / commands / risk_areas 和影响边界。

3. 文档
   - 更新 `README.md` 的 guided `init` 说明，明确写入前预览展示 scan 补充约束。
   - 更新 `docs/engineering/init-workflow.md` 的写入前预览规则。
   - 更新 `docs/evolution-log.md`。

4. 验证
   - 目标 integration。
   - 完整 guided init integration。
   - `git diff --check`。
   - `scripts/test-fast.sh`。

5. 提交
   - 中文 commit message。
   - 本轮不 push；push 仍需完整工作包和 full regression。
