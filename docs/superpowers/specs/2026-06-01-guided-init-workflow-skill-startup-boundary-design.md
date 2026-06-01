# Guided Init Workflow Skill 启动边界设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`src/harness_builder_agent/tools/interactive_init.py`、`src/harness_builder_agent/tools/init_summary.py`、`src/harness_builder_agent/tools/asset_writers/skills.py`、相关 guided init / skill writer tests、当前 git 状态。
- 按需未展开：`llm-contracts.md`、`sensor-and-gate-rules.md`、`architecture.md`；本轮不修改 LLM、benchmark、schema、模块边界或 Runtime 产物。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 启动说明与 README 产物树显式列出三类 Workflow Skill | 上轮 Gate / init North Star / 当前文档审查 | 用户在确认继续扫描前、以及查 README 产物树时，都能知道首次 init 会生成 `lightweight`、`bugfix`、`standard` 三类 Workflow Skill | Workflow 确认阶段、写入前 preview、writer 和测试已覆盖三类 Skill；README 正文也描述三类 Skill | 启动说明只泛称 Workflow Skills；README `.ai/` 树只列 `lightweight` 和 `bugfix`，漏了 `standard`，与当前产物和 North Star 不一致 | 让用户在启动前理解本次会生成的工作流基线，也修正文档事实源漂移 | 低；只改 CLI 启动文案和 README 树 | guided init integration transcript、README diff、existing skill writer test | 无外部凭证 | 启动说明包含三类 Skill 名；README 树包含 `.ai/skills/standard/SKILL.md`；fast regression 通过 | 本轮 |
| B. 返回 scan 后重新审查 LLM enhancement candidates | 当前代码审查 | 用户修改 scan 后，后续候选审查完全基于更新后的 inventory / commands | 返回 scan 会重算 weapon selection 和 candidate report | 目前不自动重跑 candidate review，旧 candidate decisions 可能保留；但当前 candidate report 主要来自基础 LLM proposal，实际漂移风险需进一步拆解 | 保护渐进式交互一致性 | 中；会改变交互轮次和多个 transcript | guided init back-to-scan integration | 需确认 UX 是否应强制重审 | 新增返回 scan 后候选重审测试 | 下一轮候选 |
| C. full regression / push 工作包 | 用户提醒 / Git 状态 | 完整工作包同步 GitHub | 本地 ahead 72，最近 fast 通过 | `scripts/test-full.sh` acceptance 因缺 `DEEPSEEK_API_KEY` 和 `.benchmarks/RuoYi-Vue` / `.benchmarks/eShopOnWeb` 失败，不能合规 push | 远端同步本地独立价值 | 外部环境阻塞 | `scripts/test-full.sh` + `git push` | DeepSeek key 和真实仓库 | full 通过后 push | 本轮完成后评估 |

排序结论：

1. 选择 A。它紧接上一轮补齐 `standard` Workflow 确认，属于同一条“用户理解三类 Workflow 基线”的体验闭环，且修正文档事实源漂移。
2. B 暂不选，因为它可能改变交互轮次，风险和验收面更大，适合独立 Gap Analysis 深挖。
3. C 不作为功能 milestone，但本轮完成后按仓库规则评估 push；若 full regression 仍因外部前置失败，则不 push。

本轮用户故事：

作为 Harness Maintainer，当我刚运行首次 guided `init` 并看到启动说明或查阅 README 的 `.ai/` 产物树时，我可以明确知道本次会生成 `lightweight`、`bugfix` 和 `standard` 三类 Workflow Skill，从而在继续扫描前就理解 Harness 会包含低风险、缺陷修复和高风险升级三条工作流基线。

## 设计

- 更新 `_show_guided_init_startup_boundary()`：
  - 把“Workflow Skills”从泛称改为 `lightweight`、`bugfix`、`standard` 三类 Skill。
  - 保留不会执行 Runtime、不会创建 `.ai/task-runs`、确认前不写正式资产等边界。
- 更新 README `.ai/` 产物树：
  - 在 `.ai/skills/` 下补齐 `standard/SKILL.md`。
- 更新 guided init integration 测试，先 RED 证明启动说明缺少三类 Skill 名。
- 不修改 writer、Skill 模板、schema、benchmark 或 Runtime。

## 非目标

- 不新增 Workflow 类型。
- 不修改 `harness-config.yaml` routing policy。
- 不改变写入前 preview、completion summary 或 existing Harness 维护入口。
- 不执行 Runtime、不创建 `.ai/task-runs`。

## 验收标准

- RED：guided init startup integration 先证明启动说明没有 `lightweight` / `bugfix` / `standard` 三类 Skill 明细。
- 实现后 startup transcript 在用户确认继续前包含三类 Skill 名。
- README `.ai/` 树包含 `standard/SKILL.md`。
- skill writer regression 继续证明三类 Skill 实际生成。
- `compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：启动说明应保持短，但列出三类 Workflow Skill 是稳定产品边界，不是临时细节。
- Risk：启动说明过长；本轮只改一条产物说明，不展开 Skill 阶段细节，详细关系仍在后续 Workflow 确认和写入前 preview。
- Risk：README 树仍不是完整 `.ai/` 清单；本轮只修正当前明确遗漏的 `standard/SKILL.md`。

## Sub Agent

按目标模式尝试启动只读 explorer 审查启动说明与 README 产物树缺口，当前环境返回 `agent thread limit reached`。主线程继续完成调研、TDD、实现和验证。
