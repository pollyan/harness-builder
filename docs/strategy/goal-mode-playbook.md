# 目标模式运行手册

本文是 Codex/GPT 在目标模式下持续演进 Harness Builder 的运行手册。它沉淀稳定执行原则、选题策略和节奏控制，用于减少目标提示词长度，并避免每轮重复口头约定。

`Goal Mode Playbook` 比“提示词”更合适：提示词是一次性输入，运行手册是可版本化、可审查、可持续更新的团队工作方式。

## 目标与授权边界

目标模式的长期目标是将本仓库持续演进为 `docs/strategy/` 中描述的 Maturity-driven Self-Improve AI Coding Harness Builder。短中期优先服务 `docs/strategy/init-north-star.md`，把 `harness-builder-agent init` 打磨成深度引导式、成熟度驱动、CLI 友好、渐进式协作的 Harness 生成体验。

目标模式是全自动执行任务。Codex/GPT 可以在符合当前代码、`AGENTS.md`、`README.md`、`docs/engineering/` 和 `docs/strategy/` 的前提下，自主完成 milestone 选择、spec、plan、TDD 实现、测试、提交和后续推进。

不要把用户确认作为常规节点。普通澄清由模型基于文档、代码、测试和目标自行回答，并在 spec 中记录 assumptions / decisions / risks。只有权限、凭证、外部服务、仓库访问、连续阻塞或当前架构与 North Star 根本冲突时，才停止并向用户汇报。

## 事实源

目标模式每轮判断都必须基于当前文件，而不是上一轮记忆：

- 全局 North Star：`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`。
- 短中期 init North Star：`docs/strategy/init-north-star.md`。
- 项目级规则入口：`AGENTS.md`。
- CLI 能力与用户入口：`README.md`。
- 工程约束：`docs/engineering/` 下按 `AGENTS.md` 渐进式加载的专题文档。
- 策略索引与历史背景：`docs/strategy/README.md`。
- 当前执行手册：`docs/strategy/goal-mode-playbook.md`。
- 当前代码、测试、fixture、benchmark、`docs/todos/`、已有 spec / plan 和 git 历史。

若提示词、North Star、当前代码或工程文档冲突，以当前代码、`AGENTS.md`、`docs/engineering/` 和 `docs/strategy/` 的最新事实为准，并在 spec 中记录取舍。

## 每轮读取顺序

每轮目标模式开始时，先读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/strategy/README.md`
4. `docs/strategy/goal-mode-playbook.md`
5. 与当轮改动相关的 `docs/engineering/` 专题文档
6. 与当轮方向相关的 North Star / todo / 已有 spec / plan

不要用上一轮记忆替代当前文件。文件内容冲突时，以当前代码、`AGENTS.md`、`docs/engineering/` 和 `docs/strategy/` 的最新事实为准，并在 spec 中记录取舍。

读取完成后的第一个实际工作产物必须是 Current State Gap Analysis。不要先写 plan、先改代码、先跑固定 todo 清单，或直接沿用上一轮 Gate 的候选结论。上一轮 Gate 只能作为本轮候选输入，仍必须被当前文件、当前代码和当前测试重新校验。

## 每轮循环

目标模式每轮都按同一条闭环执行，不能把其中任一环节替换成上一轮记忆或固定清单：

1. 重新读取 `AGENTS.md`、`README.md`、`docs/strategy/README.md`、本手册，并按 `AGENTS.md` 渐进式读取相关 `docs/engineering/`、全局 North Star、`init-north-star.md`、相关 todo 和已有 spec / plan。
2. 执行 Current State Gap Analysis，对比 North Star、当前代码、测试和文档，识别候选 gap、排序理由、边界和验收方式。
3. 选择一个且只选择一个 milestone。milestone 必须写成用户故事或工程信任故事，优先选择可独立验收的纵向切片；同一用户故事下共享数据流、可一次验收的小候选应合并。
4. 定义可执行验收标准，覆盖用户或工程价值、CLI transcript 或文件产物、L0-L4 成熟度叙事、schema / 契约、用户输入消费链路、错误与边界、测试层级、benchmark 和文档影响中适用的内容。
5. 使用 Superpowers 形成中文 spec、中文 implementation plan，并按 TDD 先写失败测试再实现；测试失败或行为异常时用 systematic debugging 定位根因。
6. 有可用 sub agent 时，主动用于代码 / 文档调研、gap 分析、测试覆盖审查、方案评审、风险排查或边界清晰的独立子任务；主线程负责整合结论、避免冲突编辑、最终验证和提交。
7. 实现、验证并创建本地 commit。commit / push / CI 规则按 `AGENTS.md` 和本手册执行；所有文档、spec、plan、commit message 和过程记录都用中文。
8. 执行 Self-Harness Gate，把影响后续迭代质量的缺口作为下一轮候选输入；如果缺口很小且与当前轮强相关，可当前轮补齐；如果较大，记录到 `docs/todos/`。

每轮完成 Gate 后，自动进入下一轮 Current State Gap Analysis，直到满足停止条件。不要把用户确认作为常规节点；普通澄清由模型基于事实源、代码、测试和目标自行回答，并在 spec 中记录 assumptions / decisions / risks。

## 选题原则

1. 每轮选择新 milestone 前，先检查 `docs/todos/` 中未完成事项。
2. 如果 open todo 符合当前 North Star 和用户最新优先级，优先消化 todo。
3. todo 也必须进入 Current State Gap Analysis 的候选列表；不能绕过 gap 分析直接执行 todo。
4. milestone 必须写成用户故事或工程信任故事，说明角色、真实场景、完整动作、独立价值。
5. 技术债、契约 hardening、测试或重构也必须说明保护的用户工作流和降低的风险。

## Current State Gap Analysis

每轮目标模式必须先做 Current State Gap Analysis，再选择 milestone。Gap Analysis 的目标不是机械执行固定清单，而是基于最新代码、测试、文档和 North Star 判断下一步最有价值、最可验收、最少破坏当前契约的工作包。

Gap Analysis 必须作为当轮 spec 的一个独立小节实际产出，也应在 `docs/evolution-log.md` 中保留摘要。不允许只写“已分析”或直接跳到结论。它至少包含：

- 事实源快照：本轮实际读取了哪些关键文件，哪些文件因无关没有展开。
- 候选 gap 列表：至少 2 个候选；如果确实只有 1 个，也要说明为什么。候选必须覆盖 open todo、上一轮 Gate 候选和本轮新发现中的相关项。
- 排序依据：说明为什么选中的 gap 比其他候选更适合作为本轮 milestone。
- 未选候选去向：保留为下一轮候选、写入 `docs/todos/`、归入更大工作包，或明确暂不处理。
- 验收口径：每个候选都要说明可以被什么证据验证，不允许只写“后续观察”。
- 边界判断：明确哪些内容属于当前 milestone，哪些因为跨旅程、高风险或缺少依赖而不进入本轮。

分析维度至少覆盖：

- 产品能力：当前 Harness Builder 是否继续靠近 Maturity-driven Self-Improve AI Coding Harness Builder。
- init 用户旅程：启动说明、扫描进度、扫描理解对齐、成熟度初评、补充吸收、设计预览、写入摘要是否顺畅。
- CLI 体验：终端输出是否中文、分组清晰、低内部字段暴露、能表达事实 / 推断 / 待确认 / 下一步。
- 渐进式交互：关键用户输入是否发生在相关设计决策前，并被后续成熟度、推荐或资产生成消费。
- L0-L4 成熟度叙事：是否先讲等级、证据、阻断项和下一等级差距，再用维度评分解释。
- 仓库理解深度：evidence、LLM-guided expansion、scan reconcile、coverage gap、多栈 / 噪声目录 / 高风险目录是否足够支撑判断。
- Harness 推荐质量：Guides、Sensors、Workflow Skills、routing policy 和候选资产是否围绕当前仓库与成熟度缺口生成。
- 智能化闭环：LLM 是否负责判断 / 候选 / 推荐，Python 是否负责 schema、evidence、reconciler、validation 和审计。
- Runtime 分工：Builder 是否只生成和只读消费 Runtime 契约，不越界执行任务或创建 `.ai/task-runs`。
- schema / 数据契约：机器消费文件是否有 Pydantic schema，跨文件引用和 review-only 状态是否可验证。
- 测试与 benchmark：unit / integration / e2e / acceptance / benchmark 是否覆盖新增行为，断言是否超过“文件存在”。
- 工程架构：模块边界、prompt 管理、writer、scanner、maturity、experience、benchmark 是否继续清晰。
- 健壮性：LLM 不可用、schema 错误、低置信度、coverage gap、缺少验证命令等是否显式失败或显式记录风险。
- 技术债：是否存在重复代码、规则散落、过小切片造成流程成本过高、测试过慢或边界混乱。
- 文档事实源：AGENTS、README、engineering、strategy、todo、spec / plan 和当前代码是否有冲突或过期内容。

每个候选 gap 应按同一结构记录：

- 目标态：North Star 期望用户或系统能获得什么。
- 当前能力：当前代码、测试和文档已经做到什么。
- 缺口：还差什么，缺口发生在哪个用户旅程或工程链路。
- 价值：解决后保护哪个用户工作流、提升哪类信任或降低哪类风险。
- 风险 / 复杂度：是否涉及 schema、LLM、benchmark、runtime 契约、真实 acceptance 或高风险迁移。
- 可测试性：可以用哪些 unit / integration / e2e / acceptance / benchmark / CLI transcript / 文档 diff 验证。
- 依赖项：是否依赖外部凭证、真实仓库、已有 todo、上游 schema 或产品决策。
- 验收方式：完成后用什么证据证明用户故事或工程信任故事成立。

建议使用以下紧凑模板，保证分析可审查：

```markdown
### Current State Gap Analysis

事实源快照：
- 已读取：...
- 按需未展开：...

候选 gap：
| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | todo / Gate / 新发现 | ... | ... | ... | ... | ... | ... | ... | ... | 本轮 |
| B | todo / Gate / 新发现 | ... | ... | ... | ... | ... | ... | ... | ... | 下一轮候选 |

排序结论：
1. 选择 A，因为...
2. B 暂不选，因为...，后续...

本轮 milestone：
作为 <角色>，当我 <处于真实场景>，我可以 <完成完整动作或获得可信结果>，从而 <产生独立价值>。
```

候选 gap 排序时优先考虑：

1. 对 `init-north-star.md` 的推进程度。
2. Harness Maintainer 或后续维护者的独立价值。
3. 是否形成从输入、判断、产物到验证的闭环。
4. 对当前风险和测试缺口的降低程度。
5. 是否可在一个清晰 milestone 内完成并验收。

Gap Analysis 的结论要写入当轮 spec 和 `docs/evolution-log.md`，但不要把临时推理、一次性调研细节或未稳定的猜测沉淀为长期规则。

当轮验收标准必须从选中的 gap 推导出来，至少覆盖这些适用项：

- 用户或工程价值：解决了哪个真实用户旅程、维护者信任问题或迭代风险。
- CLI transcript 或文件产物：用户能看到什么，或哪些 `.ai` / review-only 产物发生稳定变化。
- L0-L4 成熟度叙事：新增能力如何影响等级、证据、阻断项或下一等级差距。
- schema / 契约：机器消费文件是否有 Pydantic schema，跨文件引用是否可验证。
- 用户输入消费链路：关键输入是否在相关设计决策前收集，并被成熟度、推荐或资产生成实际消费。
- 错误与边界：LLM 不可用、schema 错误、低置信度、coverage gap、缺少验证命令等是否显式失败或显式记录风险。
- 测试层级：unit / integration / e2e / acceptance / benchmark / CLI transcript / 文档 diff 中哪些负责证明本轮价值。
- 文档影响：是否需要同步 `README.md`、`docs/engineering/`、`docs/strategy/`、`docs/todos/` 或 evolution log。

## Milestone 粒度

milestone 的边界是完整用户价值，不是最小代码改动。

应该合并的情况：

- 同一 todo 下的多个小问题服务同一个用户故事。
- 它们共享同一条数据流或同一个 CLI 旅程阶段。
- 可以在一次 spec / plan / TDD 中清楚验收。
- 合并后仍能在一个小型 commit 组内完成。

应该拆分的情况：

- 跨越不同用户旅程，例如首次 init 和已有 Harness 维护入口。
- 需要不同验收语义，例如 CLI transcript、schema 迁移、benchmark 策略分别独立。
- 会触碰高风险 schema / prompt / benchmark / runtime 契约迁移。
- 范围变成“顺手把相关东西都重构一下”。

经验规则：一个 milestone 可以包含 2-4 个紧密相关的小修复，但必须围绕一个可讲清楚的用户故事。

## Superpowers 使用方式

目标模式仍遵循 Superpowers 的工程纪律，但不把流程成本浪费在过小切片上。

- brainstorming：用于形成当轮 spec，但自动目标模式下不等待用户确认；把 assumptions / decisions / risks 写入 spec。
- writing-plans：用于多步骤实现计划；计划应具体到文件、测试和命令。
- test-driven-development：生产行为变更先写失败测试，再实现。
- systematic-debugging：测试失败或行为异常时先定位根因，不降低断言。
- verification-before-completion：完成前必须用命令结果证明，而不是凭感觉宣称完成。
- requesting-code-review：较大、高风险或跨模块改动后使用。

每轮执行顺序：

1. 重新读取事实源和相关工程规则，不能用上一轮记忆替代当前文件。
2. 执行 Current State Gap Analysis。
3. 选择一个且只选择一个 milestone。
4. 定义可执行验收标准。
5. 使用 brainstorming 写中文 spec。
6. 使用 writing-plans 写中文 implementation plan。
7. 使用 test-driven-development 先写失败测试再实现。
8. 使用 systematic-debugging 处理失败。
9. 使用 verification-before-completion 完成前验证。
10. 创建本地 commit，并按 push 节奏决定是否同步远端。
11. 执行 Self-Harness Gate，然后进入下一轮 Gap Analysis。

如果只是沉淀稳定流程规则或文档索引，可以保持轻量，不为避免小成本而制造更大的过程文档。

验收标准必须能被测试、命令输出、CLI transcript、生成产物或文档 diff 验证。对于 `init` 相关 milestone，验收标准应显式覆盖用户 / 工程价值、CLI transcript 或文件产物、L0-L4 成熟度叙事、schema / 契约、用户输入如何影响后续决策、错误与边界、测试层级、benchmark 或文档影响。

## Sub Agent 使用

有可用 sub agent 时，优先用于并行的只读调研和风险审查：

- 代码路径定位
- 测试覆盖审查
- gap analysis 交叉验证
- 方案边界审查
- 高风险改动的独立 review

主线程负责拆分边界、整合结论、避免冲突编辑、最终验证和提交。子代理不应重复主线程正在做的阻塞工作。

## 提交与 Push 节奏

本地 commit 可以按独立切片或阶段性检查点创建；push 不跟随每个 commit。

- 创建本地 commit 前运行 `scripts/test-fast.sh`。
- 一个 todo / 工作包可以包含多个本地 commit。
- 只有完整 todo、完整工作包或已经产生独立用户价值的功能批次完成后，才统一考虑 push。
- push 前必须运行 `scripts/test-full.sh`。
- 降低 push 频率不豁免 push 前全量验证，只减少触发次数。

## Self-Harness Gate

每轮完成后检查：

- 长期文档是否需要更新。
- init North Star 是否被服务。
- `docs/todos/` 是否需要新增、更新或归档。
- fixture / integration / e2e / acceptance / benchmark 是否需要补齐或调整。
- `.ai` 资产 schema、稳定章节和跨文件引用是否有测试覆盖。
- CLI transcript、成熟度叙事、L0-L4 下一等级差距、用户输入消费链路、生成前 preview 是否有验收缺口。
- 用户补充、scan self-check、LLM evidence expansion、maturity preview、推荐动作和最终资产之间是否形成可审计闭环。
- 是否存在重复代码、边界混乱、规则散落、测试只断言文件存在、过小切片拖慢循环，或 prompt / schema / writer 分工不清的工程债。
- sub agent 使用是否充分。

Gate 缺口若影响后续迭代质量，优先作为下一轮 milestone；若很小且与当前轮强相关，可当前轮补齐；若较大，记录到 `docs/todos/`。

不要为了赶功能跳过 Gate。Gate 不是泛泛复盘，而是决定下一轮是否应优先修复执行系统、测试契约、CLI transcript、成熟度叙事或文档事实源的质量门。

## 决策规则

1. milestone 必须来自当轮 Gap Analysis，不机械执行固定清单。
2. 短中期优先选择更符合 `init-north-star.md`、更有独立价值、更可测试、更可审计、更少破坏当前契约的方案。
3. `init` 必须保持渐进式协作：关键用户输入应发生在相关设计决策前，并被后续成熟度、推荐或资产生成消费；事后确认不算有效交互。
4. 成熟度面向用户以 L0-L4 为主线，维度评分只用于解释等级和下一等级差距。
5. 智能化与确定性验证冲突时，采用“LLM 做判断 / 候选 / 推荐，Python 做 schema / evidence / reconciler / validation”。
6. 正式资产自动更新有风险时，生成候选资产和审核状态，不直接覆盖正式资产。
7. 缺少信息时从代码、docs、测试和 git 历史推断，并在 spec 中记录 assumption。
8. 每轮只做一个清晰 milestone，不做无边界大重构。
9. 测试或验收失败时，先定位根因；不要降低断言、跳过验收、放宽 schema 或引入 silent fallback。
10. 文档只沉淀稳定规则、产品边界、契约和长期决策；临时过程和一次性判断不写入长期文档。
11. 对可并行且边界清晰的工作，优先使用 sub agent。

## 每轮记录

每轮至少保留：

- 当轮 spec。
- 当轮 implementation plan。
- 本地 commit summary。
- `docs/evolution-log.md` 或 `docs/` 下其他稳定中文 Markdown 演进记录。

演进记录应简要包含：

- North Star 能力模块。
- init North Star 对应旅程阶段。
- Gap Analysis 摘要。
- 用户故事或工程信任故事。
- 当前代码 gap。
- 关键决策 / 取舍。
- assumptions / risks。
- sub agent 使用情况。
- 价值切分说明。
- 验收标准及验证方式。
- 完成内容。
- 验证结果。
- Self-Harness Gate 结论。
- 下一轮候选 gap。

记录原则：

- 过程文档尽量中文。
- 演进记录只记稳定决策、选题理由、验收结果、Gate 结论和下一轮候选 gap；临时推理、一次性调研细节和未稳定猜测不写入长期文档。
- 每轮 milestone 控制在一个可审查 commit 或小型 commit 组内。

## 停止条件

目标模式持续推进，除非出现以下情况：

1. 权限、联网审批、凭证、外部服务或仓库访问导致无法继续。
2. 连续三轮同一阻塞且无合理替代路径。
3. 当前架构与 North Star 根本冲突，需要重新界定产品边界。
4. 用户主动暂停、变更目标或结束。
5. 已完成当前可实施的主要目标态能力，并有测试、文档和 benchmark 证明。

当前可实施指在现有凭证、权限、仓库访问、产品边界和工程架构下可完成；需要外部 Runtime、未授权服务或重大产品决策的内容记录为后续 gap，不强行实现。

“当前可实施”不等于“完整 North Star 已经足够细”。目标模式可以把长期规划作为方向，在每轮 Gap Analysis 中拆成可实施的用户故事或工程信任故事，再用 Superpowers 完善需求、写计划、TDD 实现和验证。无法在当前边界内实现的内容应明确记录为后续 gap，而不是隐式跳过。

## 目标提示词精简建议

目标模式提示词可以只保留：

- 当前大目标和授权边界。
- 必须读取 `AGENTS.md`、`README.md`、`docs/strategy/README.md` 和本手册。
- 本轮优先级或最新用户指令。
- 停止条件和权限边界。

稳定执行规则、粒度策略、提交 / push 节奏和 Gate 细节应优先沉淀到本文件，而不是不断塞回目标提示词。

## 启动语义

当目标提示词写入“现在开始”时，含义是立即从 Current State Gap Analysis 启动执行，不等待用户确认。Codex/GPT 应自主选择 milestone，完成 spec、plan、TDD 实现、验证、本地提交和 Self-Harness Gate；如果工作包尚未形成独立 push 价值，不要 push。

只有以下情况需要停止汇报：权限、联网审批、凭证、外部服务、仓库访问、连续三轮同一阻塞、当前架构与 North Star 根本冲突，或用户主动暂停 / 变更目标 / 结束。

## 精简目标提示词模板

后续在 Codex 目标模式中，可以使用以下精简模板。若某轮有新的用户优先级，只补充在“本轮优先级”中；不要把本手册已有规则重复塞回提示词。

```text
目标：
将 /Users/anhui/Documents/myProgram/harness-builder 持续演进为 docs/strategy/ 中描述的 Maturity-driven Self-Improve AI Coding Harness Builder。短中期优先服务 docs/strategy/init-north-star.md：把 harness-builder-agent init 打磨成深度引导式、成熟度驱动、CLI 友好、渐进式协作的 Harness 生成体验。

授权：
这是全自动目标模式任务。Codex/GPT 可在符合当前代码、AGENTS.md、README.md、docs/engineering/、docs/strategy/ 的前提下，自主完成 milestone 选择、spec、plan、TDD 实现、测试、提交和后续推进。
不要把用户确认作为常规节点；普通澄清由模型基于文档、代码、测试和目标自行回答，并在 spec 中记录 assumptions / decisions / risks。只有权限、凭证、外部服务、仓库访问或连续阻塞导致无法继续时才停止汇报。
只有完成有独立价值的用户故事、工程信任故事或完整工作包后才 push。

每轮必须读取：
1. AGENTS.md
2. README.md
3. docs/strategy/README.md
4. docs/strategy/goal-mode-playbook.md
5. 与当轮改动相关的 docs/engineering/ 专题文档
6. docs/strategy/init-north-star.md、全景规划、相关 docs/todos/ 和已有 spec / plan

执行方式：
按 docs/strategy/goal-mode-playbook.md 执行每轮循环，包括 Current State Gap Analysis、todo 优先、完整用户价值切片、Superpowers、TDD、sub agent、验证、commit / push 节奏和 Self-Harness Gate。Current State Gap Analysis 必须在 spec 中实际产出候选 gap、排序理由和验收方式，不能只写结论。
每轮只选择一个边界清晰的 milestone，但同一用户故事下共享数据流、可一次验收的相邻小问题应合并推进，避免过小切片造成流程成本浪费。

本轮优先级：
<填写最新用户指令或当前工作包；没有则留空，由 playbook 的 todo 优先规则决定。>

停止条件：
权限、联网审批、凭证、外部服务、仓库访问或连续三轮同一阻塞导致无法继续；当前架构与 North Star 根本冲突；用户主动暂停或变更目标；或主要目标态能力已经被当前证据完整证明。

现在开始：
从 Current State Gap Analysis 开始，不等待用户确认。自主选择 milestone，完成 spec、plan、TDD 实现、验证、本地提交和 Self-Harness Gate。若工作包尚未形成独立 push 价值，不要 push。
```
