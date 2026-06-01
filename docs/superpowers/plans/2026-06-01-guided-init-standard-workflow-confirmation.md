# Guided Init Standard Workflow 确认计划

## 用户故事

作为 Harness Maintainer，当我在首次 guided `init` 中进入“推荐工作流”阶段并准备补充 Workflow 说明时，我可以同时看到 `lightweight`、`bugfix` 和 `standard` 三类工作流及 standard 的高风险升级边界，从而基于完整的工作流模型补充团队约束，而不是只围绕低风险和缺陷修复两个路径作答。

## 验收标准

- `_show_workflows()` 输出包含 `standard` 及高风险 / 跨模块 / 安全数据升级说明。
- `WorkflowConfirmation.shown_workflows` 记录 `lightweight`、`bugfix`、`standard`。
- guided init transcript 和 `interaction-decisions.yaml` 同步反映三类工作流。
- Workflow 补充仍是 review-only，不直接修改正式 routing policy。
- 相关文档和演进记录同步。
- fast regression 通过；push 前 full regression 按规则执行。

## 步骤

1. 新增 RED unit test 覆盖 `_show_workflows()`。
2. 更新 `_show_workflows()` 文案和 `shown_workflows`。
3. 更新 guided init / interaction decisions 相关测试断言。
4. 更新 README、`docs/engineering/init-workflow.md`、`docs/evolution-log.md`。
5. 运行 targeted unit / integration、compileall、diff check、`scripts/test-fast.sh`。
6. 创建本地提交。
7. 运行 `scripts/test-full.sh`；若通过则 push，若外部 acceptance 前置失败则不 push 并报告。
