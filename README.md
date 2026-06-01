# Harness Builder

Harness Builder 是一个面向既有代码库的 AI Coding Harness POC。当前仓库提供 `harness-builder-agent` CLI，用来生成项目级 `.ai/` Harness、Workflow Skills、Guides、Sensors、成熟度评估和改进候选。

当前仍是 POC，不是生产级产品。

## 工程规则文档

本仓库使用 Codex 进行开发，项目级约束入口是 `AGENTS.md`。详细工程规则放在 `docs/engineering/`，按任务渐进式加载：

- `docs/engineering/architecture.md`：架构边界和模块职责。
- `docs/engineering/init-workflow.md`：`init` 工作流、生成产物和失败行为。
- `docs/engineering/llm-contracts.md`：DeepSeek、LLM-first 扫描、schema 和 no fallback 规则。
- `docs/engineering/testing-strategy.md`：测试分层、断言深度和 acceptance 策略。
- `docs/engineering/sensor-and-gate-rules.md`：Sensor、hard gate 和 benchmark 质量门禁规则。
- `docs/strategy/goal-mode-playbook.md`：目标模式运行手册，沉淀每轮读取顺序、todo 优先、milestone 粒度、sub agent 使用、commit / push 节奏和精简目标提示词模板。

## 环境准备

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[test]"
```

真实 DeepSeek 扫描验收使用本地 `.env`，不要提交：

```bash
DEEPSEEK_API_KEY=你的 DeepSeek API Key
HARNESS_BUILDER_LLM_PROVIDER=deepseek
HARNESS_BUILDER_LLM_BASE_URL=https://api.deepseek.com
HARNESS_BUILDER_LLM_MODEL=deepseek-v4-pro
```

## Agent CLI

核心命令：

```bash
.venv/bin/harness-builder-agent init --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent assess --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent improve --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent self-improve --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent recommend-workflow --repo tests/fixtures/mini-spring-boot --task-brief "Fix checkout permission bug." --task-id task-1
.venv/bin/harness-builder-agent review-candidate --repo tests/fixtures/mini-spring-boot --candidate-id guide-project-context-scope --decision accepted --rationale "Reviewed by Harness Maintainer."
.venv/bin/harness-builder-agent review-human-input --repo tests/fixtures/mini-spring-boot --interaction-id confirm:scan-followup:test-evidence --decision resolved --rationale "Reviewed by Harness Maintainer."
.venv/bin/harness-builder-agent benchmark --repo tests/fixtures/mini-spring-boot --profile java-spring
```

`init` 默认是本地人机引导式向导。它会用中文解释扫描发现，说明主要技术栈、模块、证据和验证命令，并在收集用户补充前分组展示风险区域、不确定性、验证缺口和建议补充，让 Maintainer 知道应优先确认哪些判断；如果扫描生成了深度追问或 LLM 二次自检，CLI 会继续展示“深度追问回答建议”，把每个追问映射到可用的自然语言说明或 `stack=<value>`、`module=路径|类型|名称`、`command=ID|命令|类型|gate|来源|置信度`、`risk=路径|原因` 示例。LLM 二次自检的每条 resolution 还会保留结构化 `suggested_action_type`，例如 `provide_stack`、`provide_module`、`provide_command`、`provide_risk`、`review_current_evidence`、`run_targeted_scan` 或 `maintainer_review`，CLI 会把它翻译成对应的补充格式或人工复核提示。用户可以输入自然语言补充，或用这些结构化片段修正关键扫描结论。结构化片段格式不完整或字段非法时，CLI 会明确说明它没有进入 project inventory、command catalog 或 risk hints，只作为自然语言补充保留，并给出对应可用格式提示。随后会收集团队代码规范、架构约束、测试策略等团队规则，逐项展示 Guide / Sensor 候选，说明推荐 Workflow；推荐 Workflow 阶段会在收集 Workflow 补充前同时解释 `lightweight`、`bugfix` 和 `standard` 三类工作流，其中 `standard` 用于复杂、高风险、跨模块、安全 / 数据或影响不清任务的升级路径。之后会在写入前展示当前 Harness 成熟度初评、写入后预计建立的基线、下一目标、主要阻断项、推荐补齐动作，以及扫描补充约束、待确认与低置信度边界、团队规则约束、Workflow 补充约束、Guides / Sensors / Workflow Skills / Workflow routing 设计预览；待确认边界会摘要展示 scan follow-up、LLM 二次自检、scan warning 和低置信度验证命令，并说明确认写入不会自动关闭追问、不会把低置信度内容伪装成已验证事实，也不会创建 `.ai/task-runs`；Workflow Skills 预览会展示 `lightweight`、`bugfix`、`standard` 的 Skill 路径、关键阶段、对应 routing rule 以及引用的 Guides / Sensors；Workflow routing 预览会复用正式 `harness-config.yaml` 的构造逻辑，展示当前扫描风险或用户补充风险进入 `standard-escalation` 的 `risk_area:*` 触发条件。摘要阶段可以输入 `back`/`返回` 返回修改，也可以输入 `confirm`/`确认` 写入资产，或输入 `cancel`/`取消` 取消；返回目标支持 `scan`/`扫描`、`rules`/`团队规则`、`candidates`/`候选` 和 `workflow`/`工作流`，返回 `scan` 修改扫描理解后会刷新并重新审查基于新扫描状态生成的候选。写入完成后的终端摘要会先展示当前成熟度、建议下一步、Benchmark 健康度和优先查看入口，再用核心机器契约、语义控制资产、审查 / 经验资产和运行审计入口概览本次生成结果，并用条数、示例、结构化来源和事实边界摘要展示本次吸收的 scan / team / Workflow 用户补充，完整细节仍保留在 `.ai/init-summary.md`、`.ai/runs/*/artifacts.yaml` 与 `.ai/interaction-decisions.yaml`。

如果 guided `init` 只发现 `.ai/project-inventory.json` 或 `.ai/harness-config.yaml` 中的一部分 core 文件，启动说明会在第一次确认前标出不完整 Harness 状态、已存在 / 缺失文件，并说明本次不会进入已有 Harness 维护入口；继续后按首次 init 扫描，最终确认前仍不会覆盖正式 Harness 资产。

guided `init` 在启动确认或最终写入确认前取消时，会输出中文取消摘要并以 failed trace 结束。trace summary 会记录 `cancel_stage` 和 `scan_completed`；如果已经完成扫描并进入写入前预览，还会记录 `primary_stack` 和 `command_count`，便于审计这次未写入的会话已经走到哪一步。

guided `init` 如果在扫描阶段因为 DeepSeek / LLM 配置、网络或 schema 失败而中断，会输出短错误摘要、说明未写入正式 Harness 资产，并以 failed trace 结束。trace summary 会记录 `scan_completed=false` 和 `formal_assets_written=false`，不会把多行底层错误或原始 Python traceback 当作主要 CLI 输出。

自动化、测试、CI 或 acceptance 场景必须显式使用非交互模式：

```bash
.venv/bin/harness-builder-agent init --non-interactive --repo tests/fixtures/mini-spring-boot
```

`--non-interactive` 不展示 guided 扫描进度，但扫描阶段如果因为 DeepSeek / LLM 配置、网络或 schema 失败而中断，会输出短错误说明、标出 `scan` 阶段和错误类型，记录 failed trace，并明确未写入正式 Harness 资产；trace summary 同样会记录 `scan_completed=false` 和 `formal_assets_written=false`，不会回退成确定性扫描成功结果。

`init` 会在目标仓库生成 `.ai/`：

```text
.ai/
  project-inventory.json
  command-catalog.yaml
  harness-config.yaml
  scan-metadata.yaml
  llm-scan-proposal.json
  weapon-library-selection.yaml
  interaction-decisions.yaml
  init-summary.md
  guides/
  sensors/
  skills/
    lightweight/SKILL.md
    bugfix/SKILL.md
    standard/SKILL.md
  maturity-report.md
  maturity-score.yaml
  maturity-evidence.yaml
  evolution-plan.md
  experience/experience-index.yaml
```

`init-summary.md` 是首次初始化后的入口摘要，按成熟度框架说明当前等级、主要阻断项、建议下一步、待人工确认、Benchmark 健康度和优先查看的文件。`## 待人工确认` 会列出 `questionnaire.yaml` 中的前几个 `confirm:*` ID，并指向 `.ai/human-input-needed.md#处理方式`；scan warning 类确认项还会展示对应的 `scan_warning_action:<code>` 处理提示，scan follow-up 类确认项会在处理方式中保留具体回答建议，例如补充 `stack`、`module`、`command` 或 `risk` 示例，并继续说明这些补充不会自动关闭人工复核。首次 `init` 不默认运行 benchmark；摘要和 CLI 完成输出会显示 `benchmark_status=not_run`、`quality_status=not_available` 和建议执行的 `harness-builder-agent benchmark --repo <repo>` 命令，CLI 完成输出的 `建议下一步` 会优先提示运行 benchmark 或处理 failed checks，再提示处理 human-input 待确认，避免把“资产已生成”误解为“质量门禁已通过”。

再次运行默认 guided `init` 时，如果目标仓库已经存在 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml`，CLI 会先进入已有 Harness 维护入口，展示当前成熟度、benchmark 和人类可读的维护状态摘要，然后先把 top actions 翻译成中文 `Maintenance triage guidance`，并展示 `Maintenance action shortcuts`，把每条推荐动作映射到可输入的编号；之后再展示 `Audit signals` 审计明细，包括分项 Benchmark signals、Workflow routing signals、Experience / review signals 和只读 Maintenance triage raw lines。这样 Maintainer 第一眼先看到该运行哪个维护动作，`benchmark_failed_checks=`、`routing_default=`、`pending_improvements=` 等 raw signals 仍保留用于审计、测试定位和报告溯源。维护状态摘要会用中文解释质量门禁是否未运行 / failed / passed、Workflow routing 是否具备 standard escalation 和 risk trigger、Experience / review 是否有候选或待确认积压，以及 triage 第一动作对应的菜单编号。human-input-needed 信号会通过 `Questionnaire` schema 展开为待确认总数、scan 类确认数量、scan follow-up resolved / partially addressed / unaddressed 计数、前几个 interaction id 和 `.ai/human-input-needed.md#处理方式` 入口；`human-input-needed.md` 也会按 `## 扫描待确认摘要`、`## 待确认问题` 和 `## 处理方式` 组织处理建议。Maintenance triage 会把这些结构化信号排序成最多 3 条下一步动作，例如先运行 `benchmark`、处理 `review-candidate`、运行 `review-initial-candidate` 治理初始 LLM enhancement candidate 的成熟度影响、运行 `review-human-input` 复核未解决 scan follow-up，或从 workflow recommendation 进入 `improve`；hard gate 命令证据失败会优先显示为 `reason=hard_gate_command_evidence` 并附带 command id、reason 和 source detail；scan-report 或 init-summary 证据审计失败会显示为 `reason=scan_evidence_audit_incomplete` 并附带第一条 missing detail。初始 LLM enhancement candidate 是独立的 review-only 维护对象，入口会指向 `.ai/review/llm-enhancement-candidates.md` 和 `.ai/experience/weapon-library-candidates.yaml`，不会复用 `review-candidate` 的 asset candidate 治理语义，也不会自动写入正式 Guide 或 Sensor；选择 `review-initial-candidate` 只会记录 `accepted` / `rejected` / `kept` 决策、更新 candidate report 状态并写入 `.ai/review/weapon-candidate-governance.*`。默认输入仍是 `1` 只读退出，不会自动执行推荐动作。可选动作用编号菜单展示；用户可以输入编号，也可以输入英文命令或常见中文别名。当前可选动作包括 `1. exit` 只读退出、`2. assess` 复评成熟度并刷新 maturity / init summary 产物、`3. improve` 基于成熟度缺口生成 review-only 改进候选、`4. benchmark` 运行质量门禁并刷新 benchmark / maturity / improvement 派生产物、`5. recommend-workflow` 输入任务说明并生成 review-only Workflow 推荐、`6. review-candidate` 记录候选 `accepted` / `deferred` / `rejected` 治理决策或显式应用单个 Guide / Sensor 候选、`7. review-human-input` 处理 scan follow-up 的 `resolved` / `reopened` 人工复核治理、`8. self-improve` 生成 review-only 自改进审查包、`9. reinit` 显式重新扫描生成，以及 `10. review-initial-candidate` 记录初始 LLM Guide / Sensor 候选 `accepted` / `rejected` / `kept` 决策。选择 `reinit` 后会回到首次 init 流程，但 CLI 会先说明这是重新生成现有 Harness，接下来会重新扫描，最终 `confirm` / `确认` 前不会覆盖现有正式 Harness 资产；如果在继续扫描前取消，会明确说明未重新扫描、未覆盖正式资产、未创建 Runtime 产物。`benchmark` 维护动作不覆盖正式 Guides、Sensors、Workflow Skills、配置或 inventory；如果质量门禁失败，会在输出、trace 和 `.ai/benchmark-report.yaml` 中显式展示失败项。`recommend-workflow` 维护动作会刷新最新 `.ai/review/workflow-routing-recommendation.*`，同时追加 `.ai/review/workflow-routing-recommendations/` 历史索引和摘要，让 Experience / Maturity 识别多次任务路由建议；维护入口会优先从 history index 展示最新 recommendation 的 task、workflow、risk、review status 和 source，旧 Harness 没有 history index 时兼容 latest 文件；它不执行任务、不创建 `.ai/task-runs`、不修改正式 routing policy。guided `review-candidate` 的 `applied` 只支持 Guide / Sensor Markdown 单候选应用，并在输入决策前展示 target、append mode、重复 marker 状态和 unified append diff 预览；应用后会记录 governance 和 applied path。guided `review-human-input` 只更新 `.ai/questionnaire.yaml`、`.ai/human-input-needed.md` 和 `.ai/review/human-input-governance.*`，不修改正式 Harness 资产，也不创建 Runtime 产物。guided `review-initial-candidate` 只更新 `.ai/experience/weapon-library-candidates.yaml`、`.ai/review/llm-enhancement-candidates.md`、`.ai/review/candidate-guides.md`、`.ai/review/candidate-sensors.md` 和 `.ai/review/weapon-candidate-governance.*`，不修改正式 Harness 资产，也不创建 Runtime 产物。`workflow_policy` 应用仍需使用专家命令和结构化 patch 审核。`self-improve` 是显式 LLM 智能改进动作，会刷新 maturity review、asset candidates 和 self-improve package，但仍保持 review-only，不执行 Runtime 或应用正式资产。CI 或脚本需要失败退出码时仍应直接调用 standalone `benchmark` 命令。

`reinit` 最终确认并完成重新生成时，trace summary 会保留 `existing_harness_action=reinit`，同时 CLI 仍会展示 `== 初始化完成 ==` 交付摘要；其他已有 Harness 维护动作不会追加首次初始化交付摘要。

`reinit` 在继续扫描前取消时，trace summary 会记录 `cancel_stage=startup_confirmation` 和 `scan_completed=false`；在扫描和写入前预览之后取消时，会记录 `cancel_stage=prewrite_confirmation`、`scan_completed=true`、`primary_stack` 和 `command_count`，同时保留 `existing_harness_action=reinit`。

`reinit` 在继续扫描后如果因为 DeepSeek / LLM 配置、网络或 schema 失败而中断，会按扫描阶段失败处理：CLI 会说明未写入正式 Harness 资产，trace summary 会保留 `existing_harness_action=reinit`、`scan_completed=false`、`formal_assets_written=false`、`error_type` 和 `scan_error`，正式 Guides、Sensors、Workflow Skills、配置和 inventory 不会被覆盖，也不会创建 Runtime 产物。

如果已有 Harness 的 `.ai/project-inventory.json`、`.ai/harness-config.yaml` 或已存在的 `.ai/maturity-score.yaml` 损坏，guided `init` 会在进入维护菜单前明确报告读取失败和具体文件，并说明未重新扫描、未覆盖正式资产、未创建 Runtime 产物。

guided `review-human-input` 如果来自 human-input triage，会默认填入首个待处理 scan follow-up interaction id，Maintainer 仍可输入其他 id 覆盖；该默认值只是降低复制成本，不会自动关闭追问或修改正式 Harness 资产。

Harness Builder 不提供任务级 `run` 命令。真实 AI Coding 工具执行 Workflow Skill 时，应按 Skill 中的 runtime artifact contract 生成任务级可观测产物：

```text
.ai/task-runs/demo-task-001/
  harness-map.yaml
  sensor-report.yaml
  runtime-summary.yaml
  workflow-events.jsonl
  used-guides.yaml
  decision-log.md
  handoff-summary.md
  experience-candidates.md
```

这些 Runtime 产物仍由宿主 AI Coding Runtime 生成，Harness Builder 不主动创建或执行它们。若 `.ai/task-runs/<task-id>/` 已存在，Builder 会在 `benchmark`、Experience index、maturity evidence、`assess` 和 `summarize-experience` 中只读消费：校验 `harness-map.yaml`、`sensor-report.yaml`、`runtime-summary.yaml`、`decision-log.md` 和 `handoff-summary.md` 的结构与一致性，并把 sensor failed / skipped、repair attempts、handoff 摘要作为后续 Experience / Self-Improve 的证据。缺少 `.ai/task-runs` 不会让 benchmark 失败；存在但 schema 或跨文件一致性错误会让 benchmark 显式失败。成熟度评估会把全部 resolved 的 Runtime sensor 结果作为 Workflow-bound L3 的运行证据；failed / skipped / unresolved sensor 会作为真实成熟度 blocker，而不是被当作 Builder 产物校验失败。

`assess` 更新成熟度评估，`improve` 生成待确认改进候选，`review-maturity` 对候选做 LLM review，`generate-asset-candidates` 生成 review-only Guide / Sensor / workflow policy 候选并刷新 Experience index 与 maturity evidence，`self-improve` 串联成熟度评估、改进候选、LLM maturity review 和 review-only asset candidates，生成 `.ai/review/self-improve-package.*`。guided `init` 中的 Workflow 补充会先进入 `interaction-workflow-note-review` 改进候选；后续 LLM review / asset candidate generation 可以把它转成带结构化 `WorkflowPolicyPatch` 的 review-only `workflow_policy` 候选，但不会直接修改 `.ai/harness-config.yaml`。`self-improve` 不应用正式 Harness 变更，不执行 Runtime workflow，也不创建 `.ai/task-runs`。

`review-candidate` 是 Harness Maintainer 的显式候选治理动作。它读取 `.ai/review/asset-candidates.yaml`，把某个候选记录为 `accepted`、`deferred`、`rejected` 或 `applied`，并写入 `.ai/review/candidate-governance.*`。`applied` 支持 Guide / Sensor Markdown 候选追加到正式 `.ai/**/*.md` 资产；`workflow_policy` 候选必须来自 `support` 或 `revise` 的 maturity review，必须提供结构化 `workflow_policy_patch`，只能通过 schema 校验后更新 `.ai/harness-config.yaml` 的 routing rule，并会保持原 routing rule 顺序、刷新成熟度证据。`defer`、`missing` 或非 `.ai/harness-config.yaml` 目标的 `workflow_policy` 候选不能应用为正式 routing policy。

`review-human-input` 是 Harness Maintainer 的显式人工输入治理动作。它只支持治理 `.ai/questionnaire.yaml` 中已有的 `scan_followup_confirmation`，可以把追问标记为 `resolved` 或 `reopened`，写入 `.ai/review/human-input-governance.*` 并刷新 `.ai/human-input-needed.md`。`resolved` 表示 Maintainer 已人工复核该追问，不表示 Builder 自动重扫或验证了事实；该命令不修改正式 Guides、Sensors、Workflow Skills、`harness-config.yaml`、inventory、command catalog，也不创建 Runtime 产物。

`benchmark` 会检查 Harness 资产文件存在、schema、内容质量、Workflow Skill 引用、review-only 智能改进产物、candidate governance 产物、初始 LLM candidate governance 产物、可选 Runtime task-run 产物、human-input 处理方式、scan report evidence visibility、init summary evidence audit、project-context evidence context、scan risk context 一致性和 hard gate command 证据。`.ai/human-input-needed.md` 必须保留稳定章节、`.ai/human-input-needed.md#处理方式`、scan follow-up 具体回答示例、`review-human-input` 显式治理命令，以及不自动关闭追问、不伪装成已验证 evidence、不创建 `.ai/task-runs` 的边界；缺失时 `content:human-confirmation` 会报告具体 `missing` detail。`.ai/scan-report.md` 必须展示 Evidence、LLM Evidence Expansion、Evidence Coverage、Stack Evidence Validation、Scan Warnings、Risk Areas 和 Command Candidates；缺失时 `content:scan-report` 会报告缺少章节、evidence path、evidence reason、coverage selected path、evidence expansion detail、warning、risk 或 command confidence。`.ai/init-summary.md` 必须在 `## 扫描证据审计` 中摘要展示 evidence expansion requested/read paths、risk focus、confidence、read file count、rationale 和 coverage selected paths；缺失时 `content:init-summary` 会报告 `missing_summary_expansion_*` 或 `missing_summary_coverage_selected_path:*`。`.ai/guides/project-context.md` 必须在 `## 来源证据` 中保留 inventory evidence、文档、配置和 CI 路径及其 reason，并在 `## LLM 证据扩展` 中保留 evidence expansion 的 requested/read paths、risk focus、confidence、read file count 和 rationale；缺失时 `content:project-context-evidence-context` 会报告 `missing_evidence_path:<path>`、`missing_evidence_reason:<path>`、`missing_llm_evidence_expansion_section` 或 `missing_expansion_*`。`.ai/experience/weapon-library-candidates.yaml` 中的初始 LLM Guide / Sensor 候选可以处于 `candidate`、`confirmed` 或 `rejected`；benchmark 会校验 summary / type-specific Markdown 中的候选 id、当前 status 和 review-only 边界。如果 `.ai/review/weapon-candidate-governance.yaml/.md` 存在，`content:weapon-candidate-governance` 会校验治理日志 schema、Markdown 配对章节、candidate id / type 引用、decision 到当前 status 的一致性和 `review_only_no_formal_asset_change` 边界。Guide、Sensor、Workflow Skill 和 stack-specific Guide 的内容质量检查失败时，`content:guides-quality`、`content:sensors-quality`、`content:workflow-skills` 和 `content:stack-specific-guides` 必须保留具体 `missing` detail，例如缺失章节、缺失 Skill marker 或缺失 weapon id。扫描风险路径必须同时出现在 `.ai/guides/project-context.md`、`.ai/sensors/verification.md` 和 `.ai/harness-config.yaml` 的 standard escalation routing 中；缺失时 `content:risk-context-consistency` 会报告 `missing_project_context_risk:<path>`、`missing_verification_sensor_risk:<path>` 或 `missing_routing_risk:<path>`。hard gate command 不只需要声明 source 和 confidence；source 还必须指向目标仓库内真实存在的文件。source 为空、low confidence、source path 不存在或逃出仓库时，`content:hard-gate-command-evidence` 会失败，并在 `weak_commands.reason` 中标出 `missing_source`、`low_confidence`、`source_path_missing` 或 `source_path_outside_repo`。

`benchmark-report.yaml` 中：

- `status` 表示硬验收是否通过，缺文件、schema 错误、Workflow Skill 引用错误或 hard gate command 证据不足会让它变成 `failed`。
- `quality_status` 表示质量评分结论：`passed`、`degraded` 或 `failed`。
- `quality_scores` 给出 scan、guide、sensor、workflow 的分项评分、原因和建议。

## 真实开源仓库验证

真实仓库放在 ignored 的 `.benchmarks/` 下：

```bash
mkdir -p .benchmarks
git clone --depth 1 https://github.com/yangzongzhuan/RuoYi-Vue.git .benchmarks/RuoYi-Vue
git clone --depth 1 https://github.com/dotnet-architecture/eShopOnWeb.git .benchmarks/eShopOnWeb
```

运行完整链路：

```bash
.venv/bin/harness-builder-agent init --non-interactive --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent assess --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent improve --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent self-improve --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/RuoYi-Vue --profile java-spring

.venv/bin/harness-builder-agent init --non-interactive --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent assess --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent improve --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent self-improve --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/eShopOnWeb --profile dotnet-aspnet
```

## 测试

```bash
scripts/test-unit.sh
scripts/test-integration.sh
scripts/test-guided-init.sh
scripts/test-llm-contracts.sh
scripts/test-fast.sh
scripts/test-acceptance.sh
scripts/test-acceptance-llm-smoke.sh
scripts/test-acceptance-real-repo.sh
scripts/test-acceptance-self-improve.sh
scripts/test-full.sh
```

`scripts/test-fast.sh` 运行快速回归测试，不包含 `tests/acceptance`，适合本地 Git hook、CI 默认验证和开发过程中的快速反馈。

`scripts/test-unit.sh`、`scripts/test-integration.sh`、`scripts/test-guided-init.sh` 和 `scripts/test-llm-contracts.sh` 是常用开发切片，只用于缩短开发反馈，不能替代 `scripts/test-fast.sh` 或 `scripts/test-full.sh`。

`scripts/test-acceptance.sh` 会实际请求 DeepSeek，并运行真实开源仓库验收；没有 `DEEPSEEK_API_KEY` 或缺少 `.benchmarks/` 真实仓库会失败，不会跳过。

开发时可以把 pytest 目标透传给 acceptance 脚本，只运行当前相关的真实链路，例如：

```bash
scripts/test-acceptance.sh tests/acceptance/test_real_repositories_e2e.py::test_ruoyi_vue_real_repository_with_self_improve
```

也可以使用 `scripts/test-acceptance-llm-smoke.sh`、`scripts/test-acceptance-real-repo.sh` 或 `scripts/test-acceptance-self-improve.sh` 运行命名好的真实验收切片。targeted acceptance 只用于缩短开发反馈；推送或发布前仍以 `scripts/test-full.sh` 为准。

`scripts/test-full.sh` 先运行 fast，再运行 acceptance，适合发布前、目标模式完成前或扫描/LLM/真实仓库验收相关改动后执行。

## 本地提交保护

安装仓库内置 Git hooks：

```bash
scripts/install-git-hooks.sh
```

安装后：

- `pre-commit` 会在提交前运行 `scripts/test-fast.sh`，作为快速兜底。
- `post-commit` 会提醒推送前本地 full regression 边界；不会要求 push 后等待 GitHub Actions。
- `pre-push` 会在推送前运行 `scripts/test-full.sh`，包含真实 DeepSeek 和真实开源仓库验收。
- `scripts/check-ci.sh` 保留为人工需要时的手动 GitHub Actions 查询工具，不是 push 后阻塞步骤。

Codex 侧的规则写在 [AGENTS.md](/Users/anhui/Documents/myProgram/harness-builder/AGENTS.md)：创建 commit 前必须主动运行 `scripts/test-fast.sh`，push 前必须主动运行 `scripts/test-full.sh`；push 后不再把远端 CI 查询作为阻塞步骤。
