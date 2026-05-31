# LLM 契约

本文约束 Harness Builder 中 LLM、DeepSeek、结构化输出和扫描调和相关逻辑。修改 LLM 扫描或下游消费逻辑前，先阅读本文。

## 基本立场

Harness Builder 的扫描策略是 LLM-first。

原因是企业代码库经常目录混乱、命名不规范、测试位置不统一。如果只依赖确定性脚本，会把“我们预设的标准仓库结构”误认为真实世界。

但 LLM-first 不等于让 LLM 任意写文件或跳过工程约束。LLM 负责分析和提出结构化判断，确定性程序负责 schema 校验、调和、落盘和测试。

## LLM 输出分类

### 机器消费输出

机器消费输出会被确定性程序读取和执行，必须严格结构化。

例子：

- LLM scan proposal。
- command candidates。
- stack classification。
- module list。
- risk areas。
- architecture signals。
- evidence expansion plan。
- maturity review report。
- asset candidate report。
- experience summary report。
- workflow recommendation report。

规则：

- 必须是 JSON 或可 schema 校验的数据结构。
- 必须进入 Pydantic schema。
- 解析失败必须失败。
- 缺字段、类型错误、非法枚举必须失败。
- 不能靠字符串搜索解析关键业务字段。

### 语义上下文输出

语义上下文输出主要给人或后续 LLM 作为上下文阅读。

例子：

- guide Markdown。
- sensor Markdown。
- scan report。
- maturity report。
- review candidate 文档。

规则：

- 可以使用 Markdown 和自然语言。
- 必须保留稳定章节。
- 必须区分事实、推断、建议和待确认项。
- 重要结论应尽量带来源证据。

## DeepSeek 配置

真实 LLM 扫描当前使用 DeepSeek。

规则：

- 默认不在代码中硬编码 API key。
- API key 来自本地 `.env` 或环境变量。
- `.env` 不允许提交。
- base URL、model、timeout 应由统一配置模块读取。
- acceptance 测试需要 DeepSeek 时，缺少 key 必须失败，不能 skip。

## 禁止 silent fallback

禁止以下行为：

- DeepSeek 请求失败后，自动改用确定性扫描并返回成功。
- LLM schema 失败后，手写一个“看起来合理”的默认 proposal。
- 网络失败后生成一份假 `.ai` 资产让流程继续。
- 把 skipped、unknown 或 low confidence 包装成 passed。

允许的行为：

- 在错误信息中说明需要配置 DeepSeek。
- 对 DeepSeek 返回空 `content` 这类瞬时 API 响应异常做有限重试；重试仍失败时必须显式失败并暴露 `finish_reason`、message keys 等非敏感诊断信息。
- 在调和阶段降低置信度。
- 对无法确认的信息标记 `needs_human_confirmation`。
- 在 Markdown 中明确写出“未发现证据”或“需要人工确认”。

## Evidence 与 LLM 的关系

Evidence 是 LLM 的输入，也是调和阶段的审计依据。

规则：

- Evidence collector 收集事实，不做最终业务判断。
- LLM evidence planner 可以基于初始 `EvidenceBundle.files` 选择少量需要深入读取的补充文件；它只能引用已发现的仓库内路径，Python 必须用 Pydantic schema 和 allowlist 校验后再读取摘要。
- LLM evidence planner 的结构化输出必须进入 `ScanMetadata.evidence_expansion`，记录 planner prompt version、requested paths、risk focus、rationale、confidence、实际读取 paths 和读取文件数量，便于调试和审计深度扫描决策。
- `ScanMetadata.evidence_expansion` 不能只停留在机器 metadata 中；生成的 `.ai/guides/project-context.md` 必须以 `## LLM 证据扩展` 展示 requested/read paths、risk focus、confidence、read file count 和 rationale，benchmark 用 `content:project-context-evidence-context` 防止该审计上下文漂移。
- LLM-guided evidence expansion 不允许读取 `.ai/`、依赖目录、构建产物、仓库外路径或模型发明的路径；非法请求必须显式失败，不能回退成确定性采样成功。
- 如果 LLM evidence planner 返回低置信度，调和阶段必须保留 warning 和 human confirmation 信号；不能把低置信度规划伪装成完全可信的扫描结果。
- coverage gap、LLM stack claim 缺少 evidence、primary stack unknown、模块边界不清或测试 evidence 缺失时，调和阶段必须生成结构化 follow-up questions，并写入 `ScanMetadata.followup_questions`。这些问题用于驱动 guided CLI 的 targeted 追问、二次自检和后续人工确认；它们不能自动修正 LLM proposal。
- 当 scan follow-up 存在时，LLM scan self-check 可以基于当前 `EvidenceBundle` 与 `ScanMetadata.followup_questions` 输出结构化 `ScanSelfCheckReport`，并写入 `ScanMetadata.self_check`。该报告必须保持 `pending_harness_maintainer_review`，只能说明每个追问是当前 evidence 已支持、仍需人工确认、需要 targeted scan，还是存在冲突；它不能声称已修改 inventory、command catalog、Guides、Sensors、Workflow 或正式 Harness 资产。self-check LLM 不可用、返回空响应、schema 错误、未知 interaction id 或未知 evidence source 时必须显式失败，不能 silently skip 或 fallback。
- `ScanSelfCheckReport.resolutions[].evidence_sources` 只能引用 Builder 提供给 self-check 的仓库 evidence、follow-up evidence、scan warning evidence、scan warning code 或 evidence expansion 路径 / 关注点。scan warning code 例如 `source_sampling_truncated` 是稳定扫描审计来源，可以作为 review-only evidence source；任意未出现过的路径或字符串仍必须显式失败。
- LLM evidence planner 如果第一次返回 schema 或 allowlist 校验失败，可以带着校验错误进行一次契约修正重试；重试仍失败时必须显式失败。该重试只能要求 LLM 从已提供 `files[].path` 中逐字复制路径或返回空列表，不能由 Python 近似匹配、自动纠正或放宽 allowlist。
- Prompt 应向 LLM 提供足够 evidence，而不是只给文件名。
- LLM proposal 应保留 reasoning summary。
- Reconciler 应使用 evidence 约束 LLM 幻觉。
- 如果 LLM 声称 Java Spring，但 evidence 没有 Java/Maven/Gradle/Spring 线索，应拒绝或降级。

## Prompt 管理

Prompt 是系统行为的一部分，应当可维护。

当前规则：

- 机器消费型 LLM Prompt 内容必须集中在 `src/harness_builder_agent/prompts/`，避免散落在多个 `tools/llm_*.py`、writer 或 CLI 里。
- Prompt asset 必须使用 `## System Message` 和 `## User Message` 章节，并通过 `prompts.registry` 统一登记版本、文件名、输入标题和消息构造。
- `tools/llm_*.py` 不能直接维护 prompt 文件名或调用 prompt loader；它们只负责 payload 拼装、LLM 调用、响应解析和 schema 校验。
- Python 模块负责向 Prompt 注入结构化 JSON payload，Prompt 文件不直接承载动态数据拼接逻辑。
- Prompt 修改必须有测试或 acceptance 验证。
- Prompt 应明确要求 JSON object 和固定 schema。
- 面向机器消费输出的 Prompt 必须显式枚举对应 Pydantic schema 的必填字段；真实 LLM 返回合法 JSON 但 schema-invalid 时，应优先收紧 Prompt 和测试，而不是放宽 schema、跳过验收或生成 fallback。
- Prompt 不应要求 LLM 直接输出最终文件内容。
- LLM maturity review 只能输出结构化 review judgment，不能声称已经修改 Guides、Sensors、Workflow 或其他正式 Harness 资产。
- LLM maturity review 遇到 `experience-workflow-recommendation-review` 改进候选时，应消费 `.ai/review/workflow-routing-recommendation.yaml` 作为 review-only workflow recommendation evidence，并与 `maturity_evidence.harness_assets.workflow_routing_rules` 对照后给出 `support`、`revise` 或 `defer`；review 不能声称推荐已执行、已应用或已写入正式 Harness 资产。
- LLM asset candidate generation 只能输出结构化 draft candidates，必须保持 `pending_harness_maintainer_review`，不能声称已应用到正式 Harness 资产。
- LLM asset candidate generation 生成 `workflow_policy` candidate 时，必须输出机器可校验的 `workflow_policy_patch`；`draft_content` 只能作为人类说明，不能作为自动 patch 来源。
- LLM experience summary 只能输出结构化 Experience findings，必须保持 `pending_harness_maintainer_review`，不能声称已经沉淀为正式 Guides、Sensors、Workflow 或风险策略。
- LLM workflow recommendation 只能输出结构化 workflow recommendation report，必须保持 `pending_harness_maintainer_review`，不能声称已经执行 Workflow、生成 Harness Map、创建 `.ai/task-runs` 或修改正式 Harness 资产。
- LLM workflow recommendation 和 LLM maturity review 的 parser 必须要求模型显式返回所有顶层契约字段，尤其是 `schema_version` 和 `review_status`；不能依赖 Pydantic 默认值把缺字段响应包装成可审计结果。
- LLM maturity review Markdown 必须包含 `## Review Boundary`，并明确 `pending_harness_maintainer_review` 和 review-only 边界。
- LLM maturity review 和 asset candidate generation 的 prompt 在 `.ai/experience/experience-summary.yaml` 存在时应注入可选 `experience_summary` 上下文；缺失时显式传入 `null`，不能自动运行 summarizer 或伪造摘要。
- LLM maturity review 和 asset candidate generation 的 prompt 应显式消费 `maturity_evidence.experience.sources`，把其中的 source path / kind / item_count 作为 review-only source index；可引用这些路径作为 evidence source，但不能把 source entry 当作已经应用的正式 Harness 规则。
- LLM experience summary 的 prompt 应显式消费 `experience_index.sources`，把其中的 source path / kind / item_count 作为 review-only source index；findings 必须基于已提供 source map 中的 `.ai/` 路径，不能发明缺失 source path，也不能把 source entry 当作已经应用的正式 Harness 规则或任务执行。
- LLM asset candidate generation 在生成 `workflow_policy` 候选时，应显式消费 `maturity_evidence.harness_assets.workflow_routing_rules`，但这些 routing rules 只能作为 review-only evidence；候选必须保持 `pending_harness_maintainer_review`，不能声称已经修改或应用 `.ai/harness-config.yaml`。
- LLM asset candidate generation 遇到 `experience-workflow-recommendation-review` 改进候选时，应消费 `.ai/review/workflow-routing-recommendation.yaml` 作为 review-only workflow recommendation evidence，并优先生成指向 `.ai/harness-config.yaml` 的 `workflow_policy` 草案；草案必须保持 `pending_harness_maintainer_review`，不能声称推荐已执行或已应用。
- LLM experience summary 可以在 `.ai/review/workflow-routing-recommendation.yaml` 存在时把它作为 review-only evidence 消费，用于总结 workflow gap、routing signal 或 improvement signal；不能把该推荐当成已执行 workflow 或已应用的正式 Harness 变更。

## Schema 规则

LLM schema 应表达稳定业务契约。

规则：

- stack 枚举要谨慎扩展。
- 新增字段要说明下游用途。
- 不要为了临时 prompt 方便加入含义模糊的字段。
- 对 command candidate 必须保留 command、type、gate、source、confidence。
- 对 human confirmation 必须有明确标记，而不是藏在自然语言里。
- 对 maturity review 必须保留 candidate_id、decision、rationale、risks、suggested_acceptance_checks 和 evidence_sources，并拒绝未知 candidate_id；真实 LLM 输出必须保持短小，summary、rationale、risks、suggested_acceptance_checks、missing_candidates 和 global_risks 都要有明确长度或条数上限，不能复制大段 evidence。
- 对 asset candidate 必须保留 kind、source_candidate_id、suggested_path、draft_content、review_status、acceptance_checks 和 evidence_sources；`suggested_path` 必须限制在安全的 `.ai/` 相对路径下，不能包含空路径段、`.` 或 `..`；`workflow_policy` candidate 的 `suggested_path` 必须精确等于 `.ai/harness-config.yaml`；真实 LLM 输出必须偏短，最多 3 个候选，`draft_content` 和 rationale 要有明确长度约束，避免长 JSON 被截断成不可解析响应。
- 对 experience summary 必须保留 kind、title、summary、review_status、confidence、suggested_follow_up 和 evidence_sources；`evidence_sources` 必须限制在提供给 LLM 的 `.ai/` 证据路径内。
- 对 workflow recommendation 必须保留 task_id、task_brief、recommended_workflow、matched_rule_ids、risk_level、confidence、rationale、required_guides、required_sensors、human_confirmation_required、review_status 和 evidence_sources；`recommended_workflow` 和 `matched_rule_ids` 必须和当前 `harness-config.yaml` 对齐。
- 对 workflow recommendation、maturity review、asset candidate 和 experience summary，`evidence_sources` 不只检查 `.ai/` 前缀，还必须属于 Builder 提供给该 LLM 阶段的 evidence allowlist；未知 `.ai/` 路径必须显式失败，不能作为可追溯证据接受。
- `.ai/guides/`、`.ai/sensors/`、`.ai/skills/`、`.ai/task-runs/` 这类目录级 maturity input 不代表允许任意子路径；只有 Builder 固定生成的基线 Harness 资产路径和明确声明的契约目录可以作为精确 evidence source 加入 allowlist。
- 对注入到下游 prompt 的 experience summary，必须在 prompt 中明确它是 review-only semantic context，不是正式规则、不是已应用变更。

## 错误处理

LLM 相关错误应该让用户知道真实问题。

错误信息应尽量包含：

- 哪个阶段失败。
- 是配置缺失、请求失败、超时、JSON 解析失败还是 schema 失败。
- 用户下一步可以检查什么。
- DeepSeek 返回空 `content` 时，应包含非敏感响应元数据，例如 `finish_reason`、message keys、是否存在 `reasoning_content`。

错误信息不应该：

- 暴露 API key。
- 输出过长原始响应。
- 把 LLM 失败说成扫描成功。

## 测试要求

LLM 相关测试至少覆盖：

- 合法 JSON proposal 能解析。
- 非法 JSON 会失败。
- 缺少必填字段会失败。
- 未知 stack 会失败或进入明确的 unknown 处理。
- LLM 声称的 stack 与 evidence 冲突时会被调和。
- 没有 DeepSeek key 的真实 acceptance 会失败。
- mock LLM 测试不应该掩盖真实 LLM acceptance 的要求。
- maturity review mock 测试必须覆盖合法 JSON、非法 JSON、schema 错误、未知 candidate_id、非 `.ai/` evidence source 和未知 evidence source。
- asset candidate mock 测试必须覆盖合法 JSON、未知 source_candidate_id、非法 suggested_path、非 `.ai/` evidence source、未知 evidence source 和 schema 错误。
- experience summary mock 测试必须覆盖合法 JSON、非法 JSON、schema 错误、非 `.ai/` evidence path 和未知 evidence source。
- workflow recommendation mock 测试必须覆盖合法 JSON、非法 JSON、未知 recommended_workflow、未知 matched_rule_ids、非 `.ai/` evidence source、未知 evidence source 和 review-only CLI 产物。
