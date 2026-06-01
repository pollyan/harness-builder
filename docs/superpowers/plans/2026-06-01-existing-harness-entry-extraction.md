# Existing Harness 维护入口模块抽取计划

目标：把已有 Harness guided 维护入口从 `interactive_init.py` 抽到独立模块，保持用户行为不变，并用 unit / integration 验证拆分边界。

## 实施步骤

1. 写 RED 测试
   - 新增 `tests/unit/test_existing_harness_entry.py`。
   - import `harness_builder_agent.tools.existing_harness_entry`，验证模块和 `handle_existing_harness_entry()` / `load_existing_harness_state()` 存在。
   - 构造最小 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml`，验证 state load schema 成功。
   - 写损坏 `harness-config.yaml`，验证抛 `ExistingHarnessStateLoadError` 且 source 是 `.ai/harness-config.yaml`。
   - inspect `interactive_init.py`，断言不再定义 `def _handle_existing_harness_entry`，而是导入 alias。

2. 新增模块并搬迁
   - 新增 `src/harness_builder_agent/tools/existing_harness_entry.py`。
   - 搬迁 `ExistingHarnessStateLoadError`、已有 Harness state load、state load failure renderer、action prompt loop 和 `_handle_existing_harness_entry()` 主体。
   - 新模块调用已有 `existing_harness_signals`、`existing_harness_status`、`maintenance_triage` 和 `run_existing_harness_action()`。

3. 接入 `interactive_init.py`
   - 从新模块导入 `handle_existing_harness_entry as _handle_existing_harness_entry` 等兼容 alias。
   - 删除被搬迁的函数和不再需要的 import。
   - 保留首次 init scan / supplement / prewrite 状态机不变。

4. 验证
   - 运行新 unit test。
   - 运行 existing Harness action boundary / preview unit。
   - 运行 existing Harness integration 切片：exit、unknown action reprompt、invalid config、benchmark、recommend-workflow LLM failure、self-improve failure。
   - 运行 `tests/integration/test_init_on_fixture_projects.py`。
   - 运行 `compileall` 和 `git diff --check`。

5. 记录与提交
   - 更新 `docs/evolution-log.md`。
   - 提交前运行 `scripts/test-fast.sh`。
   - 创建中文本地 commit；不 push，除非 full regression 外部前置被允许并通过。

## 边界

- 不改用户可见文案。
- 不改 LLM、schema、writer、benchmark、Sensor 或 Runtime。
- 不拆 action runner 的内部动作分支。
- 不改变 `.ai` 产物。
