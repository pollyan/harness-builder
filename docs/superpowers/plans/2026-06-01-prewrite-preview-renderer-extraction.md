# Prewrite Preview Renderer Extraction 实施计划

目标：把首次 guided `init` 的写入前预览渲染从 `interactive_init.py` 抽成独立模块，并补直接 unit 测试。

## Steps

1. 红测：unit
   - 修改 `tests/unit/test_interactive_init_preview.py`。
   - 从新模块导入 `GuidedScanOverrides`、`render_prewrite_maturity_preview` 或 helper。
   - 增加直接测试：有 scan 补充时 preview 输出 scan supplement section；无 scan 补充时输出扫描基线说明。
   - 先运行目标 unit，确认新模块不存在或 helper 不存在导致失败。

2. 实现抽取
   - 新增 `src/harness_builder_agent/tools/prewrite_preview.py`。
   - 移动 `GuidedScanOverrides` dataclass、`_show_prewrite_maturity_preview()`、scan supplement section、weapon maturity helpers 和 partial Harness 判断。
   - 将渲染函数命名为 `show_prewrite_maturity_preview()`，私有 helper 保留在新模块。
   - `interactive_init.py` 改为导入新模块函数和 dataclass；保留必要 helper re-export 以降低测试迁移成本。

3. 测试迁移 / 兼容
   - 将新 direct unit 放在 `test_interactive_init_preview.py` 或新 unit 文件。
   - 保持既有 helper 测试通过。
   - 运行目标 unit。

4. 集成验证
   - 运行目标 guided init integration。
   - 运行完整 `tests/integration/test_init_on_fixture_projects.py`，确保 transcript 不漂移。

5. 文档和记录
   - 更新 `docs/evolution-log.md`。
   - 如长期规则需要，更新 README / engineering；若只是模块边界收口，不新增用户文档。

6. 最终验证与提交
   - `git diff --check`
   - `scripts/test-fast.sh`
   - 中文 commit message。
