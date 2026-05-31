# Self-Improve 真实 LLM Acceptance 覆盖

## 问题

`self-improve` 已经把 maturity assessment、deterministic improvement candidates、LLM maturity review 和 LLM asset candidate generation 串成一个纵向自改进包，但当前本地快速测试主要通过 mock LLM 覆盖该命令。

## 当前现状

- `tests/integration/test_assess_improve_commands.py` 覆盖 `self-improve` 的 review-only package、manifest schema、benchmark 兼容和不创建 `.ai/task-runs`。
- `tests/acceptance/test_real_repositories_e2e.py` 当前只跑 `init/assess/improve/benchmark`。
- `review-maturity` 和 `generate-asset-candidates` 的真实 DeepSeek 行为依赖已有 LLM 契约测试和人工运行，但还没有通过 acceptance 串到 `self-improve` 命令。

## 理想状态

在真实开源仓库 acceptance 中增加可控的 `self-improve` 验收路径，验证真实 DeepSeek 能生成 schema-valid maturity review、asset candidates 和 self-improve package，并且 benchmark 能校验这些 review-only 产物。

## 影响范围

- `tests/acceptance/test_real_repositories_e2e.py`
- `scripts/test-full.sh`
- DeepSeek 调用耗时和稳定性
- `docs/engineering/testing-strategy.md`

## 初步验收标准

- acceptance 在至少一个真实仓库上运行 `self-improve`。
- 断言 `.ai/review/self-improve-package.yaml` 通过 schema。
- 断言 `.ai/review/asset-candidates.yaml` 中的候选保持 `pending_harness_maintainer_review`。
- 断言 `.ai/task-runs` 未被创建。
- 断言后续 benchmark 包含并通过 `content:self-improve-package`。

## 备注

该项会增加真实 LLM 调用成本和执行时间，适合作为独立 milestone 评估是否只覆盖一个真实仓库，或通过环境变量控制扩展验收。
