# Guided Final Direct Return Target 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`src/harness_builder_agent/tools/interactive_init.py` 和 guided init integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`；本轮不修改 LLM、benchmark、Sensor gate、模块边界或 Runtime 契约。
- sub agent：尝试启动只读 explorer 审查最终确认直接返回目标，当前环境返回 `agent thread limit reached`；主线程继续。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 最终确认支持直接输入返回目标 | init North Star / 当前代码审查 | 用户在最终确认阶段可以直接输入 `scan` / `扫描`、`rules` / `团队规则`、`candidates` / `候选`、`workflow` / `工作流` 返回对应部分，也仍可输入 `back` 后二次选择 | 已支持 `back` / `返回` 后二次选择返回目标，并支持中英文目标别名 | 用户看到最终确认摘要里某个部分不对时，仍必须先输入 `back`，再输入目标；如果直接输入 `候选` 会被当成未知最终确认输入 | 降低最终确认修改成本，让中文 CLI 更自然，符合“交互低负担”和“用户可选择返回修改扫描理解、补充团队规则或取消”的目标 | 低；只扩展最终确认控制词解析，不改 schema、writer、LLM 或 Runtime | integration 覆盖直接 `候选` 进入候选复核并记录决策；覆盖 prompt 展示直接目标提示 | 无外部凭证 | CLI transcript 和 `interaction-decisions.yaml` 证明直接目标生效 | 本轮 |
| B. 返回 scan 后自动重新进入候选审查 | 上一轮 Gate | scan 修改后自动逐项复核刷新后的候选 | 当前已清空旧决策、最终确认展示待复核候选，可手动返回 candidates | 仍需要用户主动返回候选审查 | 更强审查闭环，但交互更重 | integration transcript | 需要产品取舍 | 自动重审后新决策进入产物 | 下一轮候选 |
| C. full regression / push 工作包 | Git 状态 / 用户要求 push | 本地功能批次同步 GitHub | 当前 `main...origin/main [ahead 77]`，`.env` 和 `.benchmarks` 已补齐 | `scripts/test-full.sh` 仍因 DeepSeek API 域名解析 / 外部数据发送权限失败；非 sandbox 重跑被安全策略拒绝 | 远端同步本地工作 | 外部服务和数据外发阻塞 | full + push | 网络 / 外部 API 权限 | full 通过后 push | 本轮后评估 |

排序结论：

1. 选择 A。它继续收口最终确认阶段的低负担返回修改体验，直接服务 init North Star 的 CLI 交互目标，且与当前代码变更边界小、可通过 mock integration 证明。
2. B 暂不选。A 先降低手动返回候选审查的成本；是否强制自动重审需要更明确的产品取舍。
3. C 受外部 API / 数据外发权限阻塞，不作为本轮功能 milestone；每轮完成后继续按规则评估。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认摘要中发现扫描、团队规则、候选或 Workflow 需要修改时，我可以直接输入对应目标 `扫描`、`团队规则`、`候选` 或 `工作流` 返回该部分，从而不必先输入 `返回` 再选择目标，也不会因为直接输入目标而触发未知输入。

## 设计

- 复用 `_normalize_final_back_stage()` 的 stage alias。
- `_confirm_summary()` 先解析 confirm / back / cancel；如果不是动作，再尝试解析为直接 stage。
- 直接 stage 命中时输出 `返回修改` 并返回 `scan` / `rules` / `candidates` / `workflow`。
- 更新最终确认 prompt，说明可以直接输入返回目标。
- 保留未知非空输入继续提示，不 silent confirm。

## 非目标

- 不自动重新进入候选审查。
- 不修改 scan / rules / candidates / workflow 各阶段行为。
- 不修改 `interaction-decisions.yaml` schema 或正式资产写入契约。
- 不执行 Runtime、不创建 `.ai/task-runs`。

## 验收标准

- RED：新增 integration 先证明最终确认直接输入 `候选` 不能进入候选复核。
- 实现后：
  - 最终确认 prompt 展示直接目标提示。
  - 直接输入 `候选` 进入 candidate review，后续 `a/r/e` 决策写入 `interaction-decisions.yaml` 和 candidate report。
  - 旧 `back -> rules`、中文别名和未知输入保护不回归。
  - `tests/integration/test_init_on_fixture_projects.py`、`compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：在最终确认 prompt 中，`scan` / `rules` / `candidates` / `workflow` 是控制词，不是自由文本输入；直接解析它们不会和补充内容冲突。
- Risk：prompt 变长；因此只在最终确认输入提示中用简短括号列出直接目标。
