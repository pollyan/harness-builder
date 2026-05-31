# Evidence Reason Preservation 迁移设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/local-unique-capability-migration.md`。
- 已读取相关工程文档：`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/llm-contracts.md`。
- 已对比当前代码与旧备份分支：`backup/local-61-before-migration:src/harness_builder_agent/tools/scan_reconciler.py` 中 `_evidence_entry()` 会保留 `EvidenceFile.reason`；当前 main 在 `ProjectInventory.evidence` 中把 key evidence 的 reason 写成 `item.kind`，configs / ci / documents 通常只剩 kind。
- 已检查当前消费链路：`asset_writers/reports.py`、`asset_writers/guides.py` 已优先渲染 `reason`，但 benchmark 目前只校验 evidence path，不校验 reason。
- 按需未展开：architecture 文档不展开，因为本轮不改模块边界；真实 acceptance 不运行，因为本轮不触碰真实 DeepSeek 行为或外部仓库。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Evidence reason preservation | 迁移 todo / 旧分支对比 | 扫描 evidence 不只保留路径，还保留为什么被选中，并进入 scan-report 与 project-context | EvidenceFile 已有 reason；writer 已能渲染 reason | reconcile 写入 ProjectInventory 时丢失或降级 reason；benchmark 不防止 reason 从 Markdown 漂移 | Maintainer 审计扫描深度时能知道 path 的判断意义，避免只有路径没有解释 | 低：只增强 ProjectInventory entries 和 benchmark detail，不新增顶层字段 | unit 覆盖 reconcile；writer / benchmark 覆盖 Markdown reason 展示与缺失失败 | 不依赖外部服务 | 本轮 |
| B. 顶层 test/risk/API/LLM-requested inventory 字段恢复 | 迁移 todo / 旧分支对比 | ProjectInventory 直接暴露 test_files、risk_files、api_entrypoints、llm_requested_files | EvidenceBundle 已有这些 bucket，scan-report 通过 coverage selected paths 展示部分信息 | 当前 ProjectInventory schema 未声明这些顶层字段 | 更细机器契约，但会扩 schema 和下游报告 | 中：schema 扩展、产物兼容、测试面更大 | schema / init / benchmark / fixture tests | 需要重新评估“当前不新增顶层字段”的 todo 取舍 | 后续候选 |
| C. Failed check detail 系统性全量审计 | 上轮 Gate | 所有 benchmark failed checks 都带 missing/errors/detail | 已覆盖 scan-report/init-summary/project-context/content quality/hard gate 等重点 check | 仍未逐个审计所有 schema/content check 的 detail 完整性 | 维护入口诊断更完整 | 中：范围较散，容易变 checklist | benchmark integration 可覆盖 | A 之后更清晰 | 后续候选 |
| D. Evidence helper 去重 | 上轮 Gate | scan-report、project-context、init-summary 的 evidence helper 复用 | 当前多个 helper 重复 | 维护成本升高 | 降低后续漂移 | 中：纯重构但影响多产物 | 现有 writer / benchmark tests | 不直接形成用户可见增量 | 后续技术债 |

排序结论：

1. 选择 A，因为它直接命中迁移 todo 尚未完成的 `evidence reason preservation`，并且旧分支已有清晰、小型、可移植的实现线索；它同时服务 init North Star 的“可解释”和“深度优先”。
2. B 暂不选，因为它涉及 ProjectInventory 顶层 schema 扩展，todo 当前也记录“更细顶层 inventory 字段仍不新增”；先恢复 reason 可以不破坏现有契约。
3. C / D 暂不选，分别保留为后续系统审计和技术债候选。

## 本轮 milestone

作为 Harness Maintainer，当我查看 `.ai/scan-report.md`、`.ai/guides/project-context.md` 或 benchmark report 审计扫描 evidence 时，我可以看到每个关键 evidence path 为什么被选中，并且 benchmark 会在 reason 从报告中丢失时指出具体 path，从而判断扫描结论不是只有路径列表，而是有可解释依据。

## 验收标准

- `reconcile_scan()` 写入 `ProjectInventory.evidence`、`documents`、`configs`、`ci_files` 时保留 `EvidenceFile.reason`；proposal 提供 configs / ci_files 时，如果同 path 的确定性 evidence 有 reason，也应补齐 reason。
- `scan-report.md` 和 `project-context.md` 的 evidence section 继续使用 `reason` 优先渲染。
- `content:scan-report` 和 `content:project-context-evidence-context` 在 inventory entry 带 `reason` 时校验 reason 是否出现在对应 evidence section，缺失时返回 `missing_evidence_reason:<path>`。
- 不新增 ProjectInventory 顶层字段，不执行 Runtime，不创建 `.ai/task-runs`。
- 迁移 todo、engineering docs 和 evolution log 记录本轮切片。

## 决策 / 取舍

- 复用现有 `ProjectInventory` 字段中的自由结构 dict，不新增 schema 字段；这是最小兼容迁移。
- 对只有 `kind`、没有 `reason` 的旧 inventory 不强制 reason 校验，避免旧 Harness 因历史数据缺字段突然失败。
- proposal 的 configs / ci_files 若已有更具体 reason，保留 proposal；若无 reason，则从确定性 evidence entry 补齐。

## Assumptions / Risks

- Assumption：`ProjectInventory` 中 evidence entries 允许携带 `reason`，当前 writer 已按该字段渲染。
- Risk：真实 LLM proposal configs / ci_files 的 path 与确定性 evidence path 不一致时无法补齐 reason；这时仍保留 proposal 原样，不制造 fallback。
- Sub agent 使用：尝试启动只读 explorer 调研旧分支 evidence reason，但当前环境返回 `agent thread limit reached`，本轮由主线程完成对比、TDD、实现和验证。
