# 本地独有能力迁移收口设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/local-unique-capability-migration.md`、`docs/todos/README.md`、`docs/todos/archive.md`、`docs/todos/scanner-v2-review-and-migration.md`。
- 已读取相关工程文档：`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`。
- 已审计当前代码：`benchmark.py` 中重点 content checks 已保留 `missing` / `errors` / `weak_commands`；`scan_reconciler.py` 已保留 evidence reason；scan-report / project-context / init-summary 已由 benchmark 守住 evidence audit。
- 已对照旧分支和历史 spec：旧分支中依赖的 `ProjectInventory.test_files` / `risk_files` / `api_entrypoints` / `llm_requested_files` 顶层字段不在当前 schema 中，当前设计已经明确先通过 `scan_metadata.coverage.bucket_coverage[].selected_paths` 和 evidence expansion 展示，不恢复旧顶层字段。
- 按需未展开：architecture 不展开，因为本轮不改模块边界；acceptance 不运行作为设计输入，push 前按规则运行 full。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 本地迁移工作包收口归档 | 迁移 todo / 当前审计 | 本地 61 提交不再作为整体合并目标，已迁移能力和放弃/后续项清楚记录，后续目标模式不被旧合并 todo 牵引 | 已连续迁移 existing harness 入口、benchmark/routing signals、human input、scan-report、init-summary、evidence reason、content quality detail 等切片 | todo 仍 open，会让目标模式继续在“本地迁移”框架内循环，难以进入新的 North Star gap | 建立干净远端基线，降低冲突和重复迁移风险 | 低：文档状态变更，无产品行为改动 | todo 索引、archive、evolution log、git status、fast/full/push | push 需要 full regression 和网络权限 | 本轮 |
| B. 恢复顶层 test/risk/API/llm_requested inventory 字段 | 迁移 todo residual | ProjectInventory 机器契约直接暴露各类 evidence bucket | EvidenceBundle 和 LLM prompt 已有这些 bucket；scan-report 通过 coverage 展示 selected paths | ProjectInventory 未新增顶层字段 | 未来更细审计可能有用 | 中高：schema 扩展、兼容、writer/benchmark 全链路 | schema / unit / integration / benchmark | 需要重新确认产品契约 | 后续候选，不阻塞迁移收口 |
| C. Benchmark failed check detail 系统性全量审计 | 上轮 Gate / todo residual | 所有 failed checks 都有足够 action detail | 重点路径已有 missing/errors/weak details | 少数 check 仍可进一步细化，例如 generation trace required 字段缺失时可列 missing | 提升长期诊断质量 | 中：范围散，适合单独工作包 | benchmark integration | 不依赖旧分支合并 | 后续候选，不阻塞迁移收口 |
| D. Evidence helper 去重 | Gate | evidence helper 统一，减少漂移 | 当前重复 helper 已有测试守住行为 | 代码维护成本仍在 | 降低未来改动风险 | 中：纯重构 | 现有测试 | 无 | 后续技术债 |

排序结论：

1. 选择 A，因为本地独有 / 更细能力迁移已经形成一组可独立验收的本地 commits；继续把 B/C/D 塞在同一个迁移 todo 内，会让“迁移旧分支”变成无边界长期主题。
2. B 暂不选，因为当前多份 spec / evolution log 已记录不恢复旧顶层字段的取舍；如果未来要做，应作为新的 schema 设计而不是迁移收尾。
3. C/D 暂不选，因为它们是后续质量提升，不是本地 61 提交整包合并的阻塞项。

## 本轮 milestone

作为 Harness Maintainer，当我查看 `docs/todos/` 和当前 git 分支时，我可以看到本地独有 / 更细能力迁移工作包已经收口归档、已迁移切片和未迁移取舍清楚可追溯，并且本地 commits 已通过 full regression 后同步远端，从而后续目标模式可以回到 init North Star 的新 gap，而不是继续围绕旧 61 提交做重复合并。

## 验收标准

- `docs/todos/local-unique-capability-migration.md` 状态改为 `implemented`，并记录完成说明、已迁移切片、未迁移取舍和后续候选。
- `docs/todos/README.md` 不再把该 todo 列为 open；说明当前迁移工作包已归档，后续从 North Star / scanner / benchmark 新 gap 进入。
- `docs/todos/archive.md` 增加本 todo 的归档记录。
- `docs/evolution-log.md` 增加本轮收口记录。
- 不改产品代码，不改变 CLI / schema / Runtime 边界。
- 提交前运行 `scripts/test-fast.sh`；因本轮完成完整迁移工作包，push 前运行 `scripts/test-full.sh`，再 push。

## 决策 / 取舍

- 不把 `test_files` / `risk_files` / `api_entrypoints` / `llm_requested_files` 顶层字段恢复作为迁移包阻塞项；未来如果需要，按新 schema milestone 处理。
- 不把 benchmark failed check 细节全量审计作为迁移包阻塞项；重点用户路径已迁移，系统性审计可作为后续质量工作。
- 本轮文档变更有独立价值，因为它决定后续目标模式选题和 push 边界。

## Assumptions / Risks

- Assumption：本地迁移包的独立价值由多个已提交切片共同构成，适合统一 push。
- Risk：`scripts/test-full.sh` 依赖真实 DeepSeek / 真实仓库 / 网络；如果环境缺失，按 AGENTS 明确失败原因，不把本地 fast 当作远端可推送证明。
- Sub agent 使用：尝试启动只读 explorer 审查归档判断，但当前环境返回 `agent thread limit reached`，本轮由主线程完成审计、文档收口和验证。
