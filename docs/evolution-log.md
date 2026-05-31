# Harness Builder 演进记录

## 2026-05-31 Goal Mode Retrospective And Recommendation Contract Repair

- North Star 模块：Benchmark / Review Intelligence、Workflow Toolkit Evolution、Experience & Self-Improve。
- Gap Analysis 摘要：用户指出前几轮目标模式提示词不完整后，本轮回顾最近 8 个本地目标模式提交。主要遗漏是 evolution log 未显式记录 Self-Harness Gate、sub agent 使用和下一轮候选 gap；实质代码缺口是 `recommend-workflow` 真实生成的 Markdown 章节与 benchmark `content:workflow-recommendation-review` 契约不一致。
- 当前代码 gap：`recommend_workflow.py` 生成 `## Task Brief`、`## Required Guides`、`## Required Sensors`、`## Boundary`，而 benchmark 要求 `## Task`、`## Recommended Workflow`、`## Required Harness Assets`、`## Review Boundary`。这会导致工具自己生成的 review-only workflow recommendation 可能被 benchmark 拒绝。
- 决策：不放宽 benchmark；修 producer，使真实 `recommend-workflow` 产物满足现有质量门禁。暂缓 existing-Harness guided `benchmark` 菜单和候选治理菜单，先修 review artifact 契约可信度。
- Assumptions / risks：旧标题对人工阅读不是稳定机器契约；改为 benchmark 标准章节不改变 review-only 语义。更完整的逐提交审计可后续继续，但本轮先修最高确定性的契约问题。
- 边界与失败模式：recommendation 仍保持 `pending_harness_maintainer_review`，不执行 Runtime，不创建 `.ai/task-runs`，不应用 routing policy。
- Sub agent 使用：使用 explorer 子代理审查下一步 gap，结论同主线程一致：优先修 `recommend-workflow` 生成产物与 benchmark 契约不一致。
- 验收方式：integration 从 CLI 真实生成 `.ai/review/workflow-routing-recommendation.*`，再运行 benchmark 并断言 `content:workflow-recommendation-review` 通过；保留 benchmark 缺章节失败测试。
- Self-Harness Gate：本轮补齐了近期记录缺少 Gate 结论的问题；下一轮候选 gap 首选 existing-Harness guided `benchmark` action，其次是 candidate governance 菜单。

## 2026-05-31 Existing Harness Improve Action

- North Star 模块：CLI Experience、Maturity-driven Improve、Experience & Self-Improve、Maturity & Evolution。
- 当前 gap：已有 Harness 再次执行 guided `init` 时已能复评成熟度，但用户仍需记住底层 `improve` 命令才能把成熟度缺口转成下一步 review-only 改进候选。
- 决策：在已有 Harness 维护入口加入 `improve` 动作；先刷新 Experience index 和 maturity evidence，再生成 `improvement-candidates.yaml`、`evolution-plan.md`、`pending-improvements.md` 和 `experience-index.yaml`。
- 决策：`improve` 不重新扫描、不调用 LLM、不执行 `self-improve`、不应用候选、不覆盖正式 Guides、Sensors、Workflow Skills、`harness-config.yaml` 或 `project-inventory.json`。
- 验收方式：integration 覆盖 existing Harness 下 `improve` 不调用扫描、不覆盖正式资产、输出 top candidate、刷新 stale workflow recommendation evidence，并记录 trace artifacts 与 `existing_harness_action: improve`。

## 2026-05-31 Existing Harness Assess Action

- North Star 模块：CLI Experience、Maturity & Evolution、可观测 Harness 生成。
- 当前 gap：已有 Harness 再次执行 guided `init` 时只能退出或重建，普通用户仍需知道底层 `assess` 命令才能刷新成熟度。
- 决策：在已有 Harness 维护入口加入 `assess` 动作，复用成熟度评估能力刷新 `maturity-score.yaml`、`maturity-report.md`、`maturity-evidence.yaml` 和 `init-summary.md`。
- 决策：`assess` 不重新扫描、不调用 LLM、不覆盖 `project-inventory.json`、`harness-config.yaml`、Guides、Sensors 或 Workflow Skills。
- 验收方式：integration 覆盖 existing Harness 下 `assess` 可修复缺失 maturity 文件、不调用扫描、不覆盖正式资产，并记录 trace artifacts 和 `existing_harness_action: assess`。

## 2026-05-31 Existing Harness Init Entry

- North Star 模块：CLI Experience、Maturity & Evolution、资产生成与审核接管。
- 当前 gap：再次执行默认 guided `init` 时，系统还会直接进入生成流程，容易覆盖已有 `.ai` Harness，未体现“已有 Harness 的状态感知维护入口”定位。
- 决策：guided `init` 检测到 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml` 后先展示现有 Harness 状态；第一版动作支持 `exit` 只读退出和 `reinit` 显式继续生成。
- 决策：`--non-interactive` 保持自动化重新生成语义，不在本轮引入 `--force` 或完整维护菜单。
- 验收方式：integration 覆盖已有 Harness 下 `exit` 不调用扫描、不改写正式资产，并记录 trace summary。

## 2026-05-31 Maturity Driven Init Summary

- North Star 模块：Maturity & Evolution、CLI Experience、Benchmark / Review Intelligence。
- 当前 gap：`init` 已生成成熟度评估，但完成输出仍偏“文件已生成”，没有把当前等级、阻断项和下一步入口作为主向导体验呈现。
- 决策：新增 `.ai/init-summary.md` 作为首次初始化后的成熟度驱动入口摘要，并让 CLI 完成输出打印当前成熟度、阻断项、建议下一步和推荐入口文件。
- 决策：本轮不默认运行 benchmark / self-improve / Runtime task-run，也不实现已有 Harness 的再次 init 状态菜单；这些保留在主向导 todo 的后续切片。
- 验收方式：integration / e2e / benchmark 覆盖 init summary 文件、稳定章节、CLI 输出和 no-runtime 边界。

## 2026-05-31 Workflow Policy Candidate Apply And Prompt Registry

- North Star 模块：Workflow Policy、Candidate Governance、Prompt Contract。
- 当前 gap：`workflow_policy` asset candidate 已能被 LLM 提出，但此前只能记录治理决策，不能以机器契约应用到正式 routing policy；同时 prompt 文件虽已集中，prompt 版本、文件名和输入标题仍散落在 `tools/llm_*.py`。
- 决策：新增 `WorkflowPolicyPatch` schema，要求 `workflow_policy` candidate 必须携带结构化 patch；`review-candidate --decision applied` 只允许通过该 patch upsert routing rule，并校验 guide/sensor 引用和核心 routing invariants。
- 决策：新增 `prompts.registry` 作为机器消费型 LLM prompt 的单一注册表，集中管理 prompt 文件、版本、输入标题和消息构造；LLM 工具层不再直接维护 prompt 文件名或调用 loader。
- 验收方式：schema / unit / CLI / benchmark 测试覆盖 workflow policy patch 应用、非法 patch 拒绝、成熟度证据刷新、benchmark 保留已应用 config，以及 prompt registry 防回退。

## 2026-05-31 Candidate Governance MVP

- North Star 模块：Experience & Self-Improve、Maturity & Evolution、资产生成与审核接管。
- 当前 gap：`self-improve` 已能生成 review-only asset candidates，但缺少 Maintainer 将候选记录为 accepted / deferred / rejected / applied 的机器契约，智能建议无法进入可审计接管闭环。
- 决策：新增显式 `review-candidate` 命令和 `.ai/review/candidate-governance.*`；保持原始 LLM candidate report 为 review-only。`applied` MVP 只支持 Guide / Sensor Markdown 追加，workflow policy 自动 patch 暂缓到结构化 patch schema 后实现。
- 验收方式：schema / tool / CLI / benchmark 测试覆盖 governance log、正式 Markdown 应用、Experience index 计数、未知 candidate、`.ai/` 路径边界和 trace artifact。

## 2026-05-31 Self-Improve 真实验收覆盖

- North Star 模块：Maturity-driven Improve、LLM Maturity Reviewer、Intelligent Asset Candidate Generation、Benchmark / Review Intelligence。
- 当前 gap：`self-improve` 已有 mock integration 覆盖，但真实 DeepSeek acceptance 没有跑到该智能闭环，无法证明真实模型输出仍符合 review-only schema 与 benchmark 契约。
- 本轮切分：只在 `RuoYi-Vue` 一个真实仓库上增加 `self-improve` acceptance，保持独立用户价值，同时控制全量回归成本。
- 关键发现：真实 DeepSeek 曾返回合法 JSON 但漏掉 `AssetCandidateDraft` 必填字段 `id/title/rationale`，说明 prompt schema 约束不够完整。
- 关键发现：真实 DeepSeek 还暴露过 maturity review 阶段的无效 JSON 和空 `content` 响应。诊断显示正常响应会同时包含 `content` 与 `reasoning_content`，因此不能解析 reasoning 文本作为替代。
- 决策：保持 Pydantic schema 严格失败，不引入 fallback；通过单元测试固定完整 prompt 字段契约，收紧 maturity-review / asset-candidate prompt 的字段模板和输出规模；DeepSeek client 仅对空 `content` 做一次有限重试，仍失败则显式报错。
- 决策：将所有机器消费型 LLM prompt 集中迁入 `src/harness_builder_agent/prompts/`，并通过共享 loader 读取 `## System Message` / `## User Message`。`tools/llm_*.py` 只保留 payload 拼装、调用、解析和 schema 校验。
- 验收方式：unit 覆盖 prompt 契约，acceptance 覆盖真实 `self-improve` 产物 schema、review-only 状态、benchmark `content:self-improve-package` 检查和 `.ai/task-runs` 边界。
- 风险：真实 acceptance 仍有耗时和网络不稳定成本；开发中优先使用可透传 pytest 目标的 targeted acceptance，push 或发布前再运行 full acceptance。
