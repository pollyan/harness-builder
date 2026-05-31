# 本地独有 / 更细能力合并与迁移

## 状态

- 状态：open
- 优先级：high
- 发现日期：2026-06-01
- 相关命令：`git fetch origin`、`git merge-tree --write-tree HEAD origin/main`、`harness-builder-agent init`、`benchmark`
- 相关工程规则：`AGENTS.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/llm-contracts.md`
- 相关产品方向：`docs/strategy/init-north-star.md`、`docs/strategy/goal-mode-playbook.md`

## 背景

合并收敛前，本地 `main` 与 GitHub 远端 `origin/main` 已经分叉：

- 本地领先远端 61 个提交。
- 远端领先本地 30 个提交。
- 远端 30 个提交也集中在 guided `init`、scan 深度、LLM evidence plan、成熟度叙事、目标模式规则和扫描追问 / 自检等方向。

当前已经完成基线收敛：

- 最新 `main` 对齐 `origin/main`。
- 原本地 61 个提交保留在本地备份分支 `backup/local-61-before-migration`，用于后续按需查旧实现。
- reset 前未提交工作树保留在 `stash@{0}: local-worktree-before-origin-main-reset`，不作为主线合并对象。

直接把本地 61 个提交整体 merge 到最新远端，会产生较多冲突。`git merge-tree --write-tree HEAD origin/main` 预判显示核心冲突集中在：

- `src/harness_builder_agent/tools/interactive_init.py`
- `src/harness_builder_agent/tools/init_summary.py`
- `src/harness_builder_agent/tools/scan_repo.py`
- `src/harness_builder_agent/tools/scan_reconciler.py`
- `src/harness_builder_agent/tools/human_confirmation.py`
- `src/harness_builder_agent/tools/evidence_collector.py`
- `src/harness_builder_agent/tools/write_assets.py`
- `src/harness_builder_agent/tools/asset_writers/*.py`
- `tests/integration/test_init_on_fixture_projects.py`
- 多个 unit tests 和工程文档

这些冲突不是简单格式冲突，而是两边并行实现了同一条 `init` North Star 主线。因此不应机械合并全部本地提交。

## 问题

本地 61 个提交和远端 30 个提交存在明显重复：

- guided init 阶段 / 进度反馈。
- init 完成后的 CLI 交付摘要。
- init 资产仓库特异性。
- LLM evidence expansion / evidence plan 展示。
- scan 风险、关注点、人工确认和追问。

但本地也有一些远端尚未明确覆盖，或更细、更完整的能力：

- Existing Harness 维护入口：Maintenance triage top actions、中文 guidance、编号菜单、routing signals、benchmark failed preview、human-input-needed signals。
- Benchmark / quality gate 细化：risk context consistency、hard gate command evidence / source path / weak command detail、project-context evidence context gate、failed check missing / errors / detail preservation。
- Human input 闭环：`.ai/human-input-needed.md#处理方式`、`init-summary.md` 对齐 `confirm:*` ID、scan warning action hints、已有 Harness 入口展示确认项状态。
- Scan evidence 细节：test / risk / API entrypoint / document evidence reason、project-context evidence summary、LLM requested evidence 在 report 和 guide 中的可审计展示。

当前需要从 `backup/local-61-before-migration` 中把“本地独有 / 本地更细”的能力迁移到最新 `origin/main`，而不是把本地 61 个提交整包合入。

## 已迁移切片

- 2026-06-01：迁移 Existing Harness 维护入口的编号菜单、维护动作 normalization 和 `Maintenance triage guidance`。当前 guided `init` 在已有 Harness 入口支持输入 `1` 到 `8` 选择动作，并把 top maintenance actions 翻译成中文处理建议。
- 2026-06-01：迁移 Human Input 待确认回访入口。当前 `human-input-needed.md` 包含 `## 扫描待确认摘要` 和 `## 处理方式`，已有 Harness 维护入口会展示 questionnaire 状态、待确认总数、scan 类确认数量、前几个 interaction id 和 `.ai/human-input-needed.md#处理方式`。
- 2026-06-01：迁移 Existing Harness Benchmark / Workflow routing 只读信号。当前维护入口会展示 `Benchmark signals`、`Workflow routing signals`、benchmark failed check 中文解释、error / missing / weak command detail，以及 hard gate weak command / project-context evidence 专属 triage reason。
- 2026-06-01：迁移 Init Summary 待确认处理入口。当前 `init-summary.md` 包含 `## 待人工确认`，会列出前几个 `confirm:*` ID、`.ai/human-input-needed.md#处理方式` 入口和 scan warning action hint；CLI completion message 复用同一待确认摘要，benchmark `content:init-summary` 会校验章节、处理入口和 questionnaire ID 对齐。
- 2026-06-01：迁移 hard gate command source path benchmark 校验。当前 `content:hard-gate-command-evidence` 会检查 hard gate source 为空、low confidence、source path 不存在和 source path 逃出仓库，并在 `weak_commands.reason` 保留可行动原因。
- 2026-06-01：迁移 risk context consistency benchmark 校验。当前 `content:risk-context-consistency` 会检查 scan risk path 是否同时出现在 project-context Guide、verification Sensor 和 standard escalation routing 中；`write_initial_assets()` 会把扫描风险路径写入 `risk_area:<path>` trigger 和 routing rationale。
- 2026-06-01：迁移 project-context evidence context benchmark 校验。当前 `project-context.md` 会在 `## 来源证据` 保留 inventory evidence、文档、配置和 CI 路径，并在 `## LLM 证据扩展` 保留 evidence expansion 的 requested/read paths、risk focus、confidence、read file count 和 rationale；`content:project-context-evidence-context` 会报告缺失 evidence path、缺失 LLM evidence expansion 章节或缺失 expansion detail。
- 2026-06-01：迁移 scan report evidence visibility。当前 `scan-report.md` 会展示 Evidence、LLM Evidence Expansion、Evidence Coverage、Stack Evidence Validation、Scan Warnings、Risk Areas 和 Command Candidates；`content:scan-report` 会报告缺失章节、evidence path、coverage selected path、evidence expansion detail、warning、risk 或 command confidence。
- 2026-06-01：迁移 init summary evidence audit。当前 `init-summary.md` 会在 `## 扫描证据审计` 摘要展示 evidence expansion requested/read paths、risk focus、confidence、read file count、rationale 和 coverage selected paths；`content:init-summary` 会报告缺失章节、summary expansion detail 或 summary coverage selected path。

## 理想状态

以最新 `origin/main` 为基线，逐项吸收本地真正有增量价值的能力：

1. 保留远端已经实现且更系统的 guided `init`、maturity preview、scan followup / self-check 和 evidence plan 主结构。
2. 对重复能力，不做双实现并存；优先选择远端主线，再把本地更细的解释、schema、benchmark 或测试断言补进去。
3. 对本地独有能力，按小步 milestone 迁移，每次只迁移一个可验收用户故事或工程信任故事。
4. 每个迁移切片都必须有测试证明它在最新远端代码上真实工作，而不是只保留旧测试。
5. 迁移完成后，本地 61 个提交不再作为整体合并目标；未迁移且已被远端覆盖的提交可以放弃。

推荐迁移顺序：

1. **Existing Harness 维护入口独有能力**
   - Maintenance triage top actions。
   - Maintenance triage guidance。（已迁移：2026-06-01）
   - 编号菜单。（已迁移：2026-06-01）
   - routing signals。（已迁移：2026-06-01）
   - benchmark failed preview。（已迁移：2026-06-01，包含 failed check detail 与 hard gate weak command / project-context missing triage）
   - human-input-needed signals。（已部分迁移：2026-06-01，包含 questionnaire backlog status 与 action entry）

2. **Benchmark / quality gate 细化**
   - hard gate command evidence / source path / weak command detail。
     - 已部分迁移：2026-06-01（source 为空、low confidence、source path missing / outside repo 和 weak command reason；project-context gate 仍待后续）。
   - risk context consistency。
     - 已迁移：2026-06-01。
   - project-context evidence context gate。
     - 已迁移：2026-06-01。
   - failed check missing / errors / detail preservation。
     - 已部分迁移：2026-06-01（scan-report / init-summary evidence audit failed checks 有中文 label、missing detail 和专门 triage guidance；系统性全量审计仍待后续）。

3. **Human input 闭环**
   - `.ai/human-input-needed.md#处理方式`。
     - 已迁移：2026-06-01。
   - `init-summary.md` 与 questionnaire 的 `confirm:*` ID 对齐。
     - 已迁移：2026-06-01。
   - scan warning action hints。
     - 已迁移：2026-06-01（summary / CLI completion 复用；后续如需更细状态仍可继续扩展）。
   - Existing Harness 对 confirmation backlog 的显示和 triage。
     - 已迁移：2026-06-01（backlog 显示；triage 排序仍待后续评估）。

4. **Scan evidence 可审计细节**
   - evidence reason preservation。
   - test / risk / API entrypoint / document evidence report visibility。
     - 已部分迁移：2026-06-01（scan-report 通过 coverage selected paths、risk areas、documents/configs/CI 和命令置信度展示；更细顶层 inventory 字段仍不新增）。
   - LLM requested evidence 在 scan report、project-context 和 init summary 中的审计展示。
     - 已迁移：2026-06-01（scan-report、project-context 和 init-summary 已展示并由 benchmark 校验）。

## 非目标

本 todo 不要求：

- 直接 merge 本地 61 个提交。
- 保留两套 guided `init` 阶段输出或两套 completion summary。
- 逐字合并全部 `docs/superpowers/specs/` 和 `docs/superpowers/plans/` 历史过程文档。
- 为了保留本地实现而覆盖远端最新的 scan followup、自检、多栈表达、maturity preview 或目标模式规则。
- 一次性解决所有冲突。

## 初步验收标准

进入实施前，应先产出迁移清单：

- 本地 61 个提交按主题归类。
- 每个主题标注：远端已覆盖、远端部分覆盖、本地独有、本地更细、建议放弃。
- 明确第一批迁移 milestone，优先选择可独立验收的小切片。

每个迁移切片至少满足：

- 基于最新 `origin/main` 新分支实施。
- 只迁移一个清晰能力，不整包 cherry-pick 大量旧提交。
- 更新相关 schema / docs / tests。
- 对涉及 `init` 主链路的改动运行 targeted guided init tests 和 `scripts/test-fast.sh`。
- 如果影响 acceptance、真实 DeepSeek、真实仓库或 push，按 `AGENTS.md` 运行对应 full / acceptance 前置验证。

## 待澄清点

- 是否需要把部分本地过程文档归档，而不是迁移到远端。
- 远端新加的 `docs/strategy/goal-mode-playbook.md` 是否应成为后续目标模式的主要流程事实源。
- 本地 `Maintenance triage` 系列能力应整体迁移，还是拆成 benchmark signals、routing signals、human input signals 三个小切片。
- 本地 scan warning action hints 与远端 scan followup questions / self-check 应如何统一成一个人工确认模型。
