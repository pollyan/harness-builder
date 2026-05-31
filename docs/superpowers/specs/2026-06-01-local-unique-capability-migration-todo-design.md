# 本地独有 / 更细能力迁移 Todo 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`docs/todos/guided-init-ai4se-real-repo-findings.md`、`docs/todos/maturity-driven-init-wizard.md`、`docs/todos/local-unique-capability-migration.md`。
- 按需未展开：`docs/engineering/architecture.md`、`sensor-and-gate-rules.md`、完整测试文件。当前 milestone 只收敛 git / todo 工作基线，不修改架构、Sensor 或运行逻辑。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 合并基线收敛与迁移 todo 唯一入口 | 用户最新指令 / todo | `main` 对齐最新 `origin/main`，本地旧实现可回查，当前 open todo 只指向本地独有 / 更细能力迁移 | 已创建 `backup/local-61-before-migration`，`main` 已 reset 到 `origin/main`，迁移 todo 已从 stash 恢复 | 远端当前仍有两个 open todo，会让目标模式继续被旧大主题牵引；迁移 todo 需要记录备份分支和 stash 事实 | 先解决分叉和冲突策略，降低后续功能迁移风险 | 低，文档和 git 状态收敛；不改代码 | `rg` 检查 open todo；`git status`；`git diff --check`；fast 回归 | 需要本地备份分支和 stash 已存在 | 当前 `docs/todos` 只有迁移 todo 为 open；`main` 与 `origin/main` 对齐；文档记录备份与非目标 | 本轮 |
| B. 迁移 Existing Harness 维护入口独有能力 | 新迁移 todo | 最新远端基线上恢复 maintenance triage / routing signals / human input signals | 旧实现在备份分支存在，远端已有部分维护入口 | 需要代码迁移、测试重建和冲突消解 | 直接提升已有 Harness 可持续维护体验 | 中到高，触碰 `interactive_init.py`、triage、integration tests | targeted guided init tests、unit、fast | 依赖 A 先建立干净基线 | 在最新远端上重建一个纵向能力切片并测试通过 | 下一轮候选 |
| C. 迁移 benchmark / quality gate 细化 | 新迁移 todo | 最新远端具备 hard gate evidence、risk context、missing detail 等质量门禁解释 | 旧实现有较细 benchmark gate；远端未完全覆盖 | 需对齐远端 scan self-check / evidence plan 契约 | 提升 generated Harness 的验收可信度 | 中高，涉及 benchmark schema 与多测试 | benchmark integration、unit、fast | 依赖 A；最好在维护入口迁移后处理 | 新 gate 可在 fixture 上失败并给出可行动 detail | 后续候选 |

排序结论：

1. 选择 A，因为用户明确要求“先把合并的事情搞定，之后再做功能”。A 是工程信任故事：先把主线从 61/30 分叉状态收敛为最新远端基线，并把后续迁移入口变成唯一 open todo。
2. B 与 C 都有产品价值，但属于功能迁移。若在基线未收敛前推进，会重新进入大范围冲突和重复实现判断。

本轮 milestone：

作为 Harness Builder 维护者，当本地 61 个提交和远端 30 个提交已经并行演进且决定放弃整包 merge 时，我可以在最新 `origin/main` 基线上保留旧实现备份、把当前 open todo 收敛为“本地独有 / 更细能力迁移”，从而让后续目标模式只按小步迁移独有增量，而不是继续尝试合并两套实现。

## 关键决策 / 取舍

- `main` 以最新 `origin/main` 为事实基线。
- 旧本地 61 个提交只通过 `backup/local-61-before-migration` 保留，不再作为整体合并目标。
- reset 前未提交工作树保留在 `stash@{0}: local-worktree-before-origin-main-reset`，不自动恢复功能代码。
- `guided-init-ai4se-real-repo-findings.md` 和 `maturity-driven-init-wizard.md` 暂停为背景参考，避免和迁移 todo 并列 open。
- 本轮只做文档 / todo / 流程收敛，不迁移任何功能代码。

## Assumptions / Risks

- 备份分支是本地引用；如果后续换机器，需要显式推送或导出才可共享。
- `stash@{0}` 位置可能随后续 stash 操作变化；迁移 todo 同时记录 stash message，降低定位风险。
- 暂停旧 todo 不代表否定其产品价值，只是避免当前目标模式绕开迁移决策继续在旧分叉上推进。

## 可执行验收标准

- `git status --short --branch` 显示 `main...origin/main` 且工作树只包含本轮文档改动。
- `backup/local-61-before-migration` 存在。
- `docs/todos/README.md` 只列出 `local-unique-capability-migration.md` 为 open。
- `rg "状态：open|\\| .* \\| open \\|" docs/todos -g '*.md'` 只返回迁移 todo。
- `git diff --check` 通过。
- `scripts/test-fast.sh` 通过后创建本地中文 commit。

## Sub Agent 使用情况

未使用 sub agent。本轮是 git / 文档基线收敛，范围很小且不涉及并行代码调研；此前已通过 git 命令确认冲突和重复范围。
