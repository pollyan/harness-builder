# Guided Init 不完整 Harness 启动边界计划

## 用户故事

作为 Harness Maintainer，当我对一个已有不完整 `.ai` core 文件的仓库运行默认 guided `init` 时，我可以在第一次确认继续前看到哪些核心 Harness 文件已存在、哪些缺失、为什么不会进入已有 Harness 维护入口，以及继续后仍不会在最终确认前覆盖正式资产，从而能决定是继续扫描还是先取消备份。

## 步骤

1. 增加失败测试
   - 在 guided init integration 中构造只有 `.ai/harness-config.yaml` 的 partial core 状态。
   - mock `scan_repository` 为失败函数，输入 `n` 取消。
   - 断言 RED：启动说明中缺少 partial core present / missing 和维护入口边界说明。

2. 实现启动说明
   - `_show_guided_init_startup_boundary(repo)` 接收 repo。
   - 增加 partial core 检测和格式化 helper。
   - 仅当 inventory/config 不是同时存在且至少一个 core 文件存在时展示提示。
   - 保持完整已有 Harness 仍由 `_handle_existing_harness_entry()` 拦截进入维护入口。

3. 更新长期文档与演进记录
   - 在 `docs/engineering/init-workflow.md` 记录 partial core 启动边界。
   - 在 README guided init 说明中补充 partial core 会在启动说明中提示。
   - 在 `docs/evolution-log.md` 记录本轮 gap、取舍、验证和 Gate。

4. 验证与提交
   - 运行新增 targeted integration。
   - 运行 guided init integration 文件。
   - 运行 `compileall`、`git diff --check`、`scripts/test-fast.sh`。
   - 创建中文本地 commit。
   - push 前运行 `scripts/test-full.sh`；如果仍因 DeepSeek DNS / 外部 evidence 发送权限失败，则不 push。
