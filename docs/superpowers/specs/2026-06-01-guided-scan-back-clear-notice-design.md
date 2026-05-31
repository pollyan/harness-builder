# Guided Init Scan 返回修改替换 / 清空提示设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/evolution-log.md`、上一轮 scan 返回修改 spec / plan、`interactive_init.py` 和相关 guided init integration tests。
- 按需未展开：`llm-contracts.md`、`sensor-and-gate-rules.md`、`architecture.md`，因为本轮不修改 LLM prompt/schema、benchmark gate、Sensor 规则或模块边界。
- 当前 todo 状态：`docs/todos/README.md` 显示没有 open todo；`local-unique-capability-migration.md` 已 `implemented`，不再作为本轮执行清单。
- Sub agent：按目标模式尝试启动只读 explorer 审查 back->scan 交互，但当前返回 `agent thread limit reached`；本轮由主线程完成调研。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 返回 scan 时提示替换 / 清空语义 | 上轮 Gate / 新发现 | 用户返回扫描补充时，CLI 明确说明新输入会替换上一版补充，直接回车会清空上一版补充；清空后可见确认 | 代码已基于 clean baseline 应用最新 `GuidedScanOverrides`，资产不会残留旧补充 | 用户看不到替换语义；直接回车清空旧补充时没有可见确认，容易误以为旧补充仍保留 | 提升渐进式协作可信度，让“用户输入 -> 系统理解 -> 后续决策”边界可见 | 低：只改 guided CLI 文案和少量 helper，不改 schema / writer / LLM | integration CLI transcript + 产物断言 | 无外部依赖 | 本轮 |
| B. Scan correction diff preview | init North Star / 可解释性 | 返回 scan 后展示旧补充将移除、新补充将应用的差异 | 当前有即时理解 / 影响说明 | 没有逐项 diff，复杂补充时仍需用户自己比较 | 更强审计感 | 中：需要定义 diff 格式，可能拉长 CLI 输出 | CLI transcript tests | 需在 A 的替换 / 清空语义稳定后设计 | 下一轮候选 |
| C. Workflow note 结构化 impact schema | 上轮 Gate | Workflow 补充不只是自由文本 note，而有机器可消费影响分类 | 当前会写入 decisions / project-context / human-input-needed 并提示 review-only | 缺少结构化影响字段，后续智能改进难消费 | 增强 Workflow 设计闭环 | 中：涉及 schema、writer、测试迁移 | schema + integration tests | 需要单独设计契约 | 下一轮候选 |
| D. Push 前 full regression / 远端同步 | 工程治理 | 累积本地 commit 形成完整工作包后，通过 full regression 再 push | 当前本地领先远端 19 commits | full 依赖 DeepSeek key 和 `.benchmarks`，当前未重新满足 push 条件 | 降低远端分叉风险 | 中：依赖凭证和真实仓库 | `scripts/test-full.sh` + push 状态 | 需要外部前置条件 | 后续工作包 |

排序结论：

1. 选择 A，因为上一轮已经修正正式资产正确性，但用户在 CLI 中还看不到替换 / 清空边界。`init-north-star.md` 要求关键交互必须及时复述系统理解和影响；返回 scan 是纠错路径，尤其需要显式说明。
2. B 是 A 的增强版，但 diff 语义更复杂，适合作为后续单独设计，避免本轮把清空提示扩展成大交互改版。
3. C 属于 Workflow 补充机器契约，不属于扫描补充返回修改同一用户旅程。
4. D 是 push / release 工程治理，当前不阻塞本轮小切片的本地 commit；push 前仍需 full regression。

本轮 milestone：

作为 Harness Maintainer，当我在最终确认阶段返回 `scan` 修改或撤销扫描补充时，我可以在重新输入前看到新输入会替换上一版扫描补充、直接回车会清空上一版补充，并在清空后看到系统确认后续预览和资产将回到扫描基线，从而避免误以为旧补充仍会影响正式 Harness。

## 验收标准

1. 新增 integration 测试先失败：首次输入 `legacy` module / command / risk，最终确认阶段 `back -> scan` 后直接回车，当前 CLI 不包含替换 / 清空提示。
2. 修复后，返回 scan 时 CLI 输出 `扫描补充返回修改`，并包含“新输入会替换上一版扫描补充”和“直接回车会清空上一版补充”。
3. 修复后，返回 scan 直接回车时 CLI 输出 `扫描补充已清空`，说明后续预览和正式资产将按扫描基线继续。
4. `project-inventory.json`、`command-catalog.yaml`、`interaction-decisions.yaml`、project-context、verification sensor 和 init-summary 不包含旧 `legacy` 补充。
5. 不修改 schema、LLM、asset writer、benchmark 或 Runtime 契约。
6. 运行目标测试、相关 guided init tests 和 `scripts/test-fast.sh`。

## 决策与取舍

- 新增轻量 helper 判断 `GuidedScanOverrides` 是否包含实际补充，避免散落重复条件。
- `back -> scan` 只有在上一版 scan 补充非空时展示替换 / 清空提示；初次扫描补充为空时不制造额外噪音。
- 清空确认只在“上一版非空、最新为空”时展示；普通首次回车继续仍保持安静。
- 本轮只说明替换 / 清空语义，不实现逐项 diff preview。

## Assumptions / Risks

- 用户在最终确认阶段选择返回 `scan`，语义是重新填写扫描补充；因此直接回车应表达撤销上一版补充并回到扫描基线。
- 输出文案会略微增加 guided init transcript，但只在纠错路径出现，常规 happy path 不受影响。
- 如果未来需要累计多轮补充或部分删除，应另行设计 add / remove / diff 交互，不复用本轮的全量替换语义。
