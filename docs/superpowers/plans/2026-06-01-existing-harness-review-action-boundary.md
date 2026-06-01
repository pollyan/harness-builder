# Existing Harness Review Action 边界拆分计划

## 用户故事

作为 Harness Builder 维护者，当我后续修改已有 Harness 入口中的候选治理、human-input 治理或初始 LLM 候选治理动作时，我可以在独立的 review action 模块里维护这些动作，并由现有 guided integration 回归证明 CLI 行为、trace、review-only 边界不变，从而降低一个动作变更影响整个维护入口的风险。

## 验收标准

- 架构边界测试先失败，证明缺少独立 review action 模块或 runner 仍直接依赖 review governance 细节。
- 新增 `existing_harness_action_failures.py` 与 `existing_harness_review_actions.py`。
- `existing_harness_action_runner.py` 只调度 review 类 delegate，不直接导入 review governance schema / tool。
- guided existing Harness integration 回归通过。
- 文档事实源和演进记录同步。
- fast regression 通过；push 前 full regression 按规则执行。

## 步骤

1. 写 RED unit 边界测试。
2. 抽出 action-specific 失败 helper 到独立模块。
3. 抽出 `review-candidate`、`review-human-input`、`review-initial-candidate` 分支到 review action 模块。
4. 精简 runner imports 和 dispatch。
5. 运行 targeted unit、existing Harness integration、compileall、diff check、fast regression。
6. 更新 `docs/engineering/architecture.md` 与 `docs/evolution-log.md`。
7. 提交本轮改动。
8. 运行 `scripts/test-full.sh`，若通过则 push；若因外部 acceptance 前置失败则不 push 并报告。
