# Risk Context Consistency Benchmark 迁移设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/local-unique-capability-migration.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`。
- 已对比：当前 `benchmark.py`、`write_assets.py`、Guide / Sensor writer、benchmark integration tests、`backup/local-61-before-migration` 中 risk context consistency 旧实现和测试。
- 按需未展开：LLM contracts 未展开，因为本轮不改 LLM prompt、DeepSeek 配置或 scan schema；architecture 未展开，因为不调整模块边界。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Risk context consistency | todo / Gate / 旧分支 | scan risk path 在 project-context、verification sensor 和 standard routing 中一致 | 当前 Guide / Sensor 已渲染风险路径；维护入口已识别 `content:risk-context-consistency`；routing signals 已能展示 `risk_area:*` | 当前 benchmark 没有该 check；生成的 `harness-config.yaml` 也不会把扫描风险路径写入 standard escalation | 防止风险只出现在 Markdown 而没有进入 Workflow routing，提升质量门禁和维护入口信号可信度 | 中：会改变 benchmark hard status，需要确保生成 Harness 自身通过 | integration 正向生成、三类负向缺失、report check id | 依赖当前 risk area 渲染稳定；不依赖真实 LLM | 本轮 |
| B. Project-context evidence context gate | todo / 旧分支 | project-context 保留 inventory evidence path 和 LLM evidence expansion 摘要 | 当前 Guide 有 `## 来源证据`，scan metadata 已记录 evidence expansion | 当前 benchmark 未检查 evidence path / expansion 细节；writer 是否完整表达仍需进一步对齐 | 提升仓库理解深度和可审计性 | 中高：可能要求 scan report / guide writer 一起补齐 | integration 负向 missing evidence path / expansion detail | 依赖 evidence writer 迁移范围更大 | 下一轮候选 |
| C. Scan evidence reason/report visibility | todo / Scan evidence | test / risk / API entrypoint / document evidence reason 在 report、guide、summary 中可审计 | 当前 inventory 已有多类 evidence 字段，scan metadata 已增强 | 各类 evidence reason 在语义资产里的覆盖仍不完整 | 直接服务 init North Star 的深度理解 | 中高：跨 scan reconciler、report writer、summary writer | unit / integration / fixture init | 可能和 B 合并成更完整 evidence 可审计切片 | 后续合并评估 |

排序结论：

1. 选择 A，因为它是当前迁移 todo 中“已被维护入口承接但 benchmark 主体缺失”的断点；完成后已有 Harness 入口、Benchmark signals 和质量门禁会闭环。
2. B 与 C 更靠近 evidence 深度，但它们共享 scan evidence writer 数据流，适合下一轮作为一个更完整的仓库理解可审计切片评估。

## 本轮 milestone

作为 Harness Maintainer，当我运行 `benchmark` 验收包含扫描风险区域的 Harness 时，我可以确认每个 scan risk path 同时出现在 `.ai/guides/project-context.md`、`.ai/sensors/verification.md` 和 `.ai/harness-config.yaml` 的 standard escalation routing 中；如果任一环缺失，`benchmark-report.yaml` 会给出精确 `missing_*_risk:<path>` 错误，从而避免高风险路径只停留在文档叙事而没有进入可执行路由策略。

## 验收标准

- `benchmark` 报告包含 `content:risk-context-consistency`。
- 无风险区域时该 check 通过并记录 `risk_area_count=0`。
- 有风险区域且 Guide / Sensor / routing 都包含路径时该 check 通过。
- 缺少 project-context 风险路径时失败并报告 `missing_project_context_risk:<path>`。
- 缺少 verification sensor 风险路径时失败并报告 `missing_verification_sensor_risk:<path>`。
- 缺少 standard routing 的 `risk_area:<path>` trigger 且 rationale 也不包含路径时失败并报告 `missing_routing_risk:<path>`。
- `write_initial_assets()` 生成的 `harness-config.yaml` 会把前几个扫描风险路径写入 standard escalation trigger 或 rationale，使新生成 Harness 不因新增 gate 自己失败。
- 相关 README、engineering docs、todo 和 evolution log 同步说明该质量门禁。

## 决策 / 取舍

- 复用旧分支的独立 `content:risk-context-consistency` check，而不是把风险路径校验塞进 `content:workflow-routing-policy`，这样维护入口已有的 `risk_context_inconsistent` triage 可以直接消费。
- 只验证路径在三类产物中的一致性，不判断风险是否已经被人工确认；人工确认仍由 questionnaire / human-input-needed 处理。
- routing 接受两种证据：`risk_area:<path>` trigger 或 rationale 中包含 path。生成侧优先写 trigger，并补 rationale 解释。
- 只取前 5 个 risk path，避免异常大型风险列表让 benchmark 报告过长。

## Assumptions / Risks

- `ProjectInventory.stack_extensions["risk_areas"]` 或 `stack_extensions["llm_scan_proposal"]["risk_areas"]` 中的 `path` / `area` 是当前 scan risk path 的事实源。
- 旧 Harness 如果手工删掉 Guide / Sensor / routing 中任一风险路径，新增 check 会让 benchmark failed；这是有意暴露不一致，不做 silent fallback。
- 本轮不执行 Runtime、不创建 `.ai/task-runs`，只生成和验证 Builder 侧资产契约。
- Sub agent 使用：按目标模式要求尝试启动 explorer 做只读审查，但当前返回 `agent thread limit reached`，本轮由主线程完成对比和实现。
