# Existing Harness Benchmark Action Design

## North Star 能力模块

- CLI Experience：`init` 是首次进入和后续维护的主入口。
- Benchmark / Review Intelligence：benchmark 是 Harness 资产 schema、内容、引用和 hard gate 证据的质量门禁。
- Maturity & Evolution：运行质量门禁应刷新派生成熟度证据和改进候选，帮助 Maintainer 看见下一步缺口。

## Current State Gap Analysis

| 候选 gap | 目标态要求 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 排序 |
|---|---|---|---|---|---|---|---|
| existing-Harness guided `benchmark` | 再次执行 `init` 能从维护入口运行质量验收 | standalone `benchmark` 已存在，维护入口只展示最近状态 | 用户仍需记住专家命令，状态摘要无法直接刷新质量报告 | 高，补齐“向导组织底层能力” | 低到中，需明确写边界 | 高，integration 可覆盖不扫描、不覆盖正式资产、报告失败项 | 1 |
| guided `recommend-workflow` 查看建议 | 从维护入口生成 review-only workflow recommendation | standalone 命令存在 | 需要 task brief、LLM 和 review artifact UX | 中 | 中，涉及 LLM 与候选态 | 中 | 2 |
| 候选治理菜单 | 从维护入口处理 accepted/deferred/rejected/applied | standalone `review-candidate` 存在 | 需要候选选择、rationale、apply 边界 | 高 | 高，可能修改正式资产 | 高但范围大 | 3 |

本轮只选择 existing-Harness guided `benchmark`，因为它是最小纵向用户故事：用户进入主向导、选择质量验收、看到通过/失败摘要、得到结构化报告，并且不覆盖正式 Harness 资产。

## 设计

当 guided `init` 检测到已有 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml` 后，在维护入口新增：

```text
- benchmark：运行 Harness 质量门禁，刷新 benchmark / maturity / improvement 派生产物，不覆盖正式 Harness 资产。
```

用户输入 `benchmark`、`bench`、`质量` 或 `验收` 时：

1. 复用现有 `run_benchmark(repo, profile=inventory.primary_stack)`。
2. 把当前 `init` trace 传入 `run_benchmark`，因为 benchmark 会校验最新 generation trace；随后再用 existing-Harness action summary 重新 `finish`，让最终 trace 语义归属 guided maintenance action。
3. 在 `init` trace 中记录 existing-Harness action、`.ai/benchmark-report.yaml`、maturity 派生产物、improvement 派生产物和 Experience index。
4. 打印中文摘要：`Benchmark 已通过/未通过`、hard status、quality status、check 计数、失败项前几条、报告路径。
5. benchmark 失败时，本轮设计选择 guided `init` exit code 仍为 0，因为这是人工维护入口中的一次状态刷新动作；失败必须在输出、报告和 trace 中显式可见，不能被静默吞掉。CI/自动化仍应使用 standalone `benchmark` 命令，它继续按 hard gate 失败返回非零。

## 边界与失败模式

- 这不是只读动作。`run_benchmark` 会刷新 `.ai/benchmark-report.yaml`，并通过 `assess_maturity` / `generate_improvements` 刷新 maturity、evolution、pending improvements 和 experience index 等派生产物。
- 它不能重新扫描已有 Harness；测试会把 `interactive_init.scan_repository`、`benchmark.scan_repository` 和 `assess_maturity.scan_repository` 替换为失败函数。
- 它不能覆盖正式资产：`project-inventory.json`、`command-catalog.yaml`、`harness-config.yaml`、Guides、Sensors、Workflow Skills、scan metadata、LLM proposal 和 weapon library selection。
- benchmark 失败不能降低断言、不能改成成功、不能隐藏失败项；输出和 trace 必须保留 failed status 与失败计数。

## Assumptions / Risks

- Assumption：guided 维护入口面向人工状态刷新，因此 benchmark 失败不应阻止 `init` 完成消息；自动化质量门禁仍使用 standalone command 的非零退出码。
- Risk：`run_benchmark` 文案里“without rewriting”容易被误读为完全只读；本轮文档明确只保证不覆盖正式 Harness 资产。
- Risk：底层 `run_benchmark` 当前可接收 trace 并 finish；guided action 需要在它完成后再次 finish，覆盖为 `existing_harness_action: benchmark` 的最终 summary。该行为通过 integration trace 断言固定。

## Sub Agent 使用

使用 explorer 子代理审计本轮候选 gap。子代理建议优先实现 existing-Harness guided `benchmark`，并指出 `run_benchmark` 会刷新派生产物、不能称为只读，以及 trace 不应直接传入底层 benchmark。

## 可执行验收标准

- guided existing-Harness 菜单包含 `benchmark`。
- 输入 `benchmark` 能生成并校验 `.ai/benchmark-report.yaml`。
- 输出包含 hard status、quality status、check 数和报告路径。
- benchmark failed 时输出失败项 id，trace 记录 failed status，但 guided `init` 不静默成功化该报告。
- 不调用扫描，不覆盖正式 Harness 资产。
- trace summary 包含 `existing_harness_action: benchmark`、`benchmark_status` 和 failed check count。
- README、init workflow 文档和 todo 状态同步该动作边界。
