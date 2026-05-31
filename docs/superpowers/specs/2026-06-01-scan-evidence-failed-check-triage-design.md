# Scan Evidence Failed Check Triage 迁移设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/local-unique-capability-migration.md`。
- 已读取相关工程文档：`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`。
- 已对比当前代码与测试：`interactive_init.py` 的 `_benchmark_signal_lines()` / `_benchmark_failed_check_label()` / `_benchmark_check_detail()`、`maintenance_triage.py`、`tests/unit/test_interactive_init_preview.py`、`tests/unit/test_maintenance_triage.py`、上一轮 init-summary evidence audit spec / plan。
- 按需未展开：`llm-contracts.md` 不再重复展开，因为本轮不改 LLM；architecture 未展开，因为不改模块边界；acceptance 未运行，因为不触碰真实 LLM 或真实仓库。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Scan evidence failed check triage | todo / 上轮 Gate | 已有 Harness 维护入口能把 `content:scan-report` / `content:init-summary` 失败翻译成中文 label、保留 missing detail，并给出专门 triage guidance | BenchmarkReport schema 保留 missing；Benchmark signals 已能输出 failed id 和 error detail | 新 check id 没有专门中文 label；Maintenance triage 只专门处理 hard gate 和 project-context，scan-report / init-summary 退成泛化 schema/content | Maintainer 再次进入 guided init 时能直接知道扫描审计摘要缺失，而不是只看到泛化失败 | 低：只改 label / triage helper 和 unit 测试，不改 benchmark 计算 | unit 覆盖 benchmark signals 和 maintenance triage | 依赖上一轮新增的 `content:scan-report` / `content:init-summary` | 本轮 |
| B. Failed check detail preservation system audit | todo | 系统性审查所有 benchmark check 的 missing/errors/detail 输出 | 多数关键 check 已保留 detail | 还缺完整 checklist 和旧报告兼容策略 | 更全面的维护入口诊断 | 中：范围更大，容易变成审计/重构 | 多个 unit / integration | 需要先稳定新增 check 的用户可见解释 | 后续候选 |
| C. Evidence helper 去重 | Gate 技术债 | evidence expansion / coverage helper 统一 | 当前 writer / benchmark 有重复 | 重复 helper 增加维护成本 | 降低后续迭代成本 | 中：重构跨模块 | 回归测试 | 不影响当前用户可见 triage | 后续候选 |

排序结论：

1. 选择 A，因为它是上一轮新增质量门禁后的直接用户可见缺口：benchmark 已能报告具体 missing，但已有 Harness 入口缺少专门解释和行动建议。
2. B 暂不选，因为完整系统审计范围更大；A 是它的一条小而完整的纵向切片。
3. C 保留为 Gate 技术债，不在本轮混入。

## 本轮 milestone

作为再次运行 guided `init` 进入已有 Harness 维护入口的 Harness Maintainer，当最近 benchmark 因 `content:scan-report` 或 `content:init-summary` 失败时，我可以在 Benchmark signals 和 Maintenance triage guidance 中看到中文解释、具体 missing detail 和下一步动作，从而知道要补齐 scan-report / init-summary 的扫描证据审计，而不是只能打开 YAML 猜测失败含义。

## 验收标准

- `_benchmark_failed_check_label()` 为 `content:scan-report` 和 `content:init-summary` 提供稳定中文解释。
- `_benchmark_signal_lines()` 对这两个 check 的 `missing` detail 继续输出 `benchmark_failed_check_error=<id>|<detail>`。
- `build_maintenance_triage()` 对这两个 check 生成专门的 `reason=scan_evidence_audit_incomplete` top action，source 指向具体 check id，detail 使用第一条 missing。
- `render_maintenance_triage_guidance_lines()` 对该 reason 输出中文建议，要求补齐 scan-report / init-summary 的扫描证据审计后重新运行 benchmark。
- 不改变 benchmark pass/fail 计算，不执行 Runtime，不创建 `.ai/task-runs`。
- 迁移 todo 和 evolution log 同步记录该 failed check detail preservation 小切片。

## 决策 / 取舍

- 本轮不新增 BenchmarkReport schema；复用现有 `missing` detail。
- 不把所有 content check 都专门化，只处理近期新增且与 scan evidence migration 直接相关的 `content:scan-report` 和 `content:init-summary`。
- `scan_evidence_audit_incomplete` 比泛化 `schema_content_failed_checks` 优先，但低于 hard gate command evidence；它属于审计上下文修复，不代表命令证据可执行性问题。

## Assumptions / Risks

- Assumption：用户再次进入已有 Harness 时，维护入口是定位 benchmark failed 的第一视图，因此新增 check id 必须有专门中文解释。
- Risk：如果多个 scan evidence check 同时失败，本轮只展示第一条 missing detail；完整列表仍在 `.ai/benchmark-report.yaml`。
- Sub agent 使用：尝试启动只读 explorer 审查本轮候选，但当前环境返回 `agent thread limit reached`，本轮由主线程完成分析、TDD、实现和验证。
