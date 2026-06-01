# 架构规则

本文描述 Harness Builder 当前架构边界和演进约束。修改模块边界、目录结构、核心流程或跨层调用前，先阅读本文。

## 当前架构概览

Harness Builder 是一个 Python CLI 项目，主入口是 `harness-builder-agent`。当前核心命令包括：

- `init`：扫描目标仓库并生成初始 Harness 资产。
- `assess`：生成或更新成熟度评估。
- `improve`：生成待确认的改进候选。
- `self-improve`：串联 maturity assessment、deterministic improvement candidates、LLM maturity review 和 review-only asset candidates，生成自改进审查包；不应用正式 Harness 变更，不执行 Runtime。
- `review-candidate`：记录 Harness Maintainer 对 review-only asset candidate 的显式治理决策；`applied` 可追加 Guide / Sensor Markdown，或按结构化 `workflow_policy_patch` 更新 `.ai/harness-config.yaml` routing rule。
- `benchmark`：对完整链路产物做结构、内容和质量门禁检查。
- `recommend-workflow`：基于任务 brief、`workflow_routing` 和成熟度证据生成 review-only workflow 推荐，并刷新 Experience / Maturity 派生证据；不执行 Runtime。

当前主要目录职责：

| 路径 | 职责 |
| --- | --- |
| `src/harness_builder_agent/cli.py` | CLI 参数解析、命令入口、顶层异常出口 |
| `src/harness_builder_agent/schemas/` | 机器消费数据结构的 Pydantic schema |
| `src/harness_builder_agent/tools/` | 扫描、LLM、调和、资产生成、benchmark 等业务模块 |
| `src/harness_builder_agent/tools/existing_harness_action_runner.py` | 已有 Harness guided 维护入口的动作路由和非 review 动作编排 |
| `src/harness_builder_agent/tools/existing_harness_deterministic_actions.py` | 已有 Harness guided 维护入口中的确定性维护动作编排，例如 `assess`、`improve` 和 `benchmark` |
| `src/harness_builder_agent/tools/existing_harness_intelligent_actions.py` | 已有 Harness guided 维护入口中的 LLM / review-only 智能维护动作编排，例如 `recommend-workflow` 和 `self-improve` |
| `src/harness_builder_agent/tools/existing_harness_review_actions.py` | 已有 Harness 的候选治理、human-input 治理和初始 LLM 候选治理动作实现 |
| `src/harness_builder_agent/tools/existing_harness_action_failures.py` | 已有 Harness 维护动作的 action-specific 失败 trace 出口 |
| `src/harness_builder_agent/prompts/` | 机器消费型 LLM prompt 资产，按功能集中管理 |
| `src/harness_builder_agent/templates/skills/` | 固定内置 Workflow Skill 模板 |
| `tests/unit/` | 单模块、函数、schema、边界条件测试 |
| `tests/integration/` | CLI 命令和多模块协作测试，通常使用 mock LLM |
| `tests/e2e/` | fixture 仓库完整链路测试 |
| `tests/acceptance/` | 真实 DeepSeek 和真实开源仓库验收 |
| `docs/superpowers/` | 历史设计和实施计划 |
| `docs/engineering/` | 当前工程规则和维护约束 |

## 分层职责

### CLI 层

`cli.py` 负责命令定义、参数解析、调用应用层能力和返回用户可理解的结果。

规则：

- CLI 层不应包含复杂业务判断。
- CLI 层可以创建 `GenerationTrace`，但具体事件和产物记录应由业务模块补充。
- CLI 参数变更必须同步 README、相关工程文档和测试。
- 新增命令必须明确输入、输出、失败行为和测试入口。

### Schema 层

`schemas/` 是机器消费数据的唯一契约来源。

规则：

- JSON/YAML 产物只要会被程序再次读取，就必须有 Pydantic schema。
- schema 变更必须有测试覆盖。
- 不要用 ad hoc dict 长期承载跨模块契约。
- schema 字段应优先表达业务含义，避免把当前实现细节暴露成长期契约。

### 扫描层

扫描层由 evidence 收集、LLM 分析和结果调和组成。

规则：

- `evidence_collector` 只能收集事实，不能成为最终技术栈裁决器。
- `llm_evidence_planner` 可以在最终 LLM scan 前基于初始文件索引选择少量补充 evidence；它只输出结构化路径计划，不能直接读取任意文件或生成最终结论。
- `llm_scan_analyzer` 负责 LLM-first 分析，并输出结构化 proposal。
- `scan_reconciler` 负责把 LLM proposal 和 evidence 调和成稳定的 `ProjectInventory` 与 `CommandCatalog`。
- 补充 evidence 读取必须由 Python 按 allowlist 执行，路径必须来自已发现文件索引，不能包含 `.ai/`、依赖目录、构建产物或仓库外路径。
- 如果 LLM 输出和 evidence 明显冲突，应该降级置信度、标记人工确认或失败，不能默默接受。
- 不允许新增“LLM 不可用时用确定性扫描冒充成功”的 fallback。

### 资产生成层

资产生成层负责把扫描结果、命令目录、武器库选择和上下文输入写成 Harness 资产。

规则：

- 资产生成应该由确定性程序完成，不能让 LLM 直接随意写文件。
- 生成 Markdown 可以是语义化内容，但必须保留稳定章节，便于测试和人工审查。
- 生成 JSON/YAML 必须符合 schema。
- Workflow Skill 当前来自固定模板，内置模板包括 `lightweight`、`bugfix` 和 `standard`，不做动态 LLM 生成。
- `harness-config.yaml` 必须包含可被宿主 Runtime 消费的 workflow definitions 和 `workflow_routing` 策略；Builder 只生成策略契约，不执行任务路由。
- `recommend-workflow` 只能输出 `.ai/review/workflow-routing-recommendation.*` 最新审查产物，并追加 `.ai/review/workflow-routing-recommendations/` 历史索引和摘要；随后刷新 `.ai/experience/experience-index.yaml`、`.ai/maturity-score.yaml` 和 `.ai/maturity-evidence.yaml` 等派生证据。正式任务执行、Harness Map、`.ai/task-runs` 和正式 routing policy 应用仍由宿主 Runtime / 后续审核流程承担。
- `self-improve` 只能输出 `.ai/review/self-improve-package.*` 以及被其串联命令生成的 review-only 改进产物；正式 Guide、Sensor、Workflow Skill 和 routing policy 仍需后续审核流程应用。
- `review-candidate` 是候选治理层的显式应用入口。它必须把治理决策写入 `.ai/review/candidate-governance.*`，保持原始 LLM candidate report 为 review-only；`workflow_policy` 的 `applied` 只能消费结构化 `WorkflowPolicyPatch`，不得从自由文本 `draft_content` 推断 YAML patch。
- 如果 writer 文件持续膨胀，应优先按产物类型拆分，而不是继续堆在单文件中。

### Prompt 资产层

机器消费型 LLM prompt 是系统行为契约，统一放在 `src/harness_builder_agent/prompts/`。Prompt 文件、版本、输入标题和消息构造入口由 `prompts.registry` 集中登记；业务模块只选择已注册 prompt，并注入结构化 evidence / payload。

规则：

- 不在 `tools/llm_*.py` 中内联大段 prompt contract。
- 不在 `tools/llm_*.py` 中维护 prompt 文件名或直接调用 prompt loader；新增机器消费型 prompt 必须先进入 registry。
- Prompt asset 必须有测试覆盖，至少验证可加载、关键 schema 字段和 review-only 边界。
- Prompt asset 只描述系统/用户指令和输出契约；Pydantic schema、payload 拼装、解析和错误处理仍属于 Python 代码。
- 修改 prompt 时必须同步考虑真实 DeepSeek acceptance 或 targeted acceptance。

### 武器库层

武器库层为不同技术栈提供稳定、可复用的 guide/sensor 基线。

规则：

- 内置武器库负责提供稳定下限，避免每次完全依赖 LLM 生成导致结果漂移。
- LLM 可以提出增强候选，但候选必须标记为 candidate，并要求人工确认。
- 武器库选择结果必须落盘，便于审计和测试。

### 可观测层

可观测层包括 Harness Builder 自身的 generation trace、artifact list 和 decision log。任务级 runtime trace 仍是未来 AI Coding Runtime 执行 Workflow Skill 时需要维护的可观测性契约，但不由 Harness Builder CLI 生成。

规则：

- 关键 Harness Builder 命令应记录开始、完成、失败和关键阶段事件。
- 生成的重要文件应记录到 artifact list。
- 失败不能只表现为异常栈；应尽量保留可解释的阶段和上下文。
- trace 是调试和验收依据，不是装饰性输出。
- 已有 Harness guided 维护入口应由 `existing_harness_action_runner.py` 负责动作路由；确定性维护动作由 `existing_harness_deterministic_actions.py` 维护，review 类治理动作由 `existing_harness_review_actions.py` 维护，LLM / review-only 智能动作由 `existing_harness_intelligent_actions.py` 维护，action-specific 失败 trace 统一通过 `existing_harness_action_failures.py` 写入，避免失败上下文退化成泛化 init failure。

### Benchmark 层

`benchmark` 是 POC 的验收器，用来检查生成 Harness 是否达到最低质量要求。

规则：

- benchmark 不应只检查文件存在，还要检查 schema、内容章节、跨文件引用和 hard gate command 证据。
- hard gate command 证据不足时，benchmark 可以失败，但必须给出明确失败项。
- benchmark 检查项新增或调整时必须有测试。

## 跨层调用约束

- CLI 可以调用 tools，但 tools 不应反向依赖 CLI。
- schemas 不应依赖 tools。
- tests 可以读取生成产物，但不要依赖临时目录之外的脏状态。
- acceptance 测试可以依赖真实网络和本地 API key，但不能进入默认 CI。
- 业务模块之间传递结构化对象优先于传递裸 dict。

## 需要警惕的反模式

- 在 CLI 中堆业务逻辑。
- LLM 输出不经 schema 直接驱动下游程序。
- 生成文件测试只断言存在。
- 将 skipped 当作 passed。
- 失败时自动 fallback，让用户误以为成功。
- README、AGENTS、engineering docs 中重复维护同一规则。
- 让 Workflow Skill 每次由 LLM 随机生成。

## 演进判断

当出现以下情况时，应考虑拆分模块或更新架构文档：

- 单个 writer 同时负责 4 类以上产物，且测试难以定位失败。
- 某个 schema 被 3 个以上模块隐式拼装。
- benchmark 检查逻辑开始承担实际生成职责。
- LLM prompt、解析和错误处理散落在多个文件中。
- 新增技术栈需要复制大量既有逻辑。
