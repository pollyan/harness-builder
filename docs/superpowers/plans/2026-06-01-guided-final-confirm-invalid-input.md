# Guided Final Confirm Invalid Input 计划

## 用户故事

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认阶段误输入了未知命令或把 `confirm` 拼错时，我可以看到明确的无效输入提示，并且 Harness Builder 不会写入正式 `.ai` 资产，直到我显式输入 `confirm` 或按默认回车确认，从而避免 typo 触发误写入。

## 验收标准

- 最终确认输入 `cnofirm` 等未知非空值不会写入资产。
- CLI 输出无效输入提示，并说明有效选项是 `confirm`、`back`、`cancel`。
- 用户后续输入有效 `confirm` 后才写入 `.ai`。
- 空回车默认 confirm、`back`、`cancel` 既有语义不回归。
- 不修改 schema、writer、LLM、benchmark 或 Runtime 分工。

## 步骤

1. 新增 guided init integration RED test：
   - 在最终确认先输入未知值，再输入 `confirm`。
   - 断言输出无效提示，并且完成写入。
   - 通过输出顺序证明无效提示发生在初始化完成前。
2. 修改 `_confirm_summary()`：
   - 对最终确认输入使用循环解析。
   - `""` / `confirm` 返回 confirm。
   - `back` 进入返回目标选择。
   - `cancel` 返回 cancel。
   - 其他输入输出提示并继续询问。
3. 同步 `docs/engineering/init-workflow.md` 的稳定规则。
4. 更新 `docs/evolution-log.md`。
5. 运行 targeted integration、完整 guided init integration、compileall、diff check、`scripts/test-fast.sh`。
6. 本地提交。
7. 运行 `scripts/test-full.sh`；若仍缺外部 acceptance 前置则不 push。

## Self-Harness Gate 检查点

- README 是否需要更新：此为最终确认错误恢复细节，预计工程规则即可。
- docs/todos 是否需要新增：预计不需要。
- 后续候选：自动重新审查 candidates、进一步减少最终确认 prompt 的重复大段输出。
