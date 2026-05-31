# Guided Init Scan 返回修改差异预览设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、近期 `docs/evolution-log.md`、`AssetCandidateDraft` / `WorkflowPolicyPatch` schema、guided init scan back 相关代码与测试。
- 按需未展开：`docs/engineering/llm-contracts.md`、`sensor-and-gate-rules.md` 和 `architecture.md`；本轮不修改 LLM、benchmark、Sensor 或架构边界。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. scan 返回修改差异预览 | 上轮 Gate / 新发现 | 用户返回 scan 输入新补充后，CLI 明确展示上一版补充被当前生效补充替换 | 已支持 clean baseline、替换语义、清空提示和最终资产只保留最新补充 | 有“上一版摘要”和“新补充理解”，但没有稳定的 old/new 对照区块；用户仍需自己比对 | 提升纠错路径信任感，保护正式资产写入前的可审查性 | 低；只改 guided CLI 文案和 integration 测试 | guided integration transcript、现有资产替换断言 | 无外部凭证 | CLI 有“扫描补充替换结果”，展示上一版 / 当前生效；最终资产无旧补充 | 本轮 |
| B. Workflow note review-only routing candidate | 上轮 Gate | Workflow note 可进入 review-only workflow policy candidate | Workflow note 和 team rules 已有结构化 review-only impact contract | `workflow_policy` candidate 要求结构化 `WorkflowPolicyPatch`；自由文本 note 不能安全推断 routing patch | 更强 Workflow Toolkit 闭环 | 中高；涉及 candidate schema、治理和 policy patch | candidate / governance integration | 需要明确 note 到 patch 的安全边界 | 生成 review-only candidate 且不改正式 routing | 后续候选 |
| C. push 前 full regression / 远端同步 | 工程节奏 | 完整工作包形成独立价值后 full + push | 本地领先远端 22 个 commit | 当前仍在连续目标模式小步演进，未形成本轮 push 边界 | 降低本地积压风险 | 中；依赖 acceptance、DeepSeek、真实仓库和网络 | `scripts/test-full.sh` | 可能缺凭证或 `.benchmarks` | full 通过后 push | 工作包完成后处理 |

排序结论：

1. 选择 A。它直接服务 `init-north-star` 中“用户补充后复述理解、支持错误恢复、写入前可审查”的 CLI 体验，风险小且能用现有 guided init 测试完整验收。
2. B 暂不选。当前 schema 要求 `workflow_policy_patch`，从自由文本 Workflow note 推断结构化 routing patch 会破坏“正式资产有风险时只生成候选并审核”的边界。
3. C 不作为本轮。push 应在完整工作包或独立 push 价值形成后执行，且需要 full regression。

本轮 milestone：

作为 Harness Maintainer，当我在最终确认阶段返回 `scan` 并用新模块、验证命令或风险区域替换上一版扫描补充时，我可以在 CLI 中看到稳定的“上一版补充 / 当前生效补充”差异预览，并确认最终写入只会使用当前补充，从而不用在长输出里手动比对旧输入是否仍然生效。

## 设计

### CLI 行为

当前已有：

- 返回 scan 前显示 `扫描补充返回修改` 和上一版补充摘要。
- 新输入非空时显示 `扫描补充理解` / `扫描补充影响`。
- 新输入为空时显示 `扫描补充已清空`。

本轮新增：

- 当 `back -> scan` 前存在上一版补充，且新输入也非空时，在新补充即时理解后输出：
  - `扫描补充替换结果`
  - `上一版补充：<previous brief>`
  - `当前生效补充：<current brief>`
  - `最终写入只会使用当前生效补充；上一版补充不会进入 project inventory、command catalog、Guides、Sensors 或 init summary。`

### 复用 helper

- 复用 `_scan_override_brief()` 生成简短摘要。
- 新增 `_show_scan_supplement_replacement_summary(previous, current)`，只在 previous 和 current 都有 overrides 时输出。
- 清空路径继续使用 `_show_scan_supplement_cleared_summary()`，不额外输出 diff。

## 决策与取舍

- 不实现结构化逐字段 diff 表格，避免把 CLI 变长；本轮用稳定 old/current 摘要满足写入前审查。
- 不改变 `GuidedScanOverrides` schema，也不改变正式 `.ai` 资产契约。
- 不修改 scan parser、LLM、writer 或 benchmark。
- 不改变 scan replacement 的资产语义；只是把已经存在的语义讲清楚。

## Assumptions / Risks

- Assumption：返回 scan 重新输入表达“替换上一版补充”，而不是累计追加。
- Risk：摘要过短可能不包含全部内容；已有 `_scan_override_brief()` 会截断 notes / modules / commands / risks，本轮保留截断，完整内容仍在紧邻的 `扫描补充理解` 区块展示。

## 验收标准

1. guided init 返回 `scan` 后输入新补充时，CLI 输出 `扫描补充替换结果`。
2. 替换结果中包含上一版补充摘要和当前生效补充摘要，至少覆盖 module、command、risk 和 note。
3. CLI 明确说明最终写入只使用当前生效补充，上一版不会进入 project inventory、command catalog、Guides、Sensors 或 init summary。
4. 既有资产断言继续证明旧补充不进入 `project-inventory.json`、`command-catalog.yaml`、project-context、verification sensor 或 init-summary。
5. 清空路径仍输出 `扫描补充已清空`，不要求输出替换结果。
6. 更新 `docs/engineering/init-workflow.md` 和 `docs/evolution-log.md`，记录稳定 CLI 语义。
