# Init Completion 资产概览压缩设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、上一轮 Existing Harness action runner spec / plan、`docs/evolution-log.md`。
- 当前代码 / 测试检查：`render_init_completion_message()` 已经把当前成熟度、建议下一步、Benchmark 健康度和优先查看入口放在 `本次已生成` 之前；`_completion_user_supplement_lines()` 已压缩为每类条数 + 示例。但 `_generated_asset_summary()` 仍逐项输出 8 行文件 / 目录状态：项目清单、命令目录、Guides、Sensors、Workflow Skills、成熟度报告、待确认项、生成 trace。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo；迁移 todo 已 implemented。
- 按需未展开：`docs/engineering/llm-contracts.md` 与 `sensor-and-gate-rules.md`；本轮不修改 LLM、scan、schema、Sensor 或 benchmark 检查规则。
- Sub agent：尝试启动 explorer 做 completion message 只读审查，但当前会话返回 `agent thread limit reached`；本轮由主线程完成 Gap Analysis、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 首次 init completion 资产概览压缩 | 上一轮 Gate / init North Star | 写入完成后终端摘要短、行动优先，只用资产类型概览确认生成结果，详细文件清单由 `init-summary.md` 与 trace artifacts 承担 | completion 已行动优先，优先入口和用户补充已压缩 | `本次已生成` 仍是 8 行文件状态清单，和优先入口重复，削弱短交付摘要 | 保护首次 init 的主要交付说明，让 Maintainer 更快看到结果、下一步和审计入口 | 低：只改 completion renderer 和 transcript 断言，不改生成资产 | unit 覆盖资产概览行数、分组状态和缺失 detail；integration 验证真实 fixture transcript | 无外部凭证；依赖现有 `.ai` 文件布局 | completion 中 `本次已生成` 控制在 3-4 行资产类型概览，仍显式显示 missing 和详细清单入口 | 本轮 |
| B. 继续拆分 `interactive_init.py` 首次 init scan / supplement 交互 | 工程架构 / 当前代码 | 主向导文件继续按扫描展示、用户补充、确认摘要拆模块 | prewrite preview、existing Harness runner 已拆出，`interactive_init.py` 仍 1200+ 行 | scan 展示、用户补充解析和最终确认仍在同一文件 | 降低后续 init 主流程维护风险 | 中：涉及大量 guided transcript 和用户输入状态 | unit + guided integration | 无外部依赖 | 适合单独工程信任故事 | 下一轮候选 |
| C. Push 前 full regression / 远端同步 | Gate / git 状态 | 完整本地工作包形成后再 full regression 与 push | 当前 main ahead 47，工作树干净 | 尚未定义推送边界；full regression 依赖真实 acceptance / DeepSeek / 真实仓库 | 降低远端分叉风险 | 高，可能受外部凭证和真实仓库影响 | `scripts/test-full.sh` + push | 需要完整工作包边界和外部条件 | 不混入本轮用户体验切片 | 后续候选 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 中“写入后的短交付摘要”和“最值得先看的 3 到 5 个文件”目标；当前完成摘要已经行动优先，但资产清单仍偏机械。
2. B 暂不选，因为上一轮刚完成 existing Harness runner 抽取，本轮回到用户可见首次 init 体验更符合短中期优先级。
3. C 暂不选，因为 push 需要完整工作包和 full regression，不应和本轮小型体验切片混合。

## 本轮 Milestone

作为 Harness Maintainer，当我完成首次 `harness-builder-agent init` 后，我可以在终端 `== 初始化完成 ==` 的 `本次已生成` 段看到 3-4 行按类型分组的资产概览和详细审计入口，而不是一长串文件状态，从而更快确认第一版 Harness 已建立，并把注意力留给当前成熟度、下一步、Benchmark 和优先查看文件。

## 验收标准

1. `_generated_asset_summary()` 输出按资产类型分组的紧凑概览，而不是 8 行逐项文件状态清单。
2. 概览必须覆盖核心机器契约、语义控制资产、审查 / 经验资产、trace / 审计入口，并显示每组 `ready_count/total_count`。
3. 如果某组存在缺失项，概览必须显式列出最多 3 个 missing detail，不能伪装为成功。
4. 概览必须指向 `.ai/init-summary.md` 和 `.ai/runs/*/artifacts.yaml` 作为完整清单 / 审计入口。
5. Completion message 顺序不变：当前成熟度、建议下一步、Benchmark 健康度、优先查看仍位于 `本次已生成` 前。
6. 更新 README 与 `docs/engineering/init-workflow.md` 中关于 completion message 的长期表述，从“生成资产清单”调整为“生成资产类型概览 / 详细清单入口”。
7. 不修改 `.ai` schema、实际生成资产、benchmark 规则、LLM 或 Runtime 分工。
8. 提交前运行 `scripts/test-fast.sh`。

## 关键决策 / 取舍

- 本轮只改终端 completion message 的资产段；`init-summary.md` 的持久化内容和 trace artifacts 继续承担完整审计。
- 使用固定分组而不是动态扫描全部 `.ai`，避免把缓存、候选历史或用户手工文件混入“本次生成”。
- 对缺失项仍显式展示 missing，保持 no silent fallback。

## Assumptions / Risks

- Assumption：Maintainer 在 completion 中需要确认“资产类型已建立”，不需要逐行读所有核心文件状态；详细审计可进入 `init-summary.md` 和 trace artifacts。
- Risk：测试可能只断言 `本次已生成` 存在，不断言具体资产行；本轮新增 unit 锁定 compact behavior。
- Risk：过度压缩可能隐藏某类缺失；本轮按分组显示 ready count 和 missing detail，避免误导。
