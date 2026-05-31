# Guided Init Scan 返回修改差异预览实施计划

## 目标

让 final confirmation 阶段 `back -> scan` 的替换路径在 CLI 中明确展示“上一版补充 / 当前生效补充”，避免用户手动从长 transcript 中判断旧补充是否仍会影响最终 `.ai` 资产。

## 步骤

- [x] **Step 1: 写失败测试**
  - 修改 `tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_back_to_scan_replaces_previous_corrections`：
    - 断言输出包含 `扫描补充替换结果`。
    - 断言替换结果区块包含上一版 `legacy` module / command / risk / note。
    - 断言替换结果区块包含当前 `final` module / command / risk。
    - 断言替换结果说明最终写入只使用当前生效补充，上一版不进入正式资产。
  - 保留该测试既有资产替换断言。

- [x] **Step 2: 实现 CLI helper**
  - 修改 `src/harness_builder_agent/tools/interactive_init.py`：
    - 新增 `_show_scan_supplement_replacement_summary(previous, current)`。
    - 在 `back -> scan` 且新补充非空时，在 `_show_scan_supplement_immediate_summary()` 后调用该 helper。
    - 清空路径保持现状。

- [x] **Step 3: 同步工程文档与演进记录**
  - 修改 `docs/engineering/init-workflow.md`：
    - 在 scan 返回修改规则中补充 old/current 替换结果预览。
  - 修改 `docs/evolution-log.md`：
    - 追加本轮记录，包含 Gap Analysis 摘要、用户故事、取舍、验证和 Gate。

- [x] **Step 4: 验证**
  - 运行目标测试：
    - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_back_to_scan_replaces_previous_corrections tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_back_to_scan_can_clear_previous_corrections -q`
  - 运行 guided init integration：
    - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q`
  - 运行 `git diff --check`。
  - commit 前运行 `scripts/test-fast.sh`。

- [x] **Step 5: 本地提交**
  - 暂存本轮代码、测试、spec、plan 和文档。
  - 提交中文 commit：`展示扫描补充替换结果`。
  - 本轮不 push。

## 边界

- 不修改 schema。
- 不修改 LLM、scanner、writer、benchmark。
- 不改变正式 `.ai` 资产生成语义。
- 不执行 Runtime、不创建 `.ai/task-runs`。
