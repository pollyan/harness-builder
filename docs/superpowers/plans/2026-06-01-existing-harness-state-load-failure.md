# Existing Harness 状态读取失败保护计划

## 用户故事

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness，但核心 `.ai` 状态文件已经损坏或不符合 schema 时，我可以看到明确、中文、可行动的读取失败说明，并确认 Builder 没有重新扫描或覆盖正式资产，从而能先修复 Harness 状态再继续维护。

## 步骤

1. 增加失败测试
   - 在 existing Harness integration 测试中新增损坏 `harness-config.yaml` 的 guided `init` 用例。
   - mock `scan_repository` 为失败函数，证明读取损坏状态不会触发重新扫描。
   - 断言 RED：当前输出缺少 `已有 Harness 读取失败` 等友好边界。
   - 增加可选 `maturity-score.yaml` 损坏用例，覆盖可选状态文件存在但 schema / YAML 无效时不能静默忽略。

2. 实现读取保护
   - 在 `interactive_init.py` 增加局部异常类型和 `_load_existing_harness_state()`。
   - 读取并校验 inventory、config 和可选 score；失败时携带 source path、error type 和短摘要。
   - `_handle_existing_harness_entry()` 捕获读取异常，输出中文失败说明，写 existing-harness failed trace，并 `typer.Exit(1)`。

3. 更新长期规则与演进记录
   - 在 `docs/engineering/init-workflow.md` 记录已有 Harness 状态文件损坏必须显式失败、不得 fallback 到扫描或只读退出。
   - 在 `docs/evolution-log.md` 记录本轮 gap、决策、验收、sub agent 使用失败和 Gate。

4. 验证与提交
   - 运行新增 targeted integration。
   - 运行 existing Harness 相关 guided init integration。
   - 运行 `compileall`、`git diff --check`、`scripts/test-fast.sh`。
   - 创建中文本地 commit。
   - push 前运行 `scripts/test-full.sh`；若仍因 DeepSeek 网络 / 外部 evidence 发送权限失败，则不 push 并明确汇报。
