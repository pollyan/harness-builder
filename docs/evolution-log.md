# Harness Builder 演进记录

## 2026-06-01 Existing Harness 维护动作失败 Trace 保真

- North Star 模块：Maturity-driven Init、Existing Harness 维护入口、可观测性与审计。
- init North Star 旅程阶段：再次进入已有 Harness、维护动作失败后的可解释交接。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo；本轮候选包括 Existing Harness 维护动作失败 trace 保真、action runner 模块拆分、full regression / push 工作包。上一轮已修复 `review-candidate` 缺 report / unknown id 的早期失败，但 `recommend-workflow` 空任务说明、`review-human-input` unknown id、`review-initial-candidate` 缺候选报告、workflow policy guided apply 禁止等路径仍会在写完 action-specific failed trace 后抛 `BadParameter`，被顶层 `init` 泛化覆盖。本轮选择该 gap，因为它直接保护已有 Harness 维护入口的审计可信度。
- 工程信任故事：作为 Harness Maintainer，当我在已有 Harness guided 维护入口执行 `recommend-workflow`、`review-human-input`、`review-candidate` 或 `review-initial-candidate` 等动作但输入缺失、候选不适用或治理失败时，我可以获得明确失败，并且 generation trace 保留所选维护动作、相关 id / decision 和错误原因，从而后续排查不需要猜测这是普通 init 失败还是具体维护动作失败。
- 当前代码 gap：`existing_harness_action_runner.py` 多处 `trace.finish("failed", ...)` 后继续 `raise typer.BadParameter(...)`；`cli.py:init_command` 的泛化 `except Exception` 会再次 `trace.finish("failed", {"error_type": ...})`，覆盖维护动作上下文。
- 关键决策 / 取舍：新增 `_fail_existing_harness_action()` 统一失败出口，写 action-specific failed event / summary、输出简短失败说明并 `raise typer.Exit(code=1)`；不改变 standalone 专家命令、成功路径、schema、benchmark、LLM 或 Runtime 分工。
- Assumptions / risks：guided maintenance action 失败是用户可修复的动作失败，应以非零退出结束但保留 action trace；`typer.Exit` 输出比 `BadParameter` 短，因此 helper 先 echo action 和 error。
- Sub agent 使用情况：尝试启动只读 explorer 审查 runner 失败路径，环境返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只统一 guided existing Harness maintenance action 的失败 trace，不混入 action runner 大拆分或 push 工作包。
- 可执行验收标准及验证方式：新增 integration RED tests 覆盖 `recommend-workflow` 空 brief、`review-human-input` unknown id、`review-initial-candidate` 缺 report 和 workflow policy guided apply 禁止；实现后检查 trace summary、stages、无 scan、无 `.ai/task-runs`。
- 完成内容：`existing_harness_action_runner.py` 新增统一失败 helper 并替换已知 `BadParameter` 失败出口；`docs/engineering/init-workflow.md` 沉淀维护动作失败 trace 规则；新增本轮 spec / plan 和 integration tests。
- 验证结果：RED targeted tests 先 4 failed；实现后 targeted 4 passed，`tests/integration/test_init_on_fixture_projects.py` 49 passed，`compileall` 通过，`git diff --check` 通过；`scripts/test-fast.sh` 485 passed。
- Self-Harness Gate：长期失败 trace 规则已写入 init workflow；无需新增 open todo。下一轮候选 gap：Existing Harness action runner 按动作拆模块，或在补齐 DeepSeek key 与 `.benchmarks` 后重新执行 full regression 并 push。

## 2026-06-01 Todo 索引状态对齐

- North Star 模块：目标模式运行治理、文档事实源、Maturity-driven Init 迭代节奏。
- init North Star 旅程阶段：不直接修改 CLI 旅程；服务后续围绕 `init` 主线的选题可信度。
- Gap Analysis 摘要：当前本地 `main` 相对 `origin/main` ahead 68 / behind 0，push 前 `scripts/test-full.sh` 的 fast 阶段 482 passed，但 acceptance 因缺少 `DEEPSEEK_API_KEY` 和 `.benchmarks/RuoYi-Vue` / `.benchmarks/eShopOnWeb` 失败，不能合规 push。与此同时，`docs/todos/README.md` 写着当前待办暂无，但目录内保留多个历史 todo 文件，且管理规则仍说“已完成条目移动到 archive.md”，两个 paused 文件还指向已完成的本地迁移 todo。本轮选择 todo 索引状态对齐，先消除目标模式 todo 优先规则的事实源噪音。
- 工程信任故事：作为 Harness Maintainer，当我检查 `docs/todos/` 决定下一轮目标模式是否应优先处理已有 todo 时，我可以从 README 和每个保留文件的状态清楚区分 open、paused background 和 implemented archive，从而不会把历史 todo 文件误判成仍待执行的当前任务。
- 当前代码 gap：无代码 gap；文档事实源 gap 在于 README 当前待办、目录文件状态、archive 规则和 paused 文件说明之间存在表达不一致。
- 关键决策 / 取舍：不删除历史 todo 文件，避免破坏回溯；以 README 的“当前待办”表作为 open todo 权威入口；`archive.md` 作为已完成索引，不再要求物理移动文件；paused 文件不再把 `local-unique-capability-migration.md` 作为当前优先事项。
- Assumptions / risks：历史 todo 对理解演进仍有价值；目录里仍保留多个 `.md` 文件，用户若跳过 README 仍可能误判，但顶部状态和索引已降低风险。push 仍被外部 acceptance 前置挡住，本轮不降低规则。
- Sub agent 使用情况：尝试启动只读 explorer 审查 todo 状态，环境返回 `agent thread limit reached`；主线程完成调研和修改。
- 价值切分说明：这是一个文档事实源收敛切片，不混入代码功能、Runtime 分工或 push 规则修改。
- 可执行验收标准及验证方式：README 明确 open todo 为空并列出 retained implemented / paused 文件；paused 文件移除过期迁移优先说明；archive 规则与实际文件留存方式一致；`rg` 检查过期措辞；`git diff --check` 和 `scripts/test-fast.sh`。
- 完成内容：更新 `docs/todos/README.md`、`docs/todos/guided-init-ai4se-real-repo-findings.md`、`docs/todos/maturity-driven-init-wizard.md`、`docs/todos/archive.md`；新增本轮 spec / plan。
- 验证结果：过期措辞检查 `rg '当前优先事项改为|仍保持 open|移动到 `archive.md`' docs/todos` 无结果；`git diff --check` 通过；`scripts/test-fast.sh` 482 passed。
- Self-Harness Gate：当前无需新增 open todo；下一轮候选 gap 包括 Existing Harness action runner 失败 trace 全量保真，或在补齐 DeepSeek key 与 `.benchmarks` 后重新执行 full regression 并 push。

## 2026-06-01 Guided review-candidate 失败 trace

- North Star 模块：Maturity-driven Init、Existing Harness 维护入口、可观测性与审计。
- init North Star 旅程阶段：再次进入已有 Harness、候选治理动作、失败后的可解释交接。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo；本轮候选包括 guided `review-candidate` 失败 trace、Existing Harness action runner 继续按动作拆模块、full regression / push 工作包。当前 `review-candidate` 成功路径和后续治理失败已有 action-specific trace，但候选报告缺失或候选 ID 不存在发生在 action-specific trace 之前，会退化成泛化 `init` failure。本轮选择该 gap，因为它是 Maintainer 可触达的维护入口错误路径，范围小且能提升审计可信度。
- 用户故事：作为 Harness Maintainer，当我在已有 Harness 维护入口选择 `review-candidate` 但 `.ai/review/asset-candidates.yaml` 缺失或输入了不存在的候选 ID 时，我可以获得明确失败，并且 generation trace 会记录这是 `review-candidate` 维护动作失败、失败的 candidate id 和原因，从而后续排查不需要猜测这是普通 init 失败还是候选治理失败。
- 当前代码 gap：`show_asset_candidate_summary()` 与 `find_asset_candidate()` 在 `review-candidate` branch 的 action-specific trace 前执行；缺文件或 unknown id 时顶层 CLI 会覆盖为泛化 `error_type=FileNotFoundError/BadParameter`。
- 关键决策 / 取舍：只补 `review-candidate` 预检失败路径；不改变成功治理、applied、workflow_policy 禁止应用、候选 schema、正式资产写入或 Runtime 分工；失败前先写 `existing-harness` failed trace，再通过 `typer.Exit` 保留该 trace。
- Assumptions / risks：缺失候选报告和未知候选 ID 都是 Maintainer 可修复的治理前置问题，应记录为维护动作失败；错误输出仍保持简洁，不重做全局异常渲染。
- 边界情况 / 失败模式：候选报告缺失时 summary 记录空 candidate id 和文件错误；未知候选时 summary 保留用户输入 id；两者都不重扫、不修改正式 Harness、不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动只读 explorer 审查 action runner，环境返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只修复一个 existing Harness 维护动作的早期失败审计，不混入 action runner 大拆分或 push 工作包。
- 可执行验收标准及验证方式：integration 先 RED 证明缺失 report / unknown candidate 不能保留 action-specific trace；实现后新增失败路径测试和既有 `review-candidate` 成功 / applied / workflow_policy 禁止应用回归通过。
- 完成内容：`existing_harness_action_runner.py` 在 `review-candidate` 预检前记录 started event，预检失败时写 failed event 和 summary；新增两个 guided existing Harness integration tests；新增本轮 spec / plan。
- 验证结果：RED targeted tests 先 2 failed；实现后新增失败路径 2 passed，相关 `review-candidate` regression 3 passed，`tests/integration/test_init_on_fixture_projects.py` 46 passed，`compileall` 通过，`git diff --check` 通过，`scripts/test-fast.sh` 482 passed。
- Self-Harness Gate：无需更新 README / engineering 长期规则；无需新增 todo；未改变 schema、LLM、benchmark、writer 或 Runtime。下一轮候选 gap：Existing Harness action runner 按动作进一步拆模块，或在外部前置满足后评估 full regression / push 工作包。

## 2026-06-01 写入前待确认边界预览

- North Star 模块：Maturity-driven Init、CLI Experience、渐进式交互、人工确认治理、Runtime 边界。
- init North Star 旅程阶段：成熟度驱动的 Harness 设计预览、最终确认前的可信度边界说明。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，迁移 todo 已归档；本轮候选包括写入前待确认边界预览、Existing Harness action execution 进一步抽模块、full regression / push 工作包。当前 scan presentation 已展示深度追问、LLM 二次自检和回答建议，questionnaire / human-input 会持久化待确认项，但 `show_prewrite_maturity_preview()` 在最终确认前没有集中展示哪些内容仍是低置信度或待人工确认。本轮选择该 gap，因为它直接命中 `init-north-star.md` 的“写入前展示哪些内容标记为低置信度或需要人工确认”目标态。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 的最终确认前查看 Harness 设计预览时，我可以看到当前仍待人工确认或低置信度的 scan follow-up、LLM self-check、scan warning 和验证命令，并理解确认写入只会生成可审计 Harness 基线，不会自动关闭追问、验证用户补充或执行 Runtime，从而在写入前做出更可信的确认。
- 当前代码 gap：`prewrite_preview.py` 只展示扫描补充、团队规则、Workflow 补充、Guides、Sensors、Workflow Skills 和 routing；没有 `待确认与低置信度边界` section。
- 关键决策 / 取舍：预览只读取既有 `ProjectInventory.stack_extensions["scan_metadata"]` 和 `CommandCatalog`，不新增 schema；只展示摘要和示例，完整治理仍由 `.ai/questionnaire.yaml`、`.ai/human-input-needed.md` 和 `.ai/scan-metadata.yaml` 承担；`confirm` 不改变追问状态、不验证低置信度命令、不创建 `.ai/task-runs`。
- Assumptions / risks：早段 scan presentation 的追问信息可能被长流程冲淡，最终确认前重述能降低误确认风险；输出会变长，但只展示少量示例。
- 边界情况 / 失败模式：没有待确认项时仍提醒写入后需要 benchmark 和未来 Runtime 证据；存在低置信度命令时只提示人工确认 / benchmark 暴露，不把命令升级为 hard verified；本轮不触碰 LLM、正式 writer、benchmark check 或 Runtime。
- Sub agent 使用情况：尝试启动只读 explorer 审查 prewrite preview 待确认边界覆盖，环境返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只补最终确认前的可信度边界预览，不混入已有 Harness 维护入口重构、benchmark hardening 或 push 工作包。
- 可执行验收标准及验证方式：unit 先 RED 证明 preview 缺少 `待确认与低置信度边界`；guided integration 先 RED 证明终端预览缺少同一 section；实现后 unit、guided integration、compileall 和 diff check 通过。
- 完成内容：`prewrite_preview.py` 新增待确认与低置信度边界 section，汇总 scan follow-up、self-check resolution、低置信度命令和 scan warning；README 与 `docs/engineering/init-workflow.md` 同步稳定行为；新增本轮 spec / plan。
- 验证结果：RED targeted tests 先 2 failed；实现后 `tests/unit/test_interactive_init_preview.py` 12 passed，`tests/integration/test_init_on_fixture_projects.py` 44 passed，`compileall` 通过，`git diff --check` 通过，`scripts/test-fast.sh` 480 passed。
- Self-Harness Gate：长期文档已同步；无需新增 todo；未改变 schema、LLM、benchmark、writer 或 Runtime 分工。下一轮候选 gap：Existing Harness action execution 进一步抽模块，或在外部前置满足后评估 full regression / push 工作包。

## 2026-06-01 写入前 Workflow Skills 预览

- North Star 模块：Maturity-driven Init、CLI Experience、Workflow Toolkit、Harness 设计预览。
- init North Star 旅程阶段：成熟度驱动的 Harness 设计预览、最终确认前的资产关系说明。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，迁移 todo 已归档；本轮候选包括写入前 Workflow Skills 预览、Existing Harness action execution 进一步抽模块、full regression / push 工作包。当前 `harness-config.yaml` 已定义 `lightweight`、`bugfix`、`standard` 三个 Workflow Skill 和 routing rules，写入也会复制三个 Skill 模板，但 `show_prewrite_maturity_preview()` 只展示 Guides、Sensors 和 Workflow routing，没有展示 Workflow Skills 作为即将生成的核心资产，也没有说明它们如何引用 Guides / Sensors。本轮选择该 gap，因为它直接命中 `init-north-star.md` 的“将生成哪些 Workflow Skills，以及它们如何引用 Guides / Sensors”目标态。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 的最终确认前查看 Harness 设计预览时，我可以看到将生成的 `lightweight`、`bugfix`、`standard` Workflow Skills、它们的文件路径、关键阶段、对应 routing rule，以及会加载哪些 Guides / Sensors，从而在写入前理解即将得到的不是孤立文件，而是一套可被 Runtime 消费的工作流控制资产。
- 当前代码 gap：`prewrite_preview.py` 没有 `将生成的 Workflow Skills` section；用户只能从后续 `Workflow routing` 和 completion summary 间接推断 Skill 资产。
- 关键决策 / 取舍：Workflow Skills preview 从 `HarnessConfig` 渲染，不硬编码路径和引用；只展示前几个 stage / guide / sensor，完整契约继续由 `.ai/skills/*/SKILL.md` 和 `harness-config.yaml` 承担；不修改 Skill 模板、schema、writer、benchmark、LLM 或 Runtime。
- Assumptions / risks：三个固定 Skill 是当前产品边界内的稳定基线；preview 输出略长，但每个 workflow 只展示路径、关键阶段和 routing 引用。
- 边界情况 / 失败模式：没有显式 routing rule 的 workflow 会显示保留定义和暂无显式引用；当前默认配置下三条 workflow 都有 routing rule；本轮不动态生成 Workflow Skills、不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动只读 explorer 审查 Workflow Skills preview 覆盖，环境返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只补写入前设计预览中的 Workflow Skills 用户可见信息，不混入 existing Harness action runner 重构或远端 push 工作包。
- 可执行验收标准及验证方式：unit 先 RED 证明 preview 缺少 `将生成的 Workflow Skills`；guided integration 先 RED 证明终端预览缺少同一 section；实现后 unit 和 guided integration 通过。
- 完成内容：`prewrite_preview.py` 新增 Workflow Skills section，展示 Skill 路径、关键阶段、routing rule、引用 Guides / Sensors；README 与 `docs/engineering/init-workflow.md` 同步稳定行为；新增本轮 spec / plan。
- 验证结果：RED targeted tests 先 3 failed；实现后 targeted unit 2 passed，targeted guided integration 1 passed，`tests/unit/test_interactive_init_preview.py` 11 passed，`tests/integration/test_init_on_fixture_projects.py` 44 passed；`compileall` 通过；`git diff --check` 通过；`scripts/test-fast.sh` 479 passed。
- Self-Harness Gate：长期文档已同步；无需新增 todo；未触碰 schema、LLM、benchmark、writer 或 Runtime 分工。下一轮候选 gap：Existing Harness action execution 进一步抽模块，或在外部前置满足后评估 full regression / push 工作包。

## 2026-06-01 写入前风险路由预览一致性

- North Star 模块：Maturity-driven Init、渐进式交互、Workflow routing、风险控制。
- init North Star 旅程阶段：成熟度驱动的 Harness 设计预览、最终确认前的用户输入消费说明。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，迁移 todo 已归档；本轮候选包括写入前 Workflow 风险路由预览与最终配置一致、Existing Harness action execution 进一步抽模块、full regression / push 工作包。当前 `write_initial_assets()` 已把 scan risk path 写入最终 `harness-config.yaml` 的 `standard-escalation` trigger，但 `show_prewrite_maturity_preview()` 仍用裸 `HarnessConfig.default()` 展示 routing，导致用户确认前看不到 `risk_area:*` 风险升级规则。本轮选择该 gap，因为它直接保护“用户补充 risk -> 设计预览 -> 正式 routing policy”的可见闭环。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 的写入前预览中看到 Workflow routing 设计时，我可以看到当前扫描风险或我补充的风险路径会如何进入 `standard-escalation` 的 `risk_area:*` 触发条件，从而在最终确认前确认高风险区域不会只停留在 Guide / Sensor 文案，而会进入实际生成的路由策略。
- 当前代码 gap：`prewrite_preview.py` 使用静态 `HarnessConfig.default()` 计算 preview 和成熟度；正式 writer 使用 `write_assets.build_harness_config()`，两者对风险路径 routing 的事实源不一致。
- 关键决策 / 取舍：把正式 config 构造抽成 `harness_config_builder.py`，preview 和 writer 共用；本轮不新增 routing DSL，不把自由文本 Workflow 补充直接应用为正式 routing policy，不修改 schema、LLM、benchmark 或 Runtime。
- Assumptions / risks：复用正式 builder 后 preview 更接近最终资产；如果成熟度阻断项因此变化，应视为修正旧 preview 偏差。CLI 只在存在风险路径时增加 trigger 明细。
- 边界情况 / 失败模式：scan risk 和结构化 scan supplement risk 都通过当前内存态 inventory 进入 preview；风险路径仍保留用户补充事实边界，不声称已由扫描 evidence 验证；不执行 Runtime、不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动只读 explorer 审查用户输入消费链路，环境返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只修正写入前 Workflow routing 预览与最终配置的一致性，不混入 existing Harness 维护入口重构或远端 push 工作包。
- 可执行验收标准及验证方式：unit 先 RED 证明 preview 缺少 `risk_area:frontend/package.json`；guided integration 先 RED 证明终端预览缺少同一 trigger；实现后 unit、guided integration、write assets / risk context benchmark 相关回归、compileall、diff check 和 fast regression 通过。
- 完成内容：新增 `src/harness_builder_agent/tools/harness_config_builder.py`；`write_assets.py` 和 `prewrite_preview.py` 共用 `build_harness_config()`；Workflow routing preview 对 `risk_area:*` trigger 增加中文风险升级说明；README 和 `docs/engineering/init-workflow.md` 同步稳定行为；新增本轮 spec / plan。
- 验证结果：RED targeted tests 先 2 failed；实现后 `tests/unit/test_interactive_init_preview.py` 11 passed，`tests/integration/test_init_on_fixture_projects.py` 44 passed，`tests/unit/test_write_assets.py` 与相关 risk context benchmark 5 passed，`compileall` 通过，`git diff --check` 通过；`scripts/test-fast.sh` 479 passed。
- Self-Harness Gate：长期文档已同步；无需新增 todo；未触碰 LLM、schema、benchmark check 或 Runtime 分工。下一轮候选 gap：Existing Harness action execution 进一步抽模块，或在外部前置满足后评估 full regression / push 工作包。

## 2026-06-01 Scan Self-Check 结构化建议动作

- North Star 模块：Maturity-driven Init、仓库理解深度、渐进式交互、LLM / Python 契约闭环。
- init North Star 旅程阶段：扫描结果友好呈现、深度追问、与用户对齐扫描理解。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，迁移 todo 已归档；上一轮 Gate 候选包括 self-check suggested action 结构化约束、existing Harness action execution 抽模块、full regression / push 工作包和 human-input benchmark 后续扩展。当前 LLM scan self-check 已有 schema、evidence allowlist、guided CLI 展示和 questionnaire reason，但 `suggested_next_action` 仍是自由文本，Python 不能校验下一步到底是补 `stack`、`module`、`command`、`risk`、复核 evidence 还是 targeted scan。本轮选择结构化建议动作，因为它直接推进“LLM 做判断，Python 做 schema / validation”的智能化闭环。
- 用户故事：作为 Harness Maintainer，当首次 guided `init` 的 LLM 二次自检判断某个扫描追问仍需处理时，我可以看到稳定的结构化动作类型和对应输入提示，例如补 `stack`、`module`、`command`、`risk`、复核 evidence 或运行 targeted scan；同时 Harness Builder 会拒绝缺少结构化动作的新 LLM self-check 响应，从而避免把不可消费的自由文本建议伪装成可审计结论。
- 当前代码 gap：`ScanSelfCheckResolution` 只有自由文本 `suggested_next_action`；`parse_scan_self_check_response()` 只校验 interaction id 和 evidence source，不拒绝缺少结构化 action 的新 LLM payload；CLI 和 questionnaire reason 也没有 action type。
- 关键决策 / 取舍：新增 `suggested_action_type` 枚举；旧 persisted metadata 缺字段时用 `maintainer_review` 兼容读取，但 fresh LLM parser 必须显式要求字段存在；动作类型只是 review-only 下一步意图，不执行 targeted scan、不修改正式资产、不创建 `.ai/task-runs`。
- Assumptions / risks：真实 LLM 可能一开始漏字段；prompt 与 parser 会显式失败，等待修正而不是 silent fallback。`run_targeted_scan` 当前代表后续能力或人工流程，不在本轮实现。
- 边界情况 / 失败模式：缺 `suggested_action_type` 的 fresh response 会失败；未知 enum 由 Pydantic schema 失败；未知 interaction id / evidence source 的既有失败保持不变；旧 metadata 仍能 schema validate。
- Sub agent 使用情况：尝试启动 explorer 做只读审查，环境返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只补 self-check 动作契约和用户可见提示，不混入 benchmark、新 targeted scan 执行器、existing Harness action execution 抽取或 push 工作包。
- 可执行验收标准及验证方式：LLM parser unit 先 RED 证明缺字段不会失败、合法 action 不被保留、prompt 不含字段；实现后 schema / parser / prompt / questionnaire / guided init transcript 全部通过。
- 完成内容：`ScanSelfCheckResolution` 新增 `suggested_action_type`；`llm_scan_self_checker.py` 对 fresh LLM payload 增加显式必填校验；prompt 枚举 action type；新增 `scan_self_check_actions.py`；guided CLI 和 questionnaire reason 展示 action type 与动作提示；README、init workflow、LLM contracts、testing strategy、本轮 spec / plan 同步。
- 验证结果：RED targeted tests 先 5 failed；实现后 self-check / scan repo / schema / human confirmation 17 passed，guided follow-up integration 2 passed，相关 unit regression 80 passed，`scripts/test-llm-contracts.sh` 133 passed；`compileall` 通过；`git diff --check` 通过；`scripts/test-fast.sh` 479 passed。
- Self-Harness Gate：长期文档已同步；无需新增 todo；未触碰正式资产 writer、benchmark 或 Runtime。下一轮候选 gap：existing Harness action execution 抽模块，或在外部前置满足后处理 full regression / push 工作包。

## 2026-06-01 Human Input 处理方式 Benchmark 深度校验

- North Star 模块：Maturity-driven Init、渐进式交互、人工确认治理、Benchmark 质量门禁。
- init North Star 旅程阶段：深度追问、写入后的交付摘要、会后维护入口。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，迁移 todo 已归档；上一轮已把 scan follow-up 具体回答建议写入 `.ai/human-input-needed.md#处理方式`，但 `benchmark.py` 的 `content:human-confirmation` 仍只检查三个基础 `confirm:*` ID 和 Markdown 标题，不能发现处理方式章节、具体示例、`review-human-input` 命令或 Runtime 边界漂移。本轮候选包括 human-input benchmark 深度校验、self-check suggested action 结构化约束、full regression / push 工作包和 existing Harness action execution 抽模块；本轮选择 human-input benchmark，因为它直接保护刚交付的“动态追问 -> 会后处理 -> 显式复核”闭环。
- 工程信任故事：作为 Harness Maintainer，当我运行 `benchmark` 验收首次 `init` 生成的人工确认材料时，我可以确认 `.ai/human-input-needed.md#处理方式` 保留了必要章节、scan follow-up 的具体回答示例、`review-human-input` 显式治理入口和 Runtime 边界；如果这些内容漂移，`benchmark-report.yaml` 会给出精确 missing detail。
- 当前代码 gap：`_human_confirmation_checks()` 只校验 `required_ids.issubset(ids)` 和 `# Human Input Needed`，缺少 `.ai/human-input-needed.md` 稳定章节、per-id scan follow-up 示例、resolved / reopened 治理命令和不创建 `.ai/task-runs` 边界的断言。
- 关键决策 / 取舍：新增 `scan_followup_required_guidance_snippets()` 作为 benchmark 可复用的稳定片段事实源；benchmark 只校验 marker / snippet / boundary，不锁死整段中文；resolved follow-up 不强制要求重新补充示例，只要求 resolved / reopened 边界。
- Assumptions / risks：`Questionnaire` schema 不保留 follow-up trigger，因此 benchmark 通过稳定 interaction id fallback 推断示例类型；旧 Harness 如果人工删掉新章节会 benchmark failed，这是有意暴露质量漂移。
- 边界情况 / 失败模式：缺 `## 处理方式`、缺 `module` / `risk` / `stack` / `command` 示例、缺 `review-human-input --interaction-id <id> --decision resolved`、缺“不自动关闭追问 / 不伪装成已验证 evidence / 不创建 task-runs”都会进入 `missing` detail；本轮不修改 LLM、schema、正式资产生成或 Runtime。
- Sub agent 使用情况：尝试启动 explorer 做只读审查，环境返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只增强 human-input 处理方式质量门禁，不混入 self-check schema、existing Harness action execution 抽取或 push 工作包。
- 可执行验收标准及验证方式：integration 先 RED 证明当前 benchmark 看不出缺示例 / 缺章节；实现后新增 human-confirmation 正反测试和完整 `run_benchmark()` 漂移测试通过；benchmark integration 全文件通过。
- 完成内容：`benchmark.py` 的 `content:human-confirmation` 新增稳定章节、Runtime 边界、scan follow-up per-id guidance 和 review command 校验；`scan_followup_guidance.py` 暴露 required snippet helper；README、init workflow、testing strategy、sensor/gate rules、本轮 spec / plan 同步。
- 验证结果：RED targeted tests 先 3 failed；实现后 targeted 3 passed，benchmark / human-confirmation regression 17 passed，`tests/integration/test_benchmark_command.py` 86 passed。
- Self-Harness Gate：长期文档已同步；无需新增 todo；本轮未触碰 LLM、正式资产 writer 或 Runtime。下一轮候选 gap：self-check suggested action 结构化约束，或 existing Harness action execution 抽模块；push 工作包仍需 full regression 前置。

## 2026-06-01 Human Input 深度追问处理建议

- North Star 模块：Maturity-driven Init、CLI Experience、渐进式交互、人工确认治理。
- init North Star 旅程阶段：扫描结果友好呈现、深度追问、写入后的交付摘要和会后维护入口。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，迁移 todo 已归档；上一轮已在首次 guided `init` 的 scan supplement 前展示“深度追问回答建议”，但 `.ai/human-input-needed.md#处理方式` 仍只给 scan follow-up 泛化格式提示。候选包括 human-input follow-up action guidance、self-check suggested action 结构化约束、benchmark 校验 human-input 处理方式深度和 push / full regression 工作包；本轮选择 human-input guidance，因为它直接补齐同一条“动态追问 -> 会后处理 -> 显式治理”的用户故事。
- 用户故事：作为 Harness Maintainer，当我在首次 `init` 后查看 `.ai/human-input-needed.md#处理方式` 处理未解决或部分回应的 scan follow-up 时，我可以看到每个 follow-up 对应的具体补充建议和可复制示例，并继续通过 `review-human-input` 显式标记 resolved / reopened，从而让会后处理和已有 Harness 回访不依赖临时终端输出。
- 当前代码 gap：`_scan_followup_action_guidance()` 只提示重新进入 guided `init`，并泛化列出 `stack/module/command/risk` 格式；它没有按 coverage / stack / module boundary / test evidence follow-up 给出具体示例。
- 关键决策 / 取舍：新增轻量 `scan_followup_guidance.py` 共享 helper，让 guided CLI 和 human-input Markdown 使用同一套确定性 trigger 映射；不新增 `Questionnaire` 字段，human-input 端可从已有 `trigger` 或稳定 interaction id 推断建议；本轮不新增 benchmark content check，避免过早锁死 Markdown 表达。
- Assumptions / risks：示例仍是输入格式帮助，不代表目标仓库真实存在这些路径或命令；Markdown 会略长，但只在存在 scan follow-up 时增加；resolved follow-up 仍优先展示已复核边界，不强行提示重新补充。
- 边界情况 / 失败模式：coverage gap 输出 `module` / `risk` 示例；stack claim / unknown stack 输出 `stack` 示例；test evidence 输出 `command` 示例；partial response 保留“先人工复核是否足够关闭”；所有未解决 follow-up 都明确补充不会自动关闭追问，也不会伪装成已验证扫描 evidence。
- Sub agent 使用情况：按 playbook 尝试启动只读 explorer 审查 human-input 生成链路，当前环境返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只把上一轮 CLI 即时建议延伸到持久化处理入口，不混入 self-check schema、benchmark hardening 或 push 工作包；它保护的是同一条 scan follow-up 人工治理链路。
- 可执行验收标准及验证方式：unit 覆盖 `human_input_markdown()` 输出 per-id 示例和不自动关闭边界；guided scan presentation unit 确认 CLI 仍使用同一套建议；guided integration 确认 `.ai/human-input-needed.md` 生成内容包含示例并保留 questionnaire / self-check 信息；human-input governance regression 确认 resolved 动作不改正式资产。
- 完成内容：新增 `tools/scan_followup_guidance.py`；`guided_scan_presentation.py` 改为复用 helper；`human_confirmation.py` 的 scan follow-up 处理方式追加 trigger-specific 建议；更新 README、`docs/engineering/init-workflow.md`、本轮 spec / plan 和测试。
- 验证结果：RED unit / integration 先因 human-input 缺少 `module=src/main/java|backend|核心模块` 等示例失败；实现后 human confirmation + guided scan + guided follow-up 16 passed，human-input governance regression 4 passed，asset writer human confirmation 1 passed；`compileall` 通过；`git diff --check` 通过；`scripts/test-fast.sh` 475 passed。
- Self-Harness Gate：长期文档已同步；无需新增 todo；未触碰 LLM、schema、benchmark 或 Runtime。下一轮候选 gap：评估是否需要 benchmark `content:human-confirmation` 锁定处理方式深度，或审查 self-check suggested action 的结构化约束；push 工作包仍需单独 full regression 前置。

## 2026-06-01 深度追问回答建议

- North Star 模块：Maturity-driven Init、CLI Experience、渐进式交互、仓库理解深度。
- init North Star 旅程阶段：扫描结果友好呈现、深度追问、与用户对齐扫描理解和成熟度判断。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，迁移 todo 已归档；已有 guided `init` 能在 scan supplement 前展示“深度追问”和“LLM 二次自检”，并把 follow-up 写入 questionnaire / human-input，但 CLI 没有把每个追问翻译成用户马上可输入的回答建议。候选包括深度追问回答建议、human-input 文档端建议增强、self-check action 结构化绑定和 push / full regression 工作包；本轮选择 CLI 即时回答建议，因为它直接降低首次 init 输入成本，且不扩大 schema / LLM / benchmark 契约。
- 用户故事：作为 Harness Maintainer，当我首次 guided `init` 一个存在扫描深度追问和二次自检的仓库时，我可以在输入 scan supplement 前看到每个追问对应的低负担回答建议和可复制结构化示例，从而知道该用自然语言、`stack=`、`module=`、`command=` 或 `risk=` 补充什么，并理解这些补充只会部分回应追问、不会自动关闭人工复核。
- 当前代码 gap：`show_scan_followup_questions()` 和 `show_scan_self_check()` 只展示问题、自检状态和建议动作；`_collect_scan_supplement()` 的通用提示列出格式，但缺少 follow-up trigger 到具体回答示例的逐项映射。
- 关键决策 / 取舍：新增确定性 `trigger -> guidance` renderer，放在“LLM 二次自检”之后、“风险区域”之前；示例只作为输入帮助，不声称路径真实存在；不修改 `ScanMetadata`、`Questionnaire`、`interaction-decisions.yaml`、LLM prompt、benchmark、writer 或 Runtime 分工。
- Assumptions / risks：输出只在存在 follow-up questions 时增加，终端略长但发生在用户最需要输入帮助的阶段；本轮不把建议写入 `.ai/human-input-needed.md`，文档端增强留作后续候选。
- 边界情况 / 失败模式：coverage gap 映射到 `module` / `risk` 示例；stack claim / unknown stack 映射到 `stack` 示例；module boundary 映射到 `module` / `risk` 示例；test evidence 映射到 `command` 示例；未知 trigger 保留自然语言和通用结构化格式。补充不会自动关闭追问，仍需 `review-human-input` 复核。
- Sub agent 使用情况：按 playbook 尝试启动只读 explorer 审查 follow-up / self-check 展示链路，当前环境返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只做首次 init scan supplement 前的 CLI 即时帮助，服务同一条“动态追问 -> 用户补充 -> pending review”的用户故事；不混入 human-input Markdown 契约、self-check schema 或远端同步工作包。
- 可执行验收标准及验证方式：unit renderer 覆盖 `深度追问回答建议`、coverage / stack / test 示例和不自动关闭边界；guided integration transcript 覆盖首次 init 输出；human confirmation / partial response regression 确认 questionnaire 链路不漂移；README 与 init workflow 同步稳定行为。
- 完成内容：`guided_scan_presentation.py` 新增 `show_scan_followup_answer_guidance()` 和 trigger 映射；扩展 unit / integration 测试；更新 README、`docs/engineering/init-workflow.md` 和本轮 spec / plan。
- 验证结果：RED targeted tests 先因缺少 `深度追问回答建议` 失败；实现后 renderer + guided follow-up 6 passed，human confirmation + partial follow-up regression 10 passed；`compileall` 通过；`git diff --check` 通过；`scripts/test-fast.sh` 474 passed。
- Self-Harness Gate：长期文档已同步；无需新增 todo；未触碰 schema / benchmark / Runtime。下一轮候选 gap：把 follow-up 回答建议复用到 `.ai/human-input-needed.md#处理方式`，或审查 self-check suggested action 是否需要结构化约束；push 工作包仍需单独 full regression 前置。

## 2026-06-01 已有 Harness 维护焦点前置

- North Star 模块：Maturity-driven Init、CLI Experience、Existing Harness 维护入口、Experience / review。
- init North Star 旅程阶段：再次进入已有 Harness、维护状态摘要、下一步动作选择。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，迁移 todo 已归档；上一轮 Gate 候选包括 Existing Harness raw signals 瘦身、full regression / push 工作包和继续围绕 init North Star 做新 gap。当前 existing Harness 入口已有中文 overview、triage guidance 和 shortcuts，但 guidance / shortcuts 排在 Benchmark / Workflow / Experience raw signals 后面，Maintainer 第一眼会先看到 `benchmark_failed_checks=`、`routing_default=`、`pending_improvements=` 等内部字段。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以在 raw 审计字段之前先看到中文维护建议和对应菜单编号，从而立刻知道下一步该选哪个动作，同时仍保留 Benchmark / Workflow / Experience raw signals 供排查和测试定位。
- 当前代码 gap：`_handle_existing_harness_entry()` 在 overview 后立即输出 raw Benchmark / Workflow / Experience signals，最后才输出 `Maintenance triage guidance` 和 shortcuts；没有明确告诉用户后续机器字段是 audit detail。
- 关键决策 / 取舍：不删除 raw signals，不新增隐藏 flag；只把 `Maintenance triage guidance` 和 shortcuts 前置，并增加 `Audit signals` 说明；raw section 名称和字段保持稳定，避免破坏审计和既有测试定位。
- Assumptions / risks：输出顺序变化可能影响 transcript 测试，因此本轮用 integration 测试锁定 guidance / shortcut / audit label 出现在 raw signal 前，且只输出一次。
- 边界情况 / 失败模式：exit 和 numbered exit 仍是只读动作，不扫描、不覆盖正式 Harness 资产、不追加首次初始化完成摘要；本轮不修改 action 执行、schema、benchmark、LLM、scan 或 Runtime。
- Sub agent 使用情况：按 playbook 尝试启动只读 explorer 审查现有输出噪声和测试切入点，当前环境返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮是用户可见的 CLI 焦点调整，保护已有 Harness 维护入口第一屏决策体验；不把更大的首次 init follow-up / self-check 呈现重排或 push 工作包混入同一提交。
- 可执行验收标准及验证方式：guided existing Harness exit integration 覆盖 guidance / shortcuts / audit label 顺序和不重复；相关 existing Harness tests 覆盖 overview、signals、triage、numbered exit 和 review-initial-candidate 行为；文档 diff 覆盖 README 和 init workflow。
- 完成内容：`interactive_init.py` 将 `Maintenance triage guidance` 和 `Maintenance action shortcuts` 前置到 raw signals 之前，新增 `审计明细（Audit signals）` 说明；README 与 `docs/engineering/init-workflow.md` 同步；新增本轮 spec / plan。
- 验证结果：RED integration 先因缺少 `Audit signals` 失败；实现后 targeted exit integration 1 passed；existing Harness / maintenance triage 相关 regression 40 passed；`compileall` 通过；`git diff --check` 通过；`scripts/test-fast.sh` 473 passed。
- Self-Harness Gate：长期文档已同步；无需新增 todo。下一轮候选 gap 包括首次 init 深度追问 / self-check 呈现审查，或在外部前置满足后处理 full regression / push 工作包。

## 2026-06-01 初始候选治理 Benchmark 契约

- North Star 模块：Maturity-driven Init、Experience / review 维护入口、候选资产审核、schema / 数据契约、Benchmark 质量门禁。
- init North Star 旅程阶段：再次进入已有 Harness、初始 LLM Guide / Sensor candidate 接管、质量门禁复验。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，迁移 todo 已归档；上一轮已新增 guided `review-initial-candidate`，但 `benchmark.py` 的 `_llm_enhancement_checks()` 仍要求所有初始候选永远保持 `status=candidate` 和 `human_confirmation_required=true`，并且没有校验 `.ai/review/weapon-candidate-governance.*`。这会导致 Maintainer 完成 accepted / rejected / kept 治理后，benchmark 可能误报或漏报治理日志漂移。
- 工程信任故事：作为 Harness Maintainer，当我在已有 Harness 入口对初始 LLM Guide / Sensor 候选执行 accepted / rejected / kept 后再运行 benchmark，我可以得到一个校验 candidate report、governance log 和 Markdown 审查材料一致性的质量门禁结果，从而信任候选治理债已经被正确接管，而且 Builder 没有越界修改正式 Harness 资产或 Runtime 产物。
- 当前代码 gap：`content:llm-enhancement-candidates` 只检查 pending candidate，不理解 `confirmed` / `rejected`；`_content_checks()` 中缺少独立 `content:weapon-candidate-governance`；README / engineering docs 没有沉淀该可选 artifact benchmark 规则。
- 关键决策 / 取舍：初始 LLM candidate governance 继续独立于 `.ai/review/asset-candidates.yaml`；缺失 `.ai/review/weapon-candidate-governance.*` 不失败，但一旦存在必须严格校验 YAML / Markdown 配对、source report、candidate id / type、decision -> new status -> 当前 report 的一致性和 `review_only_no_formal_asset_change` 边界；accepted 仍不代表正式资产已应用。
- Assumptions / risks：当前 report 只保存最终状态，benchmark 不能重建所有历史状态，因此只校验 governance log 声明的 `new_status` 与当前 report 一致；`previous_status` 由 schema 约束为合法历史状态，不作为正式资产应用证据。
- 边界情况 / 失败模式：unknown candidate id、candidate type mismatch、decision status mismatch、candidate status / confirmation mismatch、Markdown 缺章节或缺 status/source detail 均显式失败；未审查初始候选仍保持合法 pending 状态；本轮不修改 LLM、scanner、正式资产 writer、Runtime 或 `.ai/task-runs`。
- Sub agent 使用情况：按 playbook 尝试启动只读 explorer 审 benchmark 风险，当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮承接上一轮用户可见治理动作，把“能记录治理决策”推进到“质量门禁能证明治理决策没有漂移”；不混入 existing Harness raw signals 瘦身或 push 工作包。
- 可执行验收标准及验证方式：integration 覆盖 governed candidate status 被 `content:llm-enhancement-candidates` 接受、Markdown status drift 被报告、absent governance optional、valid governance pass、unknown candidate / status mismatch / missing Markdown sections fail、完整 `run_benchmark()` 在治理后通过且不创建 `.ai/task-runs`；文档 diff 覆盖 README、init workflow 和 sensor/gate rules。
- 完成内容：`benchmark.py` 新增 `WeaponCandidateGovernanceLog` 校验和 `content:weapon-candidate-governance`；`content:llm-enhancement-candidates` 改为校验合法状态、human confirmation、summary / type-specific Markdown id、status 和 boundary；新增 benchmark integration tests；更新 README、工程规则和本轮 spec / plan。
- 验证结果：targeted RED 先因缺少 `_weapon_candidate_governance_check` 失败；实现后 targeted candidate governance tests 13 passed；benchmark command + weapon governance regression 87 passed；guided `review-initial-candidate` integration 1 passed；`compileall` 通过；`git diff --check` 通过；`scripts/test-fast.sh` 473 passed。
- Self-Harness Gate：长期 benchmark 规则已沉淀；无 open todo 需要更新。下一轮候选 gap 包括 Existing Harness raw signals 瘦身、full regression / push 工作包，或继续围绕 init North Star 做新的 Gap Analysis。

## 2026-06-01 Guided 初始 LLM 候选治理

- North Star 模块：Maturity-driven Init、CLI Experience、候选资产审核、Experience / review 维护入口。
- init North Star 旅程阶段：再次进入已有 Harness、Maintenance triage、候选接管闭环、review-only 治理。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，迁移 todo 已归档；上一轮 Gate 候选包括初始 LLM candidates 后续治理、candidate maturity impact benchmark hardening 和 existing Harness 维护入口瘦身。当前维护入口已经能显示 `.ai/experience/weapon-library-candidates.yaml` 的 pending 数、maturity dimensions 和 top candidate，但 Maintainer 只能手动查看，无法在同一 guided 入口记录审查决策。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 看到初始 LLM Guide / Sensor 候选仍待确认时，我可以在同一个维护入口中选择 `review-initial-candidate`，对单个初始候选记录 accepted / rejected / kept 决策，并留下机器可读治理日志，从而完成一条不修改正式 Harness 资产的候选接管闭环。
- 当前代码 gap：`EXISTING_HARNESS_ACTIONS` 没有初始候选治理动作；`Maintenance triage` 只能用 `manual-review` 指向人工查看；`.ai/experience/weapon-library-candidates.yaml` 缺少对应 governance log；guided action runner 没有路径更新候选状态和 Markdown review 文件。
- 关键决策 / 取舍：新增独立 `WeaponCandidateGovernanceLog`，不复用 `.ai/review/asset-candidates.yaml` 的 `review-candidate`；只支持 `accepted` / `rejected` / `kept`，不支持 `applied`；`accepted` 只确认候选方向，不写正式 Guide / Sensor；本轮只做 guided action，不扩展 standalone CLI 命令。
- Assumptions / risks：初始 LLM candidates 是首次 init 的审查债，不具备 draft content / suggested path / apply 语义；为避免 `accepted` 被误解为正式应用，action summary、governance Markdown、README 和 init workflow 都明确 `formal_asset_changes=0` 与 review-only 边界。
- 边界情况 / 失败模式：缺少 candidate report、未知 candidate id、非法 decision 或空 rationale 均显式失败；`kept` 保持 candidate / human confirmation required；`accepted` / `rejected` 消除 pending；动作不重新扫描、不运行 LLM、不修改正式 Harness 资产、不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动只读 explorer 审计 integration 接入点和 runner 风险，当前会话返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮把上一轮只读信号升级成可审计的 Maintainer 接管动作，仍保持候选治理边界独立；benchmark hardening 和 CLI 瘦身留作后续候选，避免把治理语义和 UI 重排混在同一提交里。
- 可执行验收标准及验证方式：schema unit 覆盖 governance log；tool unit 覆盖 accepted / rejected / kept、Markdown 刷新和显式失败；menu / triage / overview unit 覆盖编号、shortcut 和 top action；guided integration 覆盖 `10` 号动作、正式资产不变、trace artifacts 和 Runtime 边界；compileall、diff check 和 fast regression 作提交前验证。
- 完成内容：新增 `src/harness_builder_agent/schemas/weapon_candidate_governance.py` 和 `src/harness_builder_agent/tools/weapon_candidate_governance.py`；existing Harness 菜单新增 `10. review-initial-candidate`；triage 把 `weapon_library_candidates_pending` 映射到该动作；guided runner 记录 `.ai/review/weapon-candidate-governance.*` 并刷新候选 Markdown；README 与 init workflow 同步。
- 验证结果：RED tests 先因缺少 `weapon_candidate_governance` module 失败；实现后 targeted tests 24 passed，相关 existing Harness / schema / triage / integration regression 81 passed，compileall 通过，`git diff --check` 通过，`scripts/test-fast.sh` 464 passed。
- Self-Harness Gate：长期 README / init workflow 已更新；无需新增 todo。下一轮候选 gap 包括 candidate maturity impact 的 benchmark 检查策略、existing Harness 入口 raw signals 瘦身，或在 full regression / external prerequisites 满足后统一 push。

## 2026-06-01 已有 Harness 初始候选成熟度信号

- North Star 模块：Maturity-driven Init、CLI Experience、候选资产审核、Experience / review 维护入口。
- init North Star 旅程阶段：再次进入已有 Harness、维护状态摘要、Experience / review signals、Maintenance triage。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo；上一轮 Gate 候选包括 existing Harness triage 消费 candidate maturity impact、candidate maturity impact benchmark hardening 和 push / 远端同步。上一轮已把 `.ai/experience/weapon-library-candidates.yaml` 增强为带 maturity impact 的机器契约，但已有 Harness 维护入口仍只展示 asset candidates / self-improve candidates，不读初始 LLM Guide / Sensor 候选。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以看到初始 LLM Guide / Sensor 候选是否仍待确认、它们影响哪些成熟度维度、最优先候选是什么以及它仍是 review-only 边界，从而不会把首次初始化留下的候选审查债误认为已经进入后续自改进闭环。
- 当前代码 gap：`experience_status_lines()`、`render_existing_harness_status_overview_lines()` 和 `build_maintenance_triage()` 不读取 `WeaponLibraryCandidateReport`；非交互 init 生成的 pending 初始候选在维护入口不可见。
- 关键决策 / 取舍：新增只读 `weapon_candidate_status.py` helper；pending 只按 candidate report 的 `status=candidate` 或 `human_confirmation_required=true` 判断；triage 使用 `manual-review`，不伪造菜单编号，不复用 `.ai/review/asset-candidates.yaml` 的 `review-candidate` 治理语义。
- Assumptions / risks：初始 LLM candidates 的后续治理动作仍未设计，本轮只让审查债可见；旧 report 缺少 maturity impact 字段时 schema 默认值会让维度显示为 `none`，不把旧资产转成失败。
- 边界情况 / 失败模式：缺少 candidate report 显示 `weapon_library_candidates=missing`；confirmed / rejected 不计入 pending；存在更高优先级 benchmark 失败时，triage 仍先处理质量门禁；本轮不写正式 Guide / Sensor，不执行 Runtime，不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动只读 explorer 审计该 gap，当前会话返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只把上一轮机器契约接入已有 Harness 维护入口，形成用户可见的只读状态闭环；不把治理动作、benchmark hardening 或 schema 迁移混入同一切片。
- 可执行验收标准及验证方式：unit 覆盖 Experience signals、overview 和 triage；integration 覆盖 guided existing Harness exit transcript；compileall、diff check 和 fast regression 作提交前验证。
- 完成内容：新增 `src/harness_builder_agent/tools/weapon_candidate_status.py`；existing Harness Experience / review signals 显示 `weapon_library_candidates*` 与 `weapon_candidate_top`；维护状态摘要显示初始 LLM candidate 待确认数量；Maintenance triage 显示 `reason=weapon_library_candidates_pending` 和 review-only guidance；README 与 init workflow 同步。
- 验证结果：RED targeted tests 先出现 4 个预期失败；实现后 targeted tests 23 passed；排序回归曾让初始候选 triage 抢到 scan follow-up 前面，修正为 human-input 之后并通过 targeted regression；`scripts/test-fast.sh` 458 passed。
- Self-Harness Gate：长期 README / init workflow 已更新；无需新增 todo。下一轮候选 gap 包括初始 LLM candidates 的后续治理动作设计、candidate maturity impact benchmark soft/hard 检查策略，或在外部 full regression 前置满足后统一 push。

## 2026-06-01 LLM 候选成熟度影响机器契约

- North Star 模块：Maturity-driven Init、候选资产审核、Experience / Self-Improve、schema / 数据契约。
- init North Star 旅程阶段：Guide / Sensor 候选审查、写入 `.ai/experience/weapon-library-candidates.yaml`、后续 review-only 智能改进输入。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo；上一轮 Gate 候选包括把 candidate maturity impact 提升为机器契约、维护入口 triage 消费 maturity impact、push / 远端同步。上一轮已在 CLI candidate review 中展示 maturity impact，但 `.ai/experience/weapon-library-candidates.yaml` 仍只记录 type/title/rationale/evidence/status，后续 review/self-improve 无法稳定消费同一判断。
- 用户故事 / 工程信任故事：作为 Harness Maintainer / 后续 Self-Improve 审查流程，当我查看或消费 `.ai/experience/weapon-library-candidates.yaml` 中的 LLM Guide / Sensor 候选时，我可以获得结构化成熟度维度、成熟度影响摘要、下一阶段贡献和 review-only 边界，从而让候选审查不只停留在终端文案，而能被后续 review、benchmark 和自改进流程稳定审计。
- 当前代码 gap：`WeaponLibraryCandidate` schema 缺少 maturity impact 字段；CLI 的 `candidate_maturity_impact_lines()` 与 candidate generation 之间没有共享机器契约；Markdown review files 不展示 maturity impact。
- 关键决策 / 取舍：新增 `candidate_maturity_impact.py` 作为无 Typer 依赖的共享 helper；`WeaponLibraryCandidate` 新增 `maturity_dimensions`、`maturity_impact_summary`、`next_stage_contribution` 和 `review_boundary`，并提供默认值兼容旧资产；不要求 benchmark 因旧候选缺字段失败。
- Assumptions / risks：当前 maturity impact 仍是确定性启发式，不代表正式成熟度提升；通过 `review_boundary=review_only_no_formal_asset_change` 和保守 summary 降低误导。
- 边界情况 / 失败模式：architecture candidate 记录 `guides`；risk candidate 记录 `guides` / `risk_control`；sensor candidate 记录 `sensors` / `verification_sophistication`；no-enhancement fallback 记录空维度和审计边界；旧 payload 缺字段仍能 schema validate。
- Sub agent 使用情况：尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮把上一轮 CLI 叙事沉淀为机器可消费 `.ai` 契约，为后续 existing Harness triage、maturity review 或 self-improve 排序候选打基础，但不混入维护入口排序或 LLM prompt 迁移。
- 可执行验收标准及验证方式：schema unit 覆盖新字段和旧 payload 兼容；candidate generation unit 覆盖 architecture / risk / sensor / no-enhancement；asset writer unit 覆盖 YAML 和 Markdown；guided integration 覆盖真实 init candidate report；compileall、diff check 和 fast regression 作提交前验证。
- 完成内容：新增 `src/harness_builder_agent/tools/candidate_maturity_impact.py`；更新 `WeaponLibraryCandidate` schema、`llm_enhancement_candidates.py` Markdown 输出和 `guided_candidate_review.py` 复用 helper；更新 unit / integration tests；新增本轮 spec / plan。
- 验证结果：RED tests 先因缺少 maturity fields 失败；实现后 targeted tests 8 passed，相关 guided integration 1 passed，compileall 通过，`git diff --check` 通过；`scripts/test-fast.sh` 455 passed。
- Self-Harness Gate：长期工程文档无需更新；未新增 todo；下一轮候选 gap 包括 existing Harness triage 消费 candidate maturity impact，或在 acceptance 外部前置满足后统一 push。

## 2026-06-01 Guided 候选审查成熟度影响提示

- North Star 模块：Init CLI Experience、Maturity-driven Preview、候选资产审核、渐进式交互。
- init North Star 旅程阶段：Guide / Sensor 候选审查、写入前 Harness 设计预览、review-only 候选治理。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo；上一轮 Gate 候选包括候选审查成熟度解释增强和 push / 远端同步。写入前 preview 已能对内置 weapon 展示关联成熟度、阻断和下一阶段贡献，但 LLM candidate 审查只展示类型、作用和 evidence，没有说明它与 Guides / Risk Control / Sensors / Verification 成熟度差距的关系。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 中逐项审查 LLM 提出的 Guide / Sensor 候选时，我可以看到每个候选预计补齐的成熟度维度、对下一阶段基线的贡献和 review-only 边界，从而更有依据地决定接受、拒绝、备注或保持候选。
- 当前代码 gap：`guided_candidate_review.py` 只负责候选呈现和 `CandidateDecision` 构造，缺少 maturity-driven 解释；`WeaponLibraryCandidate` schema 也没有 maturity fields。
- 关键决策 / 取舍：新增确定性 `candidate_maturity_impact_lines()`，从 `candidate_type`、`id`、`title`、`rationale` 和 evidence 推导保守 CLI 提示；不修改 `WeaponLibraryCandidate` schema、不修改 LLM candidate generation、不修改 writer 或 benchmark。
- Assumptions / risks：确定性映射较粗，因此只作为用户可读审查提示，不作为机器契约；风险类关键词命中时提示 Risk Control，其余 Guide candidate 只提示 Guides 上下文。
- 边界情况 / 失败模式：`llm-guide-no-enhancement-001` 输出审计边界而非成熟度提升；Sensor candidate 输出 Sensors / Verification；所有候选都明确保持 review-only，接受只记录确认，不自动写入正式 Guide 或 Sensor；不执行 Runtime，不创建 `.ai/task-runs`。
- Sub agent 使用情况：本轮未使用 sub agent；前几轮连续遇到 `agent thread limit reached`，本轮切片范围窄、由主线程完成。
- 价值切分说明：本轮让 LLM 候选审查和写入前 maturity-driven preview 叙事更一致，但不扩大 schema 或生成资产范围。
- 可执行验收标准及验证方式：unit 覆盖 Guide / risk Guide / Sensor / no-enhancement 的成熟度影响提示和 review-only 边界；guided integration 覆盖真实 `init` transcript；compileall、diff check 和 fast regression 作提交前验证。
- 完成内容：`guided_candidate_review.py` 为每个 LLM candidate 输出成熟度影响、下一阶段贡献和 review-only 边界；更新 unit 与 guided integration；新增本轮 spec / plan。
- 验证结果：RED unit / integration 先因缺少成熟度提示失败；实现后 `tests/unit/test_guided_candidate_review.py` 3 passed，相关 guided integration 1 passed，compileall 通过，`git diff --check` 通过；`scripts/test-fast.sh` 453 passed。
- Self-Harness Gate：长期文档事实源无需更新；未新增 schema 或 todo；后续候选 gap 包括是否把 candidate maturity impact 提升为机器契约，或在 acceptance 外部前置满足后统一 push。

## 2026-06-01 Guided 团队规则输入引导增强

- North Star 模块：Init CLI Experience、渐进式交互、用户上下文吸收、工程架构可维护性。
- init North Star 旅程阶段：扫描理解对齐之后的团队规则补充、候选审查前的上下文确认、写入前团队规则约束预览。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo；上一轮 Gate 候选包括团队规则输入体验增强、候选审查成熟度解释增强、push / 远端同步。当前代码已能把团队规则写入 `interaction-decisions.yaml`、`project-context.md`、`human-input-needed.md` 和 completion summary，但输入前提示仍是一句宽泛例子，Maintainer 需要自己想起哪些隐性约束值得补充。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 的团队规则阶段准备补充组织约束时，我可以看到按架构边界、测试策略、安全合规、发布回滚和只读区域分组的输入引导，并继续用一段自然语言提交，从而更容易补充会影响 Guides 与 human-input-needed 的隐性团队规则。
- 当前代码 gap：`_collect_team_rules()` 内联在 `interactive_init.py`，没有 direct unit；输入提示没有把团队规则拆成用户容易扫描的约束类别。
- 关键决策 / 取舍：新增 `guided_team_rules.py` 承接团队规则阶段引导和 prompt；保持原 prompt 文案、单段自然语言输入和 `ContextConfirmation.inline_contexts` 契约，不把未审核团队规则拆成正式 policy 字段。
- Assumptions / risks：分组提示能提升输入质量，但可能让终端略长；本轮保持短句和单 prompt，避免增加交互负担。
- 边界情况 / 失败模式：空输入仍返回空列表；有输入仍返回单条团队规则；团队规则仍进入 review-only 上下文，不伪装成扫描事实或正式 routing policy；不执行 Runtime，不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮是用户可见的 CLI 引导增强，同时顺手收窄主向导状态机边界；不混入 schema、writer 或候选治理语义变化。
- 可执行验收标准及验证方式：unit 覆盖分组提示、有输入返回、空输入返回；guided integration 覆盖分组提示出现在团队规则理解前，并继续验证 context confirmation、project context、routing policy 不漂移；compileall、diff check 和 fast regression 作提交前验证。
- 完成内容：新增 `src/harness_builder_agent/tools/guided_team_rules.py` 与 `tests/unit/test_guided_team_rules.py`；`interactive_init.py` 删除内联 `_collect_team_rules()` 实现；更新本轮 guided init integration、spec 和 plan。
- 验证结果：RED unit 先因缺少模块失败，integration 先因缺少分组提示失败；实现后 new unit 2 passed，相关 guided integration 1 passed，compileall 通过，`git diff --check` 通过；`scripts/test-fast.sh` 452 passed。
- Self-Harness Gate：README / init workflow 已覆盖团队规则、架构、测试、安全、发布等输入方向，本轮无需同步长期规则；未新增 schema 或 todo。下一轮候选 gap 包括候选审查成熟度解释增强，或在 acceptance 外部前置满足后统一 push。

## 2026-06-01 Guided 候选审查模块抽取

- North Star 模块：Init CLI Experience、渐进式交互、候选资产审核、工程架构可维护性。
- init North Star 旅程阶段：Guide / Sensor 候选审查、写入前确认、review-only 候选治理。
- Gap Analysis 摘要：当前 `docs/todos` 无 open todo，`local-unique-capability-migration.md` 已归档为 implemented。本轮候选包括 guided 候选审查边界抽取、团队规则输入体验增强、push / 远端同步。`interactive_init.py` 在 scan / supplement / prewrite / existing Harness action 多轮抽取后仍内联 `_review_candidates()`，同时负责基线呈现、LLM candidate 渲染、Typer prompt 和 `CandidateDecision` 构造。
- 工程信任故事：作为 Harness Builder 维护者，当我继续打磨首次 guided `init` 中 Guide / Sensor 候选审查体验时，我可以在独立候选审查模块中渲染候选、读取用户选择并构造 `CandidateDecision`，从而让主向导状态机只负责编排阶段，并降低后续调整候选治理体验时误伤 scan、团队规则、Workflow 或写入流程的风险。
- 当前代码 gap：候选审查四种选择和 no-candidate 分支只能通过大型 guided integration 间接覆盖；后续如果要增强候选说明、成熟度关联或分组审查，需要继续改主向导文件。
- 关键决策 / 取舍：新增 `guided_candidate_review.py` 承接候选审查呈现与决策构造；`interactive_init.py` 通过 `review_candidates as _review_candidates` 保留兼容入口；不改变候选文案、选项、schema、LLM candidate generation、writer、benchmark 或 Runtime 分工。
- Assumptions / risks：本轮是行为保持型抽取，用户 transcript 不应变化；prompt 注入只用于单元测试，默认路径仍使用 `typer.prompt`。
- 边界情况 / 失败模式：覆盖 no-candidate 无 prompt、`a` 接受、`r` 拒绝、`e` 备注、默认保持候选，以及 empty evidence 显示“暂无”；不执行 Runtime，不创建 `.ai/task-runs`。
- Sub agent 使用情况：按 playbook 尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮不新增用户可见能力，而是保护“LLM 候选保持 review-only -> Maintainer 逐项决策 -> 写入 interaction decisions / candidate report 状态”的治理链路，为后续候选审查体验增强降低成本。
- 可执行验收标准及验证方式：unit 覆盖 baseline 呈现、no-candidate、四种 candidate decision；guided integration 覆盖真实 `init` transcript 和 `interaction-decisions.yaml` / candidate report 状态不漂移；compileall、diff check 和 fast regression 作提交前验证。
- 完成内容：新增 `src/harness_builder_agent/tools/guided_candidate_review.py` 与 `tests/unit/test_guided_candidate_review.py`；`interactive_init.py` 删除内联 `_review_candidates()` 实现；新增本轮 spec / plan。
- 验证结果：RED unit 先因缺少模块失败；实现后 new unit 2 passed，相关 guided integration 1 passed，compileall 通过，`git diff --check` 通过；`scripts/test-fast.sh` 450 passed。
- Self-Harness Gate：长期文档事实源无需更新；未新增 schema 或 todo；下一轮候选 gap 包括团队规则输入体验增强，或在 acceptance 外部前置满足后统一 push。

## 2026-06-01 Guided 补充呈现模块抽取

- North Star 模块：Init CLI Experience、渐进式交互、工程架构可维护性。
- init North Star 旅程阶段：扫描理解对齐、团队规则补充、Workflow 补充、最终确认前的补充影响说明。
- Gap Analysis 摘要：当前没有 open todo；本轮候选包括 guided 补充呈现边界抽取、进一步增强团队规则输入体验、push / 远端同步。上一轮已改善结构化 scan 补充错误恢复，但 `interactive_init.py` 仍约 781 行，团队规则、Workflow 补充、scan 补充回退 / 替换和最终补充影响摘要仍与主向导状态机混在一起。
- 工程信任故事：作为 Harness Builder 维护者，当我继续打磨首次 guided `init` 中团队规则、Workflow 补充和扫描补充返回修改体验时，我可以在独立的补充呈现模块中修改和单测这些 CLI 文案，而不触碰主向导状态机、候选审查或写入流程，从而降低后续改善渐进式协作体验时的回归风险。
- 当前代码 gap：补充呈现 helper 只能通过大型 guided integration 间接测试；后续如果要增强团队规则输入或 Workflow 说明，仍需要改 `interactive_init.py` 主状态机。
- 关键决策 / 取舍：新增 `guided_supplement_presentation.py` 承接 scan / team / Workflow 补充呈现和最终补充影响摘要；`interactive_init.py` 保留下划线 alias 作为兼容 facade；不迁移 prompt 采集函数 `_collect_team_rules()` 和 `_show_workflows()`，避免把输入状态机和显示层一起搬迁。
- Assumptions / risks：本轮是行为保持型重构，用户 transcript 不应变化；风险主要是漏 import 或文案漂移。新增 direct unit 能更快发现插值 / 摘要类错误。
- 边界情况 / 失败模式：不改 LLM、schema、writer、benchmark 或 Runtime；不新增 `.ai` 产物；不改变团队规则和 Workflow 补充的 review-only 边界。
- Sub agent 使用情况：尝试启动 explorer 做只读边界审查，但当前会话返回 `agent thread limit reached`；主线程完成分析、实现和验证。
- 价值切分说明：本轮不新增用户文案，而是保护“用户补充 -> 复述理解 -> 影响说明 -> 返回修改 -> 最终确认”的 guided init 交互链路，为后续团队规则 / Workflow 体验增强降低成本。
- 可执行验收标准及验证方式：新增 unit 覆盖 scan supplement immediate / replacement、team rules back / clear、workflow note immediate / clear 和 supplement impact summary；integration 覆盖 structured scan corrections、scan back replace / clear、team rules clear、workflow note clear；compileall、diff check 和 fast regression 作提交前验证。
- 完成内容：新增 `src/harness_builder_agent/tools/guided_supplement_presentation.py` 与 `tests/unit/test_guided_supplement_presentation.py`；`interactive_init.py` 从 781 行降到 608 行；新增本轮 spec / plan。
- 验证结果：RED unit 先因缺少模块失败；实现后 new unit 5 passed，相关 guided integration 5 passed，compileall 通过，`git diff --check` 通过；`scripts/test-fast.sh` 448 passed。
- Self-Harness Gate：长期文档事实源无需更新；未新增 schema 或 todo；下一轮候选 gap 包括团队规则输入体验增强、候选审查呈现边界抽取，或在 acceptance 外部前置满足后统一 push。

## 2026-06-01 Guided Scan 结构化补充修正提示

- North Star 模块：Init CLI Experience、渐进式交互、仓库理解深度、可审计输入吸收。
- init North Star 旅程阶段：扫描理解对齐、用户补充吸收、写入前 Harness 设计预览。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo，`local-unique-capability-migration.md` 已是 implemented。本轮候选包括结构化 scan 补充修正格式提示、团队规则 / Workflow 补充 renderer 抽取、push / 远端同步。当前 parser 已能说明 invalid `module` / `command` / `risk` 不会进入结构化资产，但缺少用户可复制的正确格式示例；`init-north-star.md` 明确要求结构化修正提供清晰示例和容错提示。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 的扫描对齐阶段输入格式不完整或字段非法的结构化补充时，我可以立即看到该片段没有进入结构化资产，并看到可复制的正确格式示例，从而能低成本修正输入并信任 Harness 没有把错误补充伪装成已验证事实。
- 当前代码 gap：`guided_scan_supplements.py` 的 invalid fragment note 只说明“未进入 ... 只作为自然语言补充保留”，没有告诉用户下一次应该如何写 `stack`、`module`、`command` 或 `risk`。
- 关键决策 / 取舍：格式提示放入 parser 生成的 note，而不是只改 prompt 文案；这样 CLI immediate summary、prewrite preview、`interaction-decisions.yaml` 和后续语义资产都能保留同一条审计诊断。不新增 schema 字段，不改变合法结构化补充行为。
- Assumptions / risks：诊断 note 会比之前更长，但它表达的是结构化补充未生效的事实边界和修正方式；优先级高于保持短句。
- 边界情况 / 失败模式：自然语言补充不被误报；合法结构化补充继续进入 overrides；invalid command 不进入 command catalog；invalid stack 不覆盖 primary stack。
- Sub agent 使用情况：尝试启动 explorer 做只读复核，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮只改善首次 init scan 补充的错误恢复体验，不修改 LLM、schema、writer、benchmark 或 Runtime 分工。
- 可执行验收标准及验证方式：unit 覆盖 invalid stack / module / command / risk 的可用格式提示；integration 覆盖 guided init immediate summary、command catalog 未更新和 `interaction-decisions.yaml` notes 审计；`git diff --check` 与 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：`guided_scan_supplements.py` 增加统一 invalid fragment hint；README 与 `docs/engineering/init-workflow.md` 同步稳定行为；新增本轮 spec / plan。
- 验证结果：RED targeted tests 先因缺少 `可用格式` 失败；实现后 targeted tests 6 passed；`git diff --check` 通过；`scripts/test-fast.sh` 443 passed。
- Self-Harness Gate：长期文档已同步；未新增 schema 或 todo；未触碰 Runtime；下一轮候选 gap 包括团队规则 / Workflow 补充 renderer 抽取、或在 acceptance 外部前置满足后统一 push。

## 2026-06-01 Guided Scan Presentation Renderer 抽取

- North Star 模块：Init CLI Experience、渐进式交互、成熟度叙事、工程架构可维护性。
- init North Star 旅程阶段：扫描发现、扫描关注点分组、扫描后的成熟度初评、用户补充前的理解对齐。
- Gap Analysis 摘要：当前没有 open todo；本轮候选包括 scan presentation renderer 抽取、scan supplement parser 进一步增强友好示例、push 前 full regression / 远端同步。`interactive_init.py` 已拆出 existing Harness action runner / summaries / signals、prewrite preview 和 scan supplement parser，但首次 guided init 的扫描进度、扫描发现、LLM evidence expansion、深度追问、self-check、风险 / 不确定性 / 验证缺口和扫描后成熟度初评仍混在主向导状态机中。
- 工程信任故事：作为 Harness Builder 维护者，当我继续打磨首次 guided `init` 的扫描理解、深度追问和成熟度初评体验时，我可以在独立 `guided_scan_presentation` 模块中修改和单测扫描呈现逻辑，而不触碰主向导状态机，从而降低后续改进用户扫描对齐体验时误伤补充收集、候选审查、确认写入或已有 Harness 维护入口的风险。
- 当前代码 gap：`interactive_init.py` 约 1175 行，scan presentation helpers 与 scan execution、用户补充、候选审查和写入确认混在一起；这些 helper 只能通过大 integration 间接测试。
- 关键决策 / 取舍：新增 `guided_scan_presentation.py` 承接 scan progress、scan findings、attention summary、evidence expansion、followup questions、self-check、maturity snapshot 和 stack label helper；`interactive_init.py` 用 import alias 保留原 `_show_*` / `_risk_*` / `_stack_*` 私有名称，兼容现有和隐藏测试。
- Assumptions / risks：本轮是行为保持型重构；用户可见 transcript 不应变化。搬迁函数较多，风险主要是漏 import 或文案漂移；通过 direct renderer unit、targeted guided integration、compileall、diff check 和 fast regression 控制。
- 边界情况 / 失败模式：不迁移 scan execution / trace、用户补充解析、团队规则、候选审查、Workflow 补充、最终确认或已有 Harness action runner；不修改 schema、LLM、writer、benchmark 或 Runtime 边界。
- Sub agent 使用情况：按 playbook 尝试启动只读 sub agent 审查抽取边界，但当前会话返回 `agent thread limit reached`；本轮由主线程完成分析、实现和验证。
- 价值切分说明：本轮不新增用户文案，而是保护首次 scan 对齐体验的工程边界；后续可以在 renderer 模块内继续优化扫描关注点、深度追问和 maturity snapshot。
- 可执行验收标准及验证方式：unit 覆盖 evidence expansion、风险 / 不确定性 / 验证缺口、maturity snapshot 和 progress callback；integration 覆盖 guided init happy path、scan risk/uncertainty/gap、LLM evidence expansion、followup questions 和 scan supplement 链路。
- 完成内容：新增 `guided_scan_presentation.py` 和 `tests/unit/test_guided_scan_presentation.py`；`interactive_init.py` 从约 1175 行降到约 782 行；新增本轮 spec / plan。
- 验证结果：RED 测试先因缺少 `guided_scan_presentation` 模块失败；实现后 renderer unit 4 passed，renderer + scan supplement unit 8 passed，相关 guided init integration 6 passed；`.venv/bin/python -m compileall` 通过；`git diff --check` 通过；`scripts/test-fast.sh` 442 passed。
- Self-Harness Gate：长期文档事实源无需更新；未新增 schema 或 todo；下一轮候选 gap 包括团队规则 / Workflow 补充 renderer 抽取、scan supplement parser 更友好示例、或 acceptance 环境补齐后统一 push。

## 2026-06-01 Guided Scan 补充解析诊断

- North Star 模块：Init CLI Experience、渐进式交互、仓库理解深度、Maturity-driven Harness 设计预览。
- init North Star 旅程阶段：扫描理解对齐、用户补充吸收、写入前预览。
- Gap Analysis 摘要：当前没有 open todo；本轮对比 init North Star、README、工程规则和 `interactive_init.py` 后发现，扫描补充支持结构化 `module=` / `command=` / `risk=`，但格式不完整时会静默进入 notes，用户可能误以为 command 已进入 command catalog 或 risk 已进入 risk hints。scan presentation renderer 拆分仍有价值，但本轮优先修用户可感知的输入生效边界。远端同步候选因 push 前 full regression 需要 `DEEPSEEK_API_KEY` 与 `.benchmarks/*` 暂不进入本轮。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 的扫描对齐阶段输入结构化补充但格式不完整或字段非法时，我可以立即看到该片段没有进入结构化 project inventory / command catalog / risk hints，只会作为自然语言补充保留，从而避免误以为 Harness 已经吸收了一个实际验证命令或风险区域。
- 当前代码 gap：`_collect_scan_supplement()` 同时负责提示、解析和构造 overrides；非法结构化片段被原样追加到 notes，没有解释结构化生效失败。
- 关键决策 / 取舍：新增 `guided_scan_supplements.py` 作为可单测解析器；合法结构化补充保持原行为，非法结构化片段生成中文诊断 note，明确“未进入结构化补充，只作为自然语言补充保留”。不新增 `GuidedScanOverrides` 字段，不修改 interaction decision schema 或 writer 契约；诊断作为 notes 进入现有审计链路。
- Assumptions / risks：诊断 note 会进入后续语义资产，可能增加少量文本噪声；但它表达的是真实人工输入未结构化生效的边界，优先级高于静默吞掉格式错误。
- 边界情况 / 失败模式：自然语言补充不被误报为结构化错误；非法 `command=` 不生成 `CommandDefinition`；invalid stack 仍保留二次输入体验，二次输入仍非法时才诊断保留为自然语言补充。
- Sub agent 使用情况：按 playbook 尝试启动只读 sub agent 交叉审查本轮 gap，但当前会话返回 `agent thread limit reached`；本轮由主线程完成分析、实现和验证。
- 价值切分说明：本轮只修 scan 补充解析诊断，不修改 LLM、scan reconciler、asset writer、benchmark 或 Runtime 分工；scan presentation renderer 拆分留作下一轮候选。
- 可执行验收标准及验证方式：unit 覆盖合法/非法结构化片段和自然语言补充；integration 覆盖 guided `init` 中非法 `command=` 的 CLI 诊断、未写入 command catalog、interaction-decisions notes 审计。
- 完成内容：新增 `parse_guided_scan_supplement()`；`interactive_init.py` 改为委托解析器；补充 README 与 `docs/engineering/init-workflow.md` 中的稳定行为说明；新增本轮 spec / plan。
- 验证结果：RED 测试先因缺少 `guided_scan_supplements` 模块失败；实现后 targeted `tests/unit/test_guided_scan_supplements.py` 与相关 guided init integration 7 passed；`git diff --check` 通过；`scripts/test-fast.sh` 438 passed。
- Self-Harness Gate：长期文档已同步；未新增 schema；未触碰 Runtime；未新增 todo。下一轮候选 gap：scan presentation renderer 抽取、scan supplement parser 进一步支持更友好的错误提示 / 示例、或在 acceptance 环境补齐后统一 push。

## 2026-06-01 Init Completion 资产概览压缩

- North Star 模块：CLI Experience、Maturity-driven Init、资产生成与审核接管。
- init North Star 旅程阶段：首次初始化、写入后的交付摘要。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo。本轮候选包括首次 init completion 资产概览压缩、继续拆分 `interactive_init.py` 首次 init scan / supplement 交互、push 前 full regression / 远端同步。当前 completion message 已行动优先，用户补充也已压缩，但 `本次已生成` 仍逐项展示 8 行文件 / 目录状态，和短交付摘要目标以及 `优先查看` 段有信息重复。
- 用户故事：作为 Harness Maintainer，当我完成首次 `harness-builder-agent init` 后，我可以在终端 `== 初始化完成 ==` 的 `本次已生成` 段看到 3-4 行按类型分组的资产概览和详细审计入口，而不是一长串文件状态，从而更快确认第一版 Harness 已建立，并把注意力留给当前成熟度、下一步、Benchmark 和优先查看文件。
- 当前代码 gap：`_generated_asset_summary()` 逐项输出项目清单、命令目录、Guides、Sensors、Workflow Skills、成熟度报告、待确认项和生成 trace；缺少资产类型分组、ready count 和缺失项 detail。
- 关键决策 / 取舍：按固定分组展示核心机器契约、语义控制资产、审查 / 经验资产和运行审计入口；每组显示 `ready=<n>/<total>`，缺失时列出最多 3 个 missing detail；完整清单继续由 `.ai/init-summary.md` 和 `.ai/runs/*/artifacts.yaml` 承担。
- Assumptions / risks：Maintainer 在终端摘要中主要需要确认资产类型已经建立；详细逐文件审计可打开持久化材料。过度压缩可能隐藏缺失项，因此保留 ready count 和 missing detail。
- 边界情况 / 失败模式：缺失核心契约或 runs 目录时 completion 显示 missing detail；不改变实际 `.ai` 生成文件、`init-summary.md` 章节、schema、benchmark、LLM 或 Runtime 分工。
- Sub agent 使用情况：尝试启动 explorer 做只读 completion message 审查，但返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮只改善首次 init 完成摘要的信息密度，不混入生成器、benchmark 或 existing Harness 维护入口变更。
- 可执行验收标准及验证方式：unit 覆盖资产概览压缩和 missing detail；guided init integration 覆盖真实 fixture transcript；`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：`_generated_asset_summary()` 改为资产类型概览；README 和 `docs/engineering/init-workflow.md` 同步 completion message 契约；新增本轮 spec / plan；更新 `tests/unit/test_init_summary.py`。
- 验证结果：RED unit 已确认旧 8 行文件清单失败；`tests/unit/test_init_summary.py` 10 passed；targeted guided init integration 3 passed；`git diff --check` passed；`scripts/test-fast.sh` 433 passed。
- Self-Harness Gate：长期文档已同步；不新增 todo。下一轮候选 gap：继续拆分 `interactive_init.py` 首次 init scan / supplement 交互，或在形成完整工作包后执行 push 前 full regression / 远端同步。

## 2026-06-01 Existing Harness Action Runner 抽取

- North Star 模块：CLI Experience、Maturity-driven Init、工程架构可维护性。
- init North Star 旅程阶段：再次进入已有 Harness 的状态感知维护入口、维护动作执行。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo，`local-unique-capability-migration.md` 已是 implemented。本轮候选包括 Existing Harness action runner 抽取、首次 init completion 生成清单进一步紧凑化、push 前 full regression / 远端同步。当前 existing Harness 入口已拆出 action contract、状态 overview、signals 和 action summaries，但 `exit`、`assess`、`improve`、`benchmark`、`recommend-workflow`、`review-candidate`、`review-human-input`、`self-improve`、`reinit` 和 unknown action 的执行分支仍集中在 `interactive_init.py`。
- 工程信任故事：作为 Harness Builder 维护者，当我继续打磨已有 Harness 维护入口的维护动作时，我可以在独立 action runner 模块中执行、测试和审查 `assess`、`improve`、`benchmark`、`recommend-workflow`、`review-candidate`、`review-human-input`、`self-improve` 等动作，从而让 `interactive_init.py` 专注于向导编排和状态展示，并降低后续修改维护动作时误伤首次 init 主流程、trace 或 Runtime 边界的风险。
- 当前代码 gap：`interactive_init.py` 仍有 1694 行，existing Harness action execution 与首次 guided init 扫描、用户补充、写入前预览混在同一文件；维护动作 trace / artifact 语义只能通过大文件间接审查。
- 关键决策 / 取舍：新增 `existing_harness_action_runner.py` 承接 action execution；`interactive_init.py` 只负责 existing Harness 状态读取、overview / signals / triage / menu 渲染和 action normalize；保留私有 helper facade 兼容现有 unit / 隐藏调用；不改变菜单、默认 `exit`、summary 文案、schema、LLM、benchmark 或 Runtime 边界。
- Assumptions / risks：上一轮已抽出 action summaries，本轮主要风险是搬迁时遗漏 trace artifact 或异常路径；通过 direct runner unit 和 existing Harness targeted integration 覆盖。由于当前会话达到 agent thread 上限，sub agent 未能执行独立审查。
- 边界情况 / 失败模式：runner unit 覆盖 `exit`、`reinit`、unknown action 和 human-input 默认 id；integration 覆盖 `assess`、`improve`、`benchmark`、failed benchmark、`recommend-workflow`、`review-candidate` apply、`review-human-input` 和 `self-improve`，防止正式资产覆盖、Runtime 越界或 trace summary 漂移。
- Sub agent 使用情况：尝试启动 explorer 做只读风险审查，但返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮不是用户可见新功能，而是保护“再次运行 init -> 选择维护动作 -> 获得可审计结果”的 existing Harness 维护旅程；它让后续维护动作体验打磨可以在更窄模块内完成。
- 可执行验收标准及验证方式：新增 runner unit；existing Harness targeted integration；`compileall`、`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：新增 `src/harness_builder_agent/tools/existing_harness_action_runner.py`；`interactive_init.py` 的 existing Harness action execution 改为调用 runner；新增 `tests/unit/test_existing_harness_action_runner.py`；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：RED unit 已确认新模块缺失；runner unit 2 passed；existing Harness 相关 unit 9 passed；existing Harness targeted integration 10 passed；`compileall` passed；`git diff --check` passed；`scripts/test-fast.sh` 432 passed。
- Self-Harness Gate：README / init workflow 无需更新，因为用户行为和长期契约未变；不新增 todo。下一轮候选 gap：首次 init completion 生成清单进一步紧凑化，或在形成完整工作包后执行 push 前 full regression / 远端同步。

## 2026-06-01 Existing Harness Action Summary Renderer 抽取

- North Star 模块：CLI Experience、Maturity-driven Init、工程架构可维护性。
- init North Star 旅程阶段：再次进入已有 Harness 的状态感知维护入口、维护动作结果摘要。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo；本轮候选包括 Existing Harness action summary renderer 抽取、Existing Harness action execution 抽模块、首次 init completion 生成清单进一步紧凑化。当前已有 Harness 入口已拆出 actions / status / signals，但 benchmark、workflow recommendation、candidate governance、human-input governance、self-improve 等维护动作完成后的 summary / preview helper 仍内联在 `interactive_init.py`。
- 工程信任故事：作为 Harness Builder 维护者，当我继续打磨已有 Harness 维护入口的各个维护动作时，我可以在独立 action summary renderer 模块中修改和单测 benchmark、workflow recommendation、candidate governance、human-input governance、self-improve 和 improvement candidate 摘要，从而降低触碰主 guided init 编排文件的风险，并确保 Maintainer 选择维护动作后看到的结果摘要不漂移。
- 当前代码 gap：`interactive_init.py` 仍有 1800+ 行，且 `_benchmark_summary()`、`_workflow_recommendation_summary()`、`_candidate_governance_summary()`、`_human_input_governance_summary()`、`_self_improve_summary()`、`_top_improvement_candidate()` 和 candidate apply preview helper 都与 action execution 分支混在一起。
- 关键决策 / 取舍：新增 `existing_harness_action_summaries.py`，只抽取 action result renderer；不搬 action execution 分支，不改菜单、prompt、trace、artifact、summary 文案、schema、LLM、benchmark 或 Runtime 边界；`interactive_init.py` 保留 underscore facade 兼容旧调用。
- Assumptions / risks：action summaries 是执行分支中最稳定、最适合先拆出的纯渲染边界；candidate apply preview 依赖目标文件存在性，因此用 direct unit 和 existing Harness apply integration 验证。
- 边界情况 / 失败模式：benchmark failed summary、Workflow recommendation summary、candidate detail / apply preview、governance summaries、self-improve summary 和 top improvement candidate 都由新 unit 覆盖；workflow_policy candidate 仍只提示专家命令，不允许 guided apply。
- Sub agent 使用情况：本轮未使用 sub agent；当前切片为单模块低风险抽取，主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮不是用户可见新功能，而是保护“选择维护动作 -> 看懂结果摘要 -> 继续治理”的 existing Harness 维护旅程；它为后续 action execution 抽模块降低风险。
- 可执行验收标准及验证方式：新增 unit 覆盖 action summary renderer；existing Harness targeted integration 覆盖 benchmark、recommend-workflow、review-candidate apply preview、review-human-input 和 self-improve；`compileall`、`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：新增 `src/harness_builder_agent/tools/existing_harness_action_summaries.py`；`interactive_init.py` 的 action summary / preview helper 改为薄 facade；新增 `tests/unit/test_existing_harness_action_summaries.py`；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：RED unit 已确认新模块缺失；action summaries unit 4 passed；existing Harness targeted integration 5 passed；`compileall` passed；`git diff --check` passed；`scripts/test-fast.sh` 430 passed。
- Self-Harness Gate：README / init workflow 无需更新，因为用户行为和长期契约未变；不新增 todo。下一轮候选 gap：Existing Harness action execution 抽模块、首次 init completion 生成清单进一步紧凑化，或 push 前 full regression / 远端同步。

## 2026-06-01 Review Human Input 默认待处理项

- North Star 模块：CLI Experience、Maturity-driven Init、Experience & Self-Improve。
- init North Star 旅程阶段：再次进入已有 Harness 的状态感知维护入口、human-input 治理动作。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo；本轮候选包括 review-human-input 默认待处理 interaction id、Existing Harness action execution 抽模块、首次 init completion 生成清单进一步紧凑化。当前 maintenance triage 已能展示 `human_input_scan_followups_pending` 的 count 和首个 interaction id，但进入 guided `review-human-input` 后仍要求 Maintainer 手动复制该 id。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 并选择 `review-human-input` 处理待确认 scan follow-up 时，我可以直接回车接受维护入口推荐的首个 interaction id，从而不用手动复制上方 triage detail，也能完成显式人工复核治理。
- 当前代码 gap：`interactive_init.py` 的 `review-human-input` 分支对 interaction id prompt 使用空默认值，未消费同一入口中已经计算出的 maintenance triage detail。
- 关键决策 / 取舍：默认 id 只来自当前 `build_maintenance_triage()` 返回的 `human_input_scan_followups_pending.detail`；Maintainer 可输入其他 id 覆盖；没有默认 id 时继续显式失败，不猜测、不 silent fallback。
- Assumptions / risks：triage detail 已由 `Questionnaire` schema 读取，足够作为默认 interaction id 的事实来源；Typer prompt 默认值可能影响 transcript，因此测试只要求回车可治理默认 id，不绑定 prompt 样式。
- 边界情况 / 失败模式：本轮不自动关闭全部 follow-up，不跳过 decision / rationale / reviewer prompt，不修改正式 Guides、Sensors、Workflow Skills、配置或 Runtime 产物。
- Sub agent 使用情况：尝试启动 explorer 做只读 gap 审查，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：这是一个小型但完整的 existing Harness 维护入口纵向切片，把“状态信号 -> 推荐动作 -> 默认治理对象”接成低负担操作闭环。
- 可执行验收标准及验证方式：integration 覆盖 interaction id prompt 直接回车仍治理首个待处理 scan follow-up；unit 覆盖默认 id helper 有 / 无 pending detail；`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：`review-human-input` guided action 使用 human-input triage detail 作为默认 interaction id；README 和 `docs/engineering/init-workflow.md` 同步长期契约；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：RED integration 已确认空 interaction id 会失败；默认值 unit 2 passed；目标 review-human-input integration 1 passed；existing Harness 相关 unit 18 passed；existing Harness exit / numbered exit / review-human-input integration 3 passed；`git diff --check` passed；`scripts/test-fast.sh` 426 passed。
- Self-Harness Gate：长期文档已同步；不新增 todo。下一轮候选 gap：Existing Harness action execution 抽模块、首次 init completion 生成清单进一步紧凑化，或 push 前 full regression / 远端同步。

## 2026-06-01 Existing Harness Signal Renderer 抽取

- North Star 模块：CLI Experience、Maturity-driven Init、工程架构可维护性。
- init North Star 旅程阶段：再次进入已有 Harness 的状态感知维护入口。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo；本轮重新读取事实源后，候选包括 existing Harness signal renderer 抽取、completion 生成清单进一步紧凑化、push 前 full regression / 远端同步。当前 existing Harness 入口已经有动作契约和状态 overview 模块，但 benchmark / workflow routing / experience signals 的读取和渲染仍堆在 `interactive_init.py`，和主向导编排、动作执行混在一起。
- 工程信任故事：作为 Harness Builder 维护者，当我继续打磨已有 Harness 维护入口的健康状态、signals 和 triage 体验时，我可以在独立 signal renderer 模块中修改和单测 benchmark / workflow routing / experience signals，从而降低触碰主 guided init 编排文件的风险，并确保 Maintainer 再次运行 `init` 时看到的维护信号不漂移。
- 当前代码 gap：`interactive_init.py` 内联 `_read_benchmark_status()`、`_benchmark_signal_lines()`、`_workflow_routing_status_lines()`、`_experience_status_lines()` 及多个私有 helper；这些 helper 更适合独立 pure-ish renderer 单测。
- 关键决策 / 取舍：新增 `existing_harness_signals.py`，只抽取 signals 读取 / 渲染；不拆 action execution 分支，不改 existing Harness CLI 文案、菜单、triage 排序、schema、LLM、benchmark 或 Runtime 边界。
- Assumptions / risks：signals 是当前维护入口中最适合先拆出的低风险边界；行为等价抽取可能遗漏 schema import 或 helper 依赖，因此用 direct unit、existing Harness integration 和 fast regression 验证。
- 边界情况 / 失败模式：benchmark report 缺失 / failed detail、standard routing risk trigger、experience index、workflow recommendation history、human-input pending signals 都由新 unit 直接覆盖；已有 Harness exit 仍不触发 scan、不覆盖正式资产、不追加首次 init completion summary。
- Sub agent 使用情况：尝试启动 explorer 做只读调研，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮不是用户可见新功能，而是保护“再次运行 init -> 看懂健康信号 -> 选择维护动作”的关键旅程；它让后续维护入口体验迭代更小、更可审查。
- 可执行验收标准及验证方式：新增 unit 覆盖 existing Harness signals；existing Harness exit integration 覆盖 transcript 等价；`compileall`、`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：新增 `src/harness_builder_agent/tools/existing_harness_signals.py`；`interactive_init.py` 删除内联 signal helpers 并改为调用新模块；新增 `tests/unit/test_existing_harness_signals.py`；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：RED unit 已确认新模块缺失；targeted signal unit 3 passed；existing Harness 相关 unit 22 passed；existing Harness exit integration 2 passed；`test_interactive_init_preview.py` + signal unit 14 passed；`compileall` passed；`git diff --check` passed；`scripts/test-fast.sh` 424 passed。
- Self-Harness Gate：README / init workflow 无需更新，因为用户行为和长期契约未变；不新增 todo。下一轮候选 gap：继续拆 existing Harness action execution、completion 生成清单进一步紧凑化，或 push 前 full regression / 远端同步。

## 2026-06-01 Init Completion 用户补充紧凑摘要

- North Star 模块：CLI Experience、Maturity-driven Init、资产生成与审核接管。
- init North Star 旅程阶段：首次初始化、写入后的交付摘要、用户补充消费闭环。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo；本轮重新读取事实源后，候选包括 completion 用户补充紧凑摘要、existing Harness 维护入口模块拆分、push 前 full regression / 远端同步。当前 completion message 已能展示本次吸收的用户补充、source 和事实边界，但每类最多逐条展示 3 条，scan / team / workflow 合计可能达到 9 条，和 `init-north-star.md` 的短交付摘要目标不完全一致。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 中提供多条 scan 修正、团队规则或 Workflow 补充并完成写入后，我可以在终端 `== 初始化完成 ==` 中看到每类补充的条数、一个可读示例、结构化来源和事实边界，从而确认输入已被吸收，同时不用在完成摘要里阅读一长串补充明细。
- 当前代码 gap：`_completion_user_supplement_lines()` 逐条输出每类前 3 条补充；完整细节虽可审计，但 completion message 作为终端主交付说明仍偏长。
- 关键决策 / 取舍：每类补充只展示条数和首条示例；完整细节继续由 `.ai/init-summary.md` 和 `.ai/interaction-decisions.yaml` 承担；保留 source 和事实边界，防止团队规则或 Workflow note 被误读为扫描事实或正式 routing policy。
- Assumptions / risks：终端 completion 中“条数 + 示例 + source”足以确认补充被吸收；如果用户需要逐条审查，必须打开持久化 Markdown / YAML。
- 边界情况 / 失败模式：无人工补充时仍提示后续可在已有 Harness 维护入口补齐；缺少 interaction decisions 时仍显式显示 `interaction_decisions=missing`；shown workflows、source 和事实边界继续保留；不修改 `init-summary.md`、schema、benchmark 或 Runtime。
- Sub agent 使用情况：尝试启动 explorer 做只读调研，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮只改善首次 init completion 的用户补充段长度，不改变用户补充的收集、写入、资产消费或后续治理流程。
- 可执行验收标准及验证方式：unit 覆盖多条 scan / team / workflow 补充时只展示条数和首条示例，不展示后续明细；integration 覆盖真实 guided init completion 仍显示关键示例、source 和事实边界；`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：`_completion_user_supplement_lines()` 改为紧凑摘要；README 和 `docs/engineering/init-workflow.md` 同步 completion 用户补充摘要契约；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：RED unit 已确认旧逐条输出失败；targeted compact unit 1 passed；`tests/unit/test_init_summary.py` 9 passed；targeted guided init integration 1 passed；`git diff --check` passed；`scripts/test-fast.sh` 421 passed。
- Self-Harness Gate：长期文档已同步；不新增 todo。下一轮候选 gap：existing Harness 维护入口模块拆分、completion 生成清单进一步紧凑化，或 push 前 full regression / 远端同步外部前置。

## 2026-06-01 Init Completion 行动优先交付摘要

- North Star 模块：CLI Experience、Maturity-driven Init、资产生成与审核接管。
- init North Star 旅程阶段：首次初始化、写入后的交付摘要。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo；本轮重新读取事实源后，候选包括 completion 行动优先交付摘要、completion 用户补充进一步压缩、existing Harness 维护入口模块拆分。当前 completion message 已包含必要信息，但顺序仍以生成清单开头，`建议下一步`、Benchmark 和优先入口位于中后段，用户要读完整段才知道先做什么。
- 用户故事：作为 Harness Maintainer，当我完成首次 guided `init` 后，我可以在终端 `== 初始化完成 ==` 的前半段先看到当前成熟度、建议下一步、Benchmark 健康度和优先查看入口，从而不用先读完整生成清单和补充审计也能知道下一步应该做什么。
- 当前代码 gap：`render_init_completion_message()` 先渲染 `本次已生成`，再渲染成熟度、证据、用户补充、建议下一步、Benchmark 和入口；这不符合 `init-north-star.md` 对短交付摘要和下一步行动清晰度的优先级。
- 关键决策 / 取舍：只重排 completion message，不改 `.ai/init-summary.md`、schema、benchmark、正式资产生成或 Runtime 边界；保留所有稳定 section 标题，避免破坏用户识别和既有测试定位。
- Assumptions / risks：首次 init 完成后用户最需要先知道当前 L 等级和下一步命令；顺序变更可能影响 transcript 断言，因此用 unit 和 integration 锁定新顺序。
- 边界情况 / 失败模式：benchmark 未运行 / failed 和 human-input 待确认的优先动作继续由上一轮 helper 决定；缺少 interaction decisions 仍显式提示 missing；不执行 benchmark、不覆盖正式资产、不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动 explorer 做只读调研，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮只改善首次 init 完成摘要的信息架构，不压缩用户补充、不拆 existing Harness 入口、不修改 benchmark 或 LLM 链路。
- 可执行验收标准及验证方式：unit 断言 `当前成熟度`、`建议下一步`、`Benchmark 健康度` 和 `优先查看` 均位于 `本次已生成` 前；integration 覆盖 fixture init transcript；`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：`render_init_completion_message()` 调整为行动优先顺序；README 和 `docs/engineering/init-workflow.md` 同步 completion message 顺序契约；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：RED unit 已确认旧顺序失败；targeted unit 1 passed；`tests/unit/test_init_summary.py` 8 passed；targeted integration 2 passed；`git diff --check` passed；`scripts/test-fast.sh` 420 passed。
- Self-Harness Gate：长期文档已同步；不新增 todo。下一轮候选 gap：completion 用户补充进一步压缩、existing Harness 维护入口模块拆分，或 push 前 full regression / 远端同步外部前置。

## 2026-06-01 Existing Harness 维护状态人话摘要

- North Star 模块：CLI Experience、Maturity-driven Init、审查接管。
- init North Star 旅程阶段：再次进入已有 Harness 的状态感知维护入口。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo。本轮重新读取事实源后，候选包括 existing Harness 维护状态人话摘要、首次 init completion summary 视觉紧凑化、existing Harness 维护入口模块拆分。当前维护入口已有中文标题、raw signals、triage guidance 和编号 shortcuts，但核心健康信息仍以 `key=value` 为主，用户需要自行翻译质量门禁、路由和 review backlog 的含义。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以先看到一组中文维护状态摘要，理解质量门禁、Workflow 路由、Experience / review backlog 和推荐下一步，从而不用先阅读 raw `key=value` signals 才知道当前应该处理什么。
- 当前代码 gap：`_handle_existing_harness_entry()` 直接从成熟度 / benchmark 简短行跳到 Benchmark / Workflow / Experience raw signals；缺少面向人的 overview 层。
- 关键决策 / 取舍：新增只读 `existing_harness_status.py` 渲染 overview；摘要从 `BenchmarkReport`、`ExperienceIndex`、`Questionnaire`、`HarnessConfig` 和 `MaintenanceAction` 读取结构化状态，不解析 raw signals；raw signals 和 triage 仍完整保留。
- Assumptions / risks：Maintainer 仍需要 raw signals 做审计和测试定位，因此不删除现有输出；摘要可能与 guidance 轻微重复，本轮控制为 4-5 条概览短句。
- 边界情况 / 失败模式：无 benchmark report 时提示先运行菜单 `4`；failed benchmark 显示 failed check 数；Experience index 缺失时提示 assess / improve；没有 backlog 时提示可按任务运行 recommend-workflow；不执行动作、不覆盖正式资产、不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动 explorer 做只读交叉审查，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮只改善已有 Harness 状态页“先读懂再审计”的 CLI 顺序，不改维护动作执行、不改 benchmark / LLM / Runtime 契约。
- 可执行验收标准及验证方式：unit 覆盖 not-run benchmark、failed benchmark + backlog、healthy state；integration 覆盖 existing Harness `1` exit transcript 包含 overview 且正式资产不变；`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：新增 `render_existing_harness_status_overview_lines()`；已有 Harness 入口在 raw signals 前展示 `维护状态摘要（Maintenance overview）`；README 和 `docs/engineering/init-workflow.md` 同步维护入口 overview 契约；新增本轮 spec / plan。
- 验证结果：targeted unit / integration 5 passed；`git diff --check` passed；`scripts/test-fast.sh` 420 passed。
- Self-Harness Gate：长期文档已同步；不新增 todo。下一轮候选 gap：首次 init completion summary 视觉紧凑化、existing Harness 维护入口模块拆分，或 push 前 full regression / 远端同步外部前置。

## 2026-06-01 Existing Harness 动作契约同源

- North Star 模块：CLI Experience、Maturity-driven Init、审查接管、工程架构。
- init North Star 旅程阶段：再次进入已有 Harness 的状态感知维护入口。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo。本轮重新读取事实源后，候选包括 existing Harness 动作契约同源、completion summary 视觉紧凑化、existing Harness 维护入口模块拆分。当前维护入口已展示 triage guidance、action shortcuts 和 1-9 菜单，但菜单定义、编号映射和输入 normalization 分散在 `interactive_init.py` / `maintenance_triage.py`，后续菜单调整存在编号漂移风险。
- 工程信任故事：作为 Harness Builder 维护者，当我继续增强已有 Harness 维护入口或调整菜单动作时，我可以依赖一份同源动作契约同时驱动菜单、编号快捷提示和用户输入 normalization，从而避免 Maintainer 在 guided `init` 中看到的推荐编号和实际动作发生漂移。
- 当前代码 gap：`interactive_init.py` 维护菜单行和 alias normalization；`maintenance_triage.py` 另有 `EXISTING_HARNESS_ACTION_NUMBERS`；同一个用户可见编号契约重复维护。
- 关键决策 / 取舍：新增 `existing_harness_actions.py` 作为单一动作契约；`interactive_init.py` 保留 underscore facade 兼容既有测试和内部调用；`maintenance_triage.py` 通过共享 helper 查询编号，不再维护独立映射。
- Assumptions / risks：当前 1-9 菜单顺序已经是稳定 CLI 契约，本轮只集中维护不重排；新增模块必须避免反向依赖业务分支，防止循环导入。
- 边界情况 / 失败模式：不改变动作执行语义、不改变默认 `1` exit、不改变 triage 排序、不执行 Runtime、不创建 `.ai/task-runs`、不覆盖正式 Harness 资产；未知 action 仍显示无菜单编号，不能伪造。
- Sub agent 使用情况：尝试启动 explorer 做只读交叉审查，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮不是泛化大重构，而是先把维护入口用户可见动作编号契约收束为后续菜单演进的稳定基础；完整 `_handle_existing_harness_entry()` 模块拆分留给后续。
- 可执行验收标准及验证方式：unit 覆盖菜单行顺序、编号查询、英文 / 中文 alias normalization 和 triage shortcut 共享编号；integration 覆盖 existing Harness `1` exit transcript 仍展示快捷编号且正式资产不变；`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：新增共享动作契约模块；`interactive_init.py` 菜单 / normalization 改为 facade；`maintenance_triage.py` 移除独立编号表；新增本轮 spec / plan / unit tests。
- 验证结果：targeted unit / integration 18 passed；`git diff --check` passed；`scripts/test-fast.sh` 417 passed。
- Self-Harness Gate：无需新增长期产品规则，README 和 `init-workflow.md` 已描述菜单与 shortcuts；本轮只收束实现契约。下一轮候选 gap：首次 init completion summary 视觉紧凑化、existing Harness 维护入口模块拆分，或 push 前 full regression / 远端同步外部前置。

## 2026-06-01 Init Completion 优先下一步

- North Star 模块：CLI Experience、Maturity-driven Init、资产生成与审核接管。
- init North Star 旅程阶段：首次初始化、写入后的交付摘要。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo。本轮重新读取事实源后，候选包括 completion 优先下一步、completion summary 视觉紧凑化、existing Harness 维护入口模块拆分。当前 completion message 已展示 Benchmark 健康度和待确认入口，但 `建议下一步` 只来自 maturity report，用户仍要在多个区块之间自行合成“先跑 benchmark / 处理 failed checks / 处理 human-input”的顺序。
- 用户故事：作为 Harness Maintainer，当我完成首次 guided `init` 后，我可以在终端 `== 初始化完成 ==` 的 `建议下一步` 中直接看到按优先级排序的下一步动作：先运行 benchmark 或查看失败报告，再处理待人工确认，最后参考成熟度建议，从而不用在多个区块之间自己推断行动顺序。
- 当前代码 gap：`render_init_completion_message()` 直接用 `score.recommended_next_steps[:3]` 渲染 `建议下一步`；benchmark not_run / failed 和 questionnaire pending 只在后面的独立区块中显示，没有进入优先动作列表。
- 关键决策 / 取舍：新增 `_completion_next_action_lines()`，只读 `BenchmarkReport` 和 `Questionnaire` schema；最多输出 3 条，benchmark / failed checks 和 human-input 基础治理动作优先，maturity recommended next steps 作为后续补充；不修改 `init-summary.md` 长期 Markdown 章节。
- Assumptions / risks：首次 init 后最稳妥的第一步是运行 benchmark 或修复 failed checks；如果 maturity recommended step 语义相近，可能仍有轻微重复，本轮通过简单去重控制完全相同文本。
- 边界情况 / 失败模式：缺少 benchmark report 时建议运行 benchmark；benchmark failed 时建议查看 report；questionnaire 有问题时建议 human-input 处理入口；不执行 benchmark、不修改正式资产、不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动 explorer 做只读调研，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮只补“完成摘要 -> 下一步行动顺序”的首次 init 交付闭环，不把整体摘要压缩或 existing Harness 模块拆分混入。
- 可执行验收标准及验证方式：unit 覆盖 benchmark not_run、benchmark failed 和 questionnaire pending 的优先动作；integration 覆盖 guided init completion transcript；`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：`render_init_completion_message()` 改用 `_completion_next_action_lines()`；README 与 `docs/engineering/init-workflow.md` 同步 completion 下一步优先级契约；本轮 spec / plan 已写入。
- 验证结果：targeted unit 2 passed；`tests/unit/test_init_summary.py` 8 passed；targeted guided init integration 1 passed；`git diff --check` passed；`scripts/test-fast.sh` 414 passed。
- Self-Harness Gate：长期文档已同步；不新增 todo。下一轮候选 gap：completion summary 视觉紧凑化、existing Harness 维护入口模块拆分，或 push 前 full regression / 远端同步外部前置。

## 2026-06-01 Existing Harness 维护入口分组标题中文化

- North Star 模块：CLI Experience、Maturity-driven Init、审查接管。
- init North Star 旅程阶段：再次进入已有 Harness 的状态感知维护入口。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo。本轮重新读取事实源后，候选包括 existing Harness 维护入口分组标题中文化、completion summary 视觉紧凑化、existing Harness 维护入口模块拆分。当前维护入口已经有 signals、triage、guidance、shortcuts 和编号菜单，但主要分组标题仍是英文，和 `init-north-star.md` 的“默认中文、CLI 是产品界面”原则不完全一致。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以先看到中文分组标题，再按需识别括号中的英文稳定标记，从而更快理解当前健康信号、维护建议和推荐动作。
- 当前代码 gap：`_handle_existing_harness_entry()` 输出 `Benchmark signals`、`Workflow routing signals`、`Experience / review signals`、`Maintenance triage`、`Maintenance triage guidance` 和 `Maintenance action shortcuts`，缺少中文主标题。
- 关键决策 / 取舍：中文标题放在主位置，英文 marker 放在括号中；不翻译每一条 key=value 机器信号，不改变 triage 排序、动作执行、默认 exit、schema、LLM、benchmark 或 Runtime 分工。
- Assumptions / risks：用户主要依靠 section header 扫读维护入口；中文化标题能降低进入门槛。中英混排略长，但保留英文 marker 有助于测试、文档检索和调试。
- 边界情况 / 失败模式：本轮只改 CLI section header；正式 Harness 资产不变；existing Harness 只读 exit 仍不触发 scan、不追加首次 init completion summary。
- Sub agent 使用情况：尝试启动 explorer 做只读调研，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮只补“已有 Harness 状态页导航语言”的小体验切片，不把 completion summary 压缩或维护入口模块拆分混入。
- 可执行验收标准及验证方式：integration 覆盖 existing Harness 只读 exit transcript 中中文标题与英文 marker 同时存在，并保持正式资产快照不变；`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：`interactive_init.py` 的 existing Harness 维护入口标题改为中文优先；新增本轮 spec / plan；更新 transcript 断言。
- 验证结果：targeted guided existing Harness integration 2 passed；`git diff --check` passed；`scripts/test-fast.sh` 413 passed。
- Self-Harness Gate：长期规则无需更新，README / init workflow 已描述维护入口分项 signals，当前变更只是中文主标题；不新增 todo。下一轮候选 gap：completion summary 视觉紧凑化、existing Harness 维护入口模块拆分，或 push 前 full regression / 远端同步外部前置。

## 2026-06-01 Existing Harness 推荐动作编号提示

- North Star 模块：CLI Experience、Maturity-driven Init、审查接管。
- init North Star 旅程阶段：再次进入已有 Harness 的状态感知维护入口。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo，本轮重新读取事实源后，候选包括 existing Harness 推荐动作编号提示、completion summary 视觉紧凑化、existing Harness 维护入口模块拆分。当前维护入口已经展示 top actions、中文 guidance 和 1-9 菜单，但用户仍需把 `benchmark` / `review-human-input` 等动作名手动映射成菜单编号。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口并看到 Maintenance triage 推荐动作时，我可以直接看到推荐动作对应的菜单编号，从而不用在长菜单中手动映射动作名，也能更稳地选择下一步维护动作。
- 当前代码 gap：`render_maintenance_triage_guidance_lines()` 只说明应运行哪个 guided action；`_existing_harness_action_menu_lines()` 在后面单独列编号，没有把 triage top action 与可输入编号连接起来。
- 关键决策 / 取舍：新增 `render_maintenance_triage_menu_hint_lines()`，集中维护 action -> 菜单编号映射；只增强 CLI 文案，不改变 triage 排序、菜单默认值、动作执行语义、schema、LLM 或 Runtime 分工。
- Assumptions / risks：现有 1-9 菜单顺序是稳定用户界面；如果未来编号调整，unit 会防止 shortcuts 漂移。默认仍是 `1` exit，避免推荐提示被误解为自动执行。
- 边界情况 / 失败模式：unknown action 显示当前菜单无直接编号，不伪造 fallback；推荐提示只做选择辅助，不自动执行动作、不覆盖正式 Harness 资产、不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动 explorer 做只读调研，但当前会话返回 `agent thread limit reached`；主线程完成 Current State Gap Analysis、TDD、实现和验证。
- 价值切分说明：本轮只补“维护信号 -> 推荐动作 -> 可输入菜单编号”的已有 Harness 维护入口选择闭环，不把 completion summary 压缩或大模块拆分混入。
- 可执行验收标准及验证方式：unit 覆盖 benchmark / review-human-input / recommend-workflow / unknown action 的编号提示；integration 覆盖 guided existing Harness exit transcript 出现 `Maintenance action shortcuts` 且正式资产不变；`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：`maintenance_triage.py` 新增编号映射和 shortcut renderer；`interactive_init.py` 在 guidance 后输出 `Maintenance action shortcuts`；README、`docs/engineering/init-workflow.md`、本轮 spec / plan 已同步。
- 验证结果：targeted unit 2 passed；完整 `tests/unit/test_maintenance_triage.py` 13 passed；targeted guided existing Harness integration 2 passed；`git diff --check` passed；`scripts/test-fast.sh` 413 passed。
- Self-Harness Gate：长期事实源已同步；不新增 todo。下一轮候选 gap：completion summary 视觉紧凑化、existing Harness 维护入口模块拆分，或 push 前 full regression / 远端同步外部前置。

## 2026-06-01 Init Completion User Supplements

- North Star 模块：CLI Experience、Maturity-driven Init、资产生成与审核接管。
- init North Star 旅程阶段：首次初始化、写入后的交付摘要、用户补充消费闭环。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo。本轮重新读取事实源后，候选包括 completion message 展示本次吸收的用户补充、existing-Harness 维护入口继续拆模块、push / full regression 外部前置。当前 `init-summary.md` 已有 `## 本次吸收的用户补充`，最终确认前 CLI 也会复述补充，但 `== 初始化完成 ==` 主交付摘要只展示生成资产、成熟度、证据缺口、benchmark、入口和待确认问题，用户需要再打开 Markdown 才能确认自己的输入进入最终交付。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 中提供 scan 修正、团队规则或 Workflow 补充并确认写入后，我可以在终端 `== 初始化完成 ==` 主交付摘要中直接看到“本次吸收的用户补充”及其事实边界，从而不用先打开 Markdown 也能确认自己的输入已经进入 Harness 交付链路。
- 当前代码 gap：`render_init_completion_message()` 没有读取 `.ai/interaction-decisions.yaml`，也没有展示 scan notes、team rules、workflow notes 或 shown workflows；缺失 interaction decisions 时终端摘要没有显式提示。
- 关键决策 / 取舍：completion message 直接读取 `InteractionDecisions` schema，不从 Markdown 反向解析；schema 错误继续显式失败，缺文件显示 `interaction_decisions=missing`；不改 `.ai` schema、不改正式资产生成、不改 Runtime 分工。
- Assumptions / risks：终端展示前几条用户补充足以完成主交付确认；完整细节仍在 `.ai/init-summary.md` 和 `.ai/interaction-decisions.yaml`。CLI 摘要变长是主要风险，已限制为短列表和 source / boundary。
- 边界情况 / 失败模式：有补充时展示 scan / team / Workflow 摘要；无补充时说明后续可在已有 Harness 维护入口继续补齐；缺少 `.ai/interaction-decisions.yaml` 时显式提示 missing；团队规则和 Workflow note 不被描述为扫描事实或正式 routing policy。
- Sub agent 使用情况：尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只补“交互输入 -> 写入资产 -> 终端主交付摘要”的可见闭环，不把 completion summary 的样式重排、existing-Harness 模块拆分或 benchmark 变更混入。
- 可执行验收标准及验证方式：unit 覆盖有补充、无补充和缺 interaction decisions；integration 覆盖真实 guided init completion message；完整 guided init integration 和 fast regression 作为提交前验证。
- 完成内容：`render_init_completion_message()` 新增 `本次吸收的用户补充` section；README 和 `docs/engineering/init-workflow.md` 同步长期规则；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：targeted unit 3 passed；`tests/unit/test_init_summary.py` 7 passed；targeted guided integration 2 passed；完整 guided init integration、`git diff --check` 和 `scripts/test-fast.sh` 见提交前验证。
- Self-Harness Gate：长期文档已同步；不新增 todo。下一轮候选 gap：existing-Harness 维护入口继续拆模块、completion summary 的结构化段落复用 / 视觉紧凑化，或 push 前 full regression / 远端同步外部前置。

## 2026-06-01 Prewrite Maturity Storyline

- North Star 模块：CLI Experience、Maturity-driven Init、资产生成与审核接管。
- init North Star 旅程阶段：首次初始化、写入前 Harness 设计预览、最终确认。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo。本轮重新读取事实源后，候选包括写入前成熟度叙事主线、existing-Harness 维护入口继续拆模块、push / full regression 外部前置。当前 prewrite preview 已展示当前等级、写入后预计基线、阻断项、推荐动作和设计预览，但信息分散；用户补充如何影响 maturity preview 与后续 Harness 推荐没有一个确认写入前的 summary。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 的最终确认前查看写入前预览时，我可以先看到一段 L0-L4 成熟度叙事，明确当前从哪里起步、确认写入后建立什么基线、用户补充如何影响成熟度与 Harness 推荐、哪些质量或 Runtime 证据仍需后续动作验证，从而更有信心决定确认、返回修改或取消。
- 当前代码 gap：`show_prewrite_maturity_preview()` 在推荐补齐动作后直接进入设计预览，缺少稳定的 `成熟度叙事主线` section；有无用户补充时都没有用一组 bullets 汇总扫描补充、团队规则、Workflow note 对本轮预览和 review-only 链路的影响。
- 关键决策 / 取舍：只增强 CLI preview 文案，不修改 `.ai` schema、maturity algorithm、正式资产生成、benchmark 或 Runtime 分工；团队规则和 Workflow note 继续保持事实边界，不伪装成扫描事实或正式 routing policy。
- Assumptions / risks：紧凑 storyline 能降低最终确认前的认知成本；CLI 输出变长是主要风险，因此限制为当前等级 / 基线 / 依据 / 用户补充影响 / 未完成边界几条 bullets。
- 边界情况 / 失败模式：无用户补充时明确按扫描证据和内置 Harness 基线预览；有 scan / team rules / workflow note 时分别说明进入 inventory / command catalog / risk hints、Guides / human-input-needed、review-only 交互决策；后续 benchmark 和 Runtime task-run 仍需显式执行。
- Sub agent 使用情况：尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只补“成熟度结论 -> 用户补充影响 -> 写入边界”的最终确认前叙事，不把已有 Harness 维护入口拆分、benchmark 或真实 acceptance 混入。
- 可执行验收标准及验证方式：unit 覆盖有补充和无补充的 `成熟度叙事主线`；目标 guided init integration 和完整 guided init integration 验证 transcript 顺序不漂移；`git diff --check` 和 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：`prewrite_preview.py` 新增 `_show_maturity_storyline()`，在推荐补齐动作后输出 L0-L4 storyline；`tests/unit/test_interactive_init_preview.py` 增加直接断言；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：新增 targeted unit 2 passed；`tests/unit/test_interactive_init_preview.py` 11 passed；目标 guided init integration 3 passed；完整 guided init integration 42 passed；`git diff --check` 和 `scripts/test-fast.sh` 见提交前验证。
- Self-Harness Gate：本轮不需要更新 README / engineering 长期规则，因为 README 已描述写入前成熟度初评和设计预览，行为仍在既有边界内；不新增 todo。下一轮候选 gap：existing-Harness 维护入口继续拆模块、首次 init completion summary 的用户输入影响表达审计，或 push 前 full regression / 远端同步外部前置。

## 2026-06-01 Prewrite Preview Renderer Extraction

- North Star 模块：CLI Experience、Maturity-driven Init、工程架构可维护性。
- init North Star 旅程阶段：首次初始化、写入前 Harness 设计预览、用户补充吸收后的最终确认。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo；本轮重新读取事实源后，候选包括写入前预览渲染抽模块、push / full regression 外部前置、以及继续强化首次 init maturity preview 叙事。当前 `interactive_init.py` 已承载扫描补充、团队规则、Workflow 补充、Guide / Sensor 推荐和 routing preview 的渲染细节，后续每次打磨 prewrite preview 都要改主向导大文件并依赖较慢 integration 定位。
- 工程信任故事：作为 Harness Builder 维护者，当我继续打磨首次 guided `init` 的写入前成熟度与设计预览时，我可以在独立的 prewrite preview renderer 模块中修改和单测 scan 补充、团队规则、Workflow 补充、Guide / Sensor 推荐和 routing 预览，从而降低修改主向导编排文件的风险，并让后续体验迭代更快、更可审查。
- 当前代码 gap：`GuidedScanOverrides`、`_show_prewrite_maturity_preview()`、scan supplement preview、weapon maturity helper 和 partial Harness 判断都在 `interactive_init.py`；预览输出缺少直接 unit，主要依赖完整 guided init transcript。
- 关键决策 / 取舍：本轮只做行为等价抽取，不调整 CLI 文案、不改 `.ai` schema、不改正式资产生成、不改 Runtime 边界；新模块继续使用 `typer.echo`，保留从 `interactive_init.py` 重新导出的 helper 名称以兼容既有测试。
- Assumptions / risks：先抽取 prewrite preview 比整体拆分 `interactive_init.py` 更小、更可验收；`interactive_init.py` 仍然偏大，后续可继续拆 existing-Harness 维护入口或 scan supplement 交互。
- 边界情况 / 失败模式：scan 补充为空时仍输出扫描基线说明；scan 补充存在时必须展示 stack / note / module / command / risk 及事实边界；损坏 schema 或 LLM 行为不在本轮修改范围。
- Sub agent 使用情况：按目标模式尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`；主线程完成代码审查、TDD、实现和验证。
- 价值切分说明：本轮不是用户可见新功能，而是保护“用户补充 -> 设计预览 -> 确认写入”关键旅程的工程信任切片；它为后续 maturity preview 叙事增强和 guided init 体验打磨降低改动风险。
- 可执行验收标准及验证方式：unit 直接验证新 renderer 有 / 无 scan supplement 的输出；完整 preview helper unit 继续通过；目标 guided init integration 和完整 `test_init_on_fixture_projects.py` 通过证明 transcript 行为等价；`git diff --check` 与 `scripts/test-fast.sh` 作为提交前验证。
- 完成内容：新增 `src/harness_builder_agent/tools/prewrite_preview.py`；`interactive_init.py` 删除 prewrite preview 渲染内联实现并改为导入；`tests/unit/test_interactive_init_preview.py` 新增直接 renderer unit；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：新增 targeted unit 2 passed；`tests/unit/test_interactive_init_preview.py` 11 passed；目标 guided init integration 3 passed；完整 guided init integration 42 passed；`git diff --check` 和 `scripts/test-fast.sh` 见提交前验证。
- Self-Harness Gate：本轮不需要更新 README / engineering 长期规则，因为用户行为和契约未变；不新增 todo。下一轮候选 gap：首次 init maturity preview 叙事收敛、existing-Harness 维护入口继续拆模块、或 push 前 full regression / 远端同步外部前置。

## 2026-06-01 Scan Supplement Prewrite Preview

- North Star 模块：CLI Experience、Maturity-driven Init、资产生成与审核接管。
- init North Star 旅程阶段：首次初始化、用户补充吸收、写入前 Harness 设计预览。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo。本轮重新读取事实源后，发现 scan 补充已经会即时复述、更新内存态 inventory / command catalog，并在最终确认摘要中展示影响；但写入前 Harness 设计预览只展示团队规则约束和 Workflow 补充约束，缺少 scan 补充约束，用户需要间接推断自己的模块、命令、风险或自然语言补充是否进入当前设计。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 中补充或修正技术栈、模块、验证命令、风险区域或自然语言 scan 说明时，我可以在写入前 Harness 设计预览中看到这些 scan 补充被列为明确约束，并看到它们将影响哪些 Harness 设计决策，从而在最终确认前确信系统使用了我的输入。
- 当前代码 gap：`_show_prewrite_maturity_preview()` 不接收 `GuidedScanOverrides`，preview 中没有 `扫描补充约束` section；返回 scan 替换后也无法通过最终 preview 直接确认旧补充已被移除。
- 关键决策 / 取舍：只增强 CLI preview，不改 `.ai` schema、不改正式资产生成策略；scan 补充仍标记为用户提供信息，不能伪装成已验证扫描事实。
- Assumptions / risks：preview 展示前 5 条各类补充即可满足确认写入前的审查需要；完整细节仍在最终确认摘要、`interaction-decisions.yaml` 和语义资产中。
- 边界情况 / 失败模式：无 scan 补充时明确按扫描基线生成；返回 scan 替换后最终 preview 只展示当前生效补充，不展示上一版补充。
- Sub agent 使用情况：尝试启动 explorer 做只读审查，但当前线程达到 agent 上限；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只补“scan 补充 -> 写入前设计预览 -> 最终确认”的可见闭环，不把更大 preview 重构、LLM prompt 或 benchmark 变更混入。
- 可执行验收标准及验证方式：integration 覆盖无补充基线说明、结构化 scan 补充的 preview section、返回 scan 替换后的最终 preview 去除旧补充；完整 guided init integration 和 fast regression 作为提交前验证。
- 完成内容：`_show_prewrite_maturity_preview()` 接收 `scan_overrides`，新增 `扫描补充约束` section，展示 stack / notes / modules / commands / risk areas 和影响边界；README 与 init workflow 同步规则；spec / plan 已写入。
- 验证结果：targeted integration 已通过；完整 guided init integration、`git diff --check` 和 `scripts/test-fast.sh` 见本轮提交前验证。
- Self-Harness Gate：本轮不新增 todo；下一轮候选 gap 保留 push/full regression 外部前置、`interactive_init.py` 模块拆分技术债，或继续强化首次 init 的成熟度预览叙事。

## 2026-06-01 Human Input Triage Recommendation

- North Star 模块：CLI Experience、Experience & Self-Improve、Maturity & Evolution。
- init North Star 旅程阶段：再次进入已有 Harness 的状态感知维护入口。
- Gap Analysis 摘要：`docs/todos` 当前没有 open todo；本轮对比 North Star、README、init workflow 和现有代码后，发现 human-input backlog 已能展示状态、guided `review-human-input` 也已存在，但 Maintenance triage 仍只读 benchmark / Experience index，没有把未解决 scan follow-up 排成下一步动作。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 查看已有 Harness 健康状态时，如果 `.ai/questionnaire.yaml` 中存在未解决或部分回应的 scan follow-up，我可以在 top actions 中看到 `review-human-input`、待处理数量和首个 interaction id，从而知道下一步先复核扫描追问。
- 当前代码 gap：`build_maintenance_triage()` 不读取 `Questionnaire` schema；CLI 只能显示 `human_input_scan_followups_partially_addressed` / `unaddressed` 计数，不能推荐治理动作。
- 关键决策 / 取舍：只统计 `scan_followup_confirmation` 的 `unaddressed` 和 `partially_addressed_by_current_scan_supplement`；`reviewed_resolved_by_harness_maintainer` 不再进入 triage；新增 `human_input_scan_followups_pending` triage reason，priority=25，排序在 benchmark 和 candidate governance 之后、workflow recommendation 和 pending improvements 之前。
- Assumptions / risks：首个待处理 interaction id 作为 detail 足够提示起点；完整列表仍在 `.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md`。损坏的 questionnaire 继续显式失败，不做 silent fallback。
- 边界情况 / 失败模式：triage 只推荐动作，不自动执行治理，不关闭追问，不修改正式 Harness 资产，不创建 Runtime 产物。
- Sub agent 使用情况：尝试启动 explorer 做只读审查，但当前线程达到 agent 上限；本轮在 spec 中记录该限制，由主线程完成代码和测试审查。
- 价值切分说明：本轮只补“状态信号 -> triage 推荐 -> guided 治理入口”的路由闭环，不修改 `review-human-input` 治理语义。
- 可执行验收标准及验证方式：unit 覆盖 pending / resolved-only / benchmark-before-human 排序；integration 覆盖已有 Harness 输出 `top_action_2=review-human-input`、reason、count、detail、中文 guidance，并保持不扫描和不覆盖正式资产；README 与 init workflow 同步长期规则。
- 完成内容：`maintenance_triage.py` 读取 `Questionnaire`，统计待复核 scan follow-up 并渲染 `review-human-input` top action 和 guidance；补充 unit / integration 测试；更新 README、init workflow、spec、plan。
- 验证结果：targeted unit 和 targeted integration 已通过；完整 guided init integration、`git diff --check` 和 `scripts/test-fast.sh` 见本轮提交前验证。
- Self-Harness Gate：本轮不新增 todo；下一轮候选 gap 保留“首次 init 用户补充对最终 maturity preview 的可见影响”、push 前 full regression 外部前置，以及继续拆解 `interactive_init.py` 过大带来的维护风险。

## 2026-06-01 Guided Human Input Review 维护入口

- North Star 模块：CLI Experience、Deep Scan Evidence、Maturity & Evolution、资产生成与审核接管。
- init North Star 旅程阶段：已有 Harness 维护入口、human-input 待确认闭环、审查接管。
- Gap Analysis 摘要：当前 `docs/todos/` 没有 open todo，本地旧能力迁移已归档；远端同步候选仍被 push 前 full regression 的外部前置阻塞（缺 `DEEPSEEK_API_KEY` 与 `.benchmarks`），真实 DeepSeek targeted acceptance 也依赖同一前置。重新读取事实源后，本轮选择可本地完成且服务 init 维护入口的 gap：standalone `review-human-input` 已能治理 scan follow-up，但 existing Harness guided `init` 菜单没有该动作。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 并看到 human-input-needed 中存在 scan follow-up 待复核项时，我可以在已有 Harness 维护菜单中选择 `review-human-input`，输入 interaction id、resolved / reopened 决策和理由后，让系统写入可审计治理日志并刷新 human-input 状态，从而不离开 init 维护入口也能关闭或重新打开扫描追问。
- 当前代码 gap：维护入口已展示 questionnaire 状态、scan follow-up resolved / partial / unaddressed 计数和 `.ai/human-input-needed.md#处理方式`，但菜单只能进入 assess / improve / benchmark / recommend-workflow / review-candidate / self-improve / reinit；human-input 治理仍要求用户记住 standalone 命令。
- 关键决策 / 取舍：复用 `review_human_input()` 和 `HumanInputGovernanceLog`，不新增第二套治理逻辑；`resolved` 仍只表示 Maintainer 人工复核完成，不代表 Builder 自动重扫或验证事实；该 guided action 不自动选择 item，仍要求输入稳定 interaction id，避免误关错误追问。
- Assumptions / risks：Maintainer 可以从维护入口状态行或 `.ai/human-input-needed.md#处理方式` 读取 interaction id；菜单动作增多可能增加选择成本，本轮通过编号、英文和中文别名降低记忆成本。
- 边界情况 / 失败模式：未知 interaction id、非法 decision 或空 rationale 继续由现有 human-input governance 显式失败；本轮不重新扫描、不修改正式 Guides / Sensors / Workflow Skills / `harness-config.yaml` / inventory / command catalog，不执行 Runtime、不创建 `.ai/task-runs`。
- Sub agent 使用情况：按目标模式尝试启动 explorer 只读调研接入点，但当前返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮只补齐 `existing Harness status -> guided review-human-input -> governance log -> refreshed questionnaire / human-input-needed -> trace` 的纵向闭环，不把 triage 自动推荐或真实 acceptance 混入同一轮。
- 可执行验收标准及验证方式：unit 覆盖菜单数字和中英文别名；integration 覆盖 guided `init` 选择 `review-human-input` 后写 governance、刷新 questionnaire / human-input Markdown、记录 trace artifacts、正式资产快照不变且不创建 `.ai/task-runs`。
- 完成内容：existing Harness 菜单新增 `7. review-human-input`，`self-improve` / `reinit` 编号后移；guided 分支收集 interaction id、decision、rationale、reviewer 并复用 `review_human_input()`；README、`docs/engineering/init-workflow.md`、spec 和 plan 同步。
- 验证结果：TDD 红测先因 `review-human-input` 未识别失败；实现后目标 unit / human-input governance unit 12 passed；目标 guided integration 2 passed；完整 guided init integration 42 passed；`git diff --check` 通过；`scripts/test-fast.sh` 通过，403 passed。
- Self-Harness Gate：长期文档已同步；`docs/todos/` 暂不新增。下一轮候选 gap：push 前 full regression / 远端同步（需 `DEEPSEEK_API_KEY` 与 `.benchmarks`）、真实 DeepSeek targeted acceptance 验证 Workflow note asset candidate prompt 效果，或维护入口 triage 是否应在 human-input backlog 非零时推荐 `review-human-input`。

## 2026-06-01 Workflow Note 资产候选闭环

- North Star 模块：CLI Experience、Workflow Toolkit、Maturity & Evolution、Experience & Self-Improve、资产生成与审核接管。
- init North Star 旅程阶段：Workflow 设计、用户补充吸收、已有 Harness 维护入口、review-only 自演进候选。
- Gap Analysis 摘要：当前 open todo 为空，旧本地独有能力迁移已归档。本轮重新读取事实源后，guided `init` 的 Workflow note 已能进入 `interaction-decisions.yaml`、`human-input-needed.md` 和 `interaction-workflow-note-review` improvement candidate，但 LLM maturity review / asset candidate prompt 只对 `experience-workflow-recommendation-review` 有专门指引，缺少 Workflow note -> `workflow_policy` asset candidate 的稳定提示契约。候选还包括 push/full regression 和 human-input review 菜单化；本轮选择 Workflow note 资产候选闭环。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 中留下 Workflow 补充说明，并在已有 Harness 入口运行 self-improve 或专家链路时，我可以得到一个以该 Workflow note 为 evidence 的 review-only `workflow_policy` asset candidate，且它必须携带结构化 `WorkflowPolicyPatch`、保持 `pending_harness_maintainer_review`、不修改正式 routing policy，从而把交互式 Workflow 经验推进到可审核的 Harness 演进候选。
- 当前代码 gap：`generate_improvements()` 已生成 `interaction-workflow-note-review`，但 `llm_maturity_review_v2.md` 和 `llm_asset_candidate_v2.md` 没有告诉真实 LLM 如何专门处理该候选；缺少 integration 证明 Workflow note 能在 self-improve 中变成 workflow_policy asset candidate。
- 关键决策 / 取舍：不新增确定性 free-text-to-patch；Workflow note 到 routing patch 的语义判断仍由 LLM asset candidate generator 完成，Python 继续负责 schema、evidence allowlist、safe path、`WorkflowPolicyPatch` 和 review-only 校验；不自动 apply `.ai/harness-config.yaml`。
- Assumptions / risks：Workflow note 是用户 review-only routing signal，不是正式配置；LLM 可能生成过宽 routing rule，因此候选仍需 Maintainer 审核，`review-candidate applied` 会校验 routing invariants，benchmark 继续校验 workflow policy / candidate governance。
- 边界情况 / 失败模式：未知 source candidate、非法 evidence source、非法 workflow policy target 和缺失 patch 仍由现有 parser/schema 拒绝；本轮不执行 Runtime、不创建 `.ai/task-runs`、不扩展 guided workflow_policy apply。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer 调研 Workflow note 到 asset candidate 链路，但当前返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮补齐 `guided init Workflow note -> improvement candidate -> maturity review prompt -> asset candidate prompt -> self-improve package` 的纵向闭环，不把正式候选应用或菜单化混入同一轮。
- 可执行验收标准及验证方式：prompt unit 覆盖 `interaction-workflow-note-review`、`.ai/interaction-decisions.yaml`、`.ai/human-input-needed.md`、review-only 边界和 `workflow_policy_patch` 指引；integration 覆盖 guided `init` 输入 Workflow note 后 existing Harness `self-improve` 生成 workflow_policy candidate，正式资产不变且不创建 `.ai/task-runs`。
- 完成内容：`llm_maturity_review_v2.md` 增加 Workflow note review-only 判断指引；`llm_asset_candidate_v2.md` 增加 Workflow note -> review-only workflow_policy candidate / structured patch 指引；README 和 `docs/engineering/init-workflow.md` 同步边界；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：TDD 红测先因 prompt 缺少 Workflow note 专门指引失败；实现后目标测试 3 passed；相关 LLM unit 31 passed；相关 Workflow note integration 2 passed；完整 guided init integration 41 passed；`git diff --check` 通过；`scripts/test-fast.sh` 通过，402 passed。
- Self-Harness Gate：长期文档已同步；`docs/todos/` 暂不新增。下一轮候选 gap：push 前 full regression / 远端同步、human-input review guided 菜单化、或真实 DeepSeek targeted acceptance 验证 Workflow note asset candidate prompt 效果。

## 2026-06-01 Human Input Follow-up 人工复核治理

- North Star 模块：CLI Experience、Deep Scan Evidence、Maturity & Evolution、资产生成与审核接管。
- init North Star 旅程阶段：深度追问、用户补充吸收、已有 Harness 维护入口、human-input 待确认闭环。
- Gap Analysis 摘要：当前 open todo 为空，旧本地独有能力迁移已归档。本轮重新读取事实源后，scan follow-up 已能区分 `unaddressed` 和 `partially_addressed_by_current_scan_supplement`，但 Maintainer 没有显式动作把已复核追问关闭；候选还包括 Workflow note -> 结构化 workflow policy candidate 和 push 前 full regression。选择本轮是因为它把“scan supplement 可能回应追问”推进到“人工复核可审计关闭 / 重新打开”，且不触碰正式资产或 Runtime。
- 用户故事：作为 Harness Maintainer，当我看到 `.ai/questionnaire.yaml` 中某个 `scan_followup_confirmation` 已被 scan supplement 部分回应后，我可以运行 `review-human-input` 将其标记为 resolved 或 reopened，并在再次进入 guided `init` 时看到 resolved / partial / unaddressed 计数，从而区分已人工关闭、仍待复核和未回应的扫描追问。
- 当前代码 gap：`QuestionnaireQuestion.response_status` 没有 Maintainer resolved 状态；没有 human-input governance schema / CLI；`human-input-needed.md#处理方式` 只建议重新进入 guided scan correction，不能表达已复核边界；已有 Harness 入口不展示 resolved count。
- 关键决策 / 取舍：新增独立 `HumanInputGovernanceLog`，不复用 candidate governance；`resolved` 只表示人工复核完成，不表示 Builder 自动重扫或验证事实；命令只治理已有 `scan_followup_confirmation`，不修改正式 Guides、Sensors、Workflow Skills、`harness-config.yaml`、inventory 或 command catalog。
- Assumptions / risks：Maintainer 可以基于团队知识和现有补充判断追问已解决；为避免误读，README、工程规则、Markdown review boundary 都明确 resolved 不是扫描 evidence 自动补齐。
- 边界情况 / 失败模式：未知 interaction id、空 rationale、缺少 questionnaire、非 scan follow-up 都显式失败；`reopened` 若仍有 `response_sources` 则恢复 partial，否则恢复 unaddressed；本轮不新增 guided 菜单项、不执行 Runtime、不创建 `.ai/task-runs`。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer 审查 human-input governance 接入点，但当前返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮完成 `questionnaire.yaml -> review-human-input -> governance log -> human-input-needed.md -> existing Harness status lines` 的纵向闭环，不把 Workflow policy patch 安全设计混入同一轮。
- 可执行验收标准及验证方式：schema unit 覆盖 resolved status 与 governance log；unit 覆盖 resolved / reopened / invalid target；Markdown unit 覆盖 resolved / partial 处理建议；existing Harness preview unit 覆盖 resolved count；integration 覆盖 CLI 命令更新产物、正式资产快照不变、再次 `init` 输出 resolved count。
- 完成内容：`QuestionnaireQuestion.response_status` 增加 `reviewed_resolved_by_harness_maintainer`；新增 `human_input_governance` schema / tool / CLI；`human-input-needed.md` 展示 follow-up response status 和治理命令；已有 Harness 入口输出 resolved / partial / unaddressed 计数；README、init workflow、spec 和 plan 同步。
- 验证结果：TDD 红测先因缺少 `human_input_governance` schema 失败；实现后目标 unit 7 passed；目标 CLI integration 1 passed；完整 guided init integration 40 passed；`git diff --check` 通过；`scripts/test-fast.sh` 通过，399 passed。
- Self-Harness Gate：长期文档已同步；`docs/todos/` 暂不新增，因为当前没有 open todo，下一轮继续按 `init-north-star.md` 重新做 Gap Analysis。下一轮候选 gap：Workflow note -> 结构化 `workflow_policy` asset candidate 安全设计、push 前 full regression / 远端同步，或 existing Harness human-input review action 是否需要 guided 菜单化。

## 2026-06-01 Workflow 补充改进候选

- North Star 模块：CLI Experience、Workflow Toolkit、Maturity & Evolution、Experience & Self-Improve、资产生成与审核接管。
- init North Star 旅程阶段：Workflow 设计、用户补充吸收、已有 Harness 维护入口、review-only 改进候选。
- Gap Analysis 摘要：当前 open todo 为空，旧本地独有能力迁移已归档。本轮重新读取事实源后，Workflow 补充已经进入 `interaction-decisions.yaml`、project-context 和 human-input-needed，并带有 review-only 结构化边界；但 existing Harness `improve` 只消费 maturity evidence / workflow recommendation review 计数，不能把 guided `init` 收到的 Workflow note 转成可治理候选。候选还包括直接生成结构化 `workflow_policy` asset candidate、follow-up resolved 状态和 push/full regression；本轮选择低风险的 review-only improvement candidate。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 中输入 Workflow 补充说明后，再次进入已有 Harness 并选择 `improve`，我可以在 `.ai/improvement-candidates.yaml` 和 `.ai/evolution-plan.md` 中看到一个 review-only 的 `workflow_policy_update` 候选，引用 `interaction-decisions.yaml` / `human-input-needed.md`，并明确它不会直接修改正式 routing policy，从而让 Workflow 经验进入可审查改进流。
- 当前代码 gap：`generate_improvements()` 不读取 `interaction-decisions.yaml`，`MaturityEvidencePack.maturity_inputs` 也未暴露 `interaction-decisions.yaml` / `human-input-needed.md` 作为后续 evidence allowlist 来源。
- 关键决策 / 取舍：使用 `ImprovementCandidate` 而不是 `AssetCandidateDraft(kind="workflow_policy")`；候选只表达“应审查是否调整 routing policy”，不生成 `WorkflowPolicyPatch`，不修改 `.ai/harness-config.yaml`。
- Assumptions / risks：Workflow note 是用户 review-only 说明，不是扫描事实；后续如需正式 routing rule 变更，仍必须经过 LLM / 人工审查生成结构化 patch 并由 candidate governance 应用。
- 边界情况 / 失败模式：旧 Harness 缺少 `interaction-decisions.yaml` 时 `improve` 不失败，只是不生成该候选；无 note、非 pending review 或非 review-only effect 时不生成候选；本轮不执行 Runtime、不创建 `.ai/task-runs`。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer 调研 Workflow 补充链路，但当前返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮把“Workflow 补充被记录”推进到“Workflow 补充能进入 review-only 改进治理入口”，完成首次 guided init 与 existing Harness improve 之间的一段闭环。
- 可执行验收标准及验证方式：unit 测试覆盖 pending review / review-only note 生成候选和非 review-only 不生成；integration 覆盖 guided init 输入 Workflow note 后 existing Harness `improve` 生成候选、不重新扫描、不覆盖正式资产、不污染 routing policy；maturity evidence 测试覆盖新增 evidence inputs。
- 完成内容：`generate_improvements()` 读取可选 `interaction-decisions.yaml` 并生成稳定 `interaction-workflow-note-review` 候选；`MATURITY_INPUTS` 增加 `.ai/interaction-decisions.yaml` 和 `.ai/human-input-needed.md`；`docs/engineering/init-workflow.md` 固化 review-only 边界；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 unit `tests/unit/test_generate_improvements.py` 4 passed；相关 unit / maturity evidence 7 passed；相关 improve / guided init integration 6 passed；完整 guided init integration 39 passed；`git diff --check` 通过；`scripts/test-fast.sh` 通过，392 passed。
- Self-Harness Gate：长期规则已同步到 `docs/engineering/init-workflow.md`；README 不需要新增细节，因为面向用户的主入口已说明 `improve` 生成 review-only 候选且 Workflow policy apply 需要结构化 patch；`docs/todos/` 暂不新增。下一轮候选 gap：更完整的 Workflow note -> 结构化 `workflow_policy` asset candidate 安全设计、follow-up Maintainer resolved 状态、或 push 前 full regression / 远端同步。

## 2026-06-01 Questionnaire Follow-up 回应状态契约

- North Star 模块：CLI Experience、Deep Scan Evidence、Maturity & Evolution、资产生成与审核接管。
- init North Star 旅程阶段：深度追问、用户补充吸收、已有 Harness 维护入口、机器可读交互状态。
- Gap Analysis 摘要：当前 open todo 为空。本轮重新读取事实源后，上轮已把 scan follow-up 的“本轮补充可能已部分回应”写入 reason，但机器仍只能解析自然语言；已有 Harness 维护入口只能统计 scan confirmation 总数，不能区分 partially addressed / unaddressed follow-up。候选还包括 Workflow note review-only routing candidate 和 push 前 full regression；本轮选择先补 questionnaire 的机器回应状态契约。
- 工程信任故事：作为 Harness Maintainer，当我再次运行 guided `init` 查看已有 Harness 的 human-input 信号时，我可以看到 scan follow-up 中有多少项已被上一次 guided `init` 的 scan supplement 部分回应、多少仍待确认；同时后续 Self-Improve / 审计链路可以通过 `questionnaire.yaml` 的结构化字段读取该状态，而不是解析自然语言 reason。
- 当前代码 gap：`QuestionnaireQuestion` 没有 `response_status` / `response_sources`；`build_questionnaire()` 只把 partial response 写入 reason；`_human_input_needed_status_lines()` 只显示 scan confirmation 总数。
- 关键决策 / 取舍：新增默认兼容字段 `response_status=unaddressed` 和 `response_sources=[]`；matching scan supplement 时写入 `partially_addressed_by_current_scan_supplement` 和稳定 sources；不新增 resolved 状态，不删除追问，不改变正式扫描事实。
- Assumptions / risks：partial response 只表示“当前补充可能回应”，不是 Maintainer 已确认解决；自然语言 notes 不进入 `response_sources`，避免机器消费不稳定 source。
- 边界情况 / 失败模式：旧 questionnaire payload 通过默认值兼容；unrelated risk 不回应 test evidence follow-up；本轮不修改 LLM self-check、workflow policy candidate、Runtime 或 benchmark。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer 审查最小安全路径，但当前返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮将上一轮 human-readable 状态升级为 schema 契约，并把状态带到已有 Harness 维护入口，形成跨首次 init 和再次进入 init 的闭环。
- 可执行验收标准及验证方式：schema 测试覆盖旧 payload 默认值和 partial 状态；human confirmation unit 覆盖 matching / unrelated supplement；existing Harness preview unit 覆盖 partial / unaddressed 计数；guided integration 覆盖生成的 questionnaire 字段。
- 完成内容：`QuestionnaireQuestion` 增加 `response_status` / `response_sources`；`build_questionnaire()` 写入结构化 partial response；维护入口输出 scan follow-up partial / unaddressed 计数；本轮 spec / plan 和工程规则已同步。
- 验证结果：新增目标测试先按 TDD 失败；实现后目标 schema / human confirmation / preview / guided integration 6 passed；相关 writer / schema / human confirmation / preview / guided integration 12 passed；完整 guided init integration 38 passed；`git diff --check` 通过；`scripts/test-fast.sh` 通过，389 passed。
- Self-Harness Gate：README 暂不需要暴露 schema 细节；`docs/todos/` 暂不新增。下一轮候选 gap：Workflow note review-only routing candidate 安全设计、push 前 full regression / 远端同步，或更完整的 follow-up Maintainer resolved 状态。

## 2026-06-01 Scan Follow-up 补充状态标注

- North Star 模块：CLI Experience、Deep Scan Evidence、Maturity & Evolution、资产生成与审核接管。
- init North Star 旅程阶段：深度追问、用户 scan 补充吸收、human-input 待确认闭环。
- Gap Analysis 摘要：当前 open todo 为空。本轮重新读取事实源后，scan follow-up、LLM 二次自检和结构化 scan supplement 都已存在，但 `build_questionnaire()` 只消费 scan metadata，不消费 `InteractionDecisions.scan_confirmation`；因此用户在同轮 guided `init` 中补充 `module` / `command` / `risk` 后，`.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md` 仍会把相关追问表现为完全未处理。候选还包括 Workflow note review-only routing candidate 和 push 前 full regression；本轮选择先补齐 follow-up 与当前补充之间的待复核标注。
- 用户故事：作为 Harness Maintainer，当扫描阶段出现深度追问且我在同一次 guided `init` 中用结构化 scan supplement 补充相关信息时，我可以在 questionnaire 和 human-input 中看到这些追问已被本轮补充部分回应、但仍需 Maintainer 复核，从而知道系统吸收了输入，同时不会误以为不确定性已经自动关闭。
- 当前代码 gap：`write_initial_assets()` 调用 `build_questionnaire()` 时没有传入 interaction decisions；`scan_followup_confirmation.reason` 只能展示原始 follow-up 和可选 LLM self-check。
- 关键决策 / 取舍：只在 reason 中追加“可能已部分回应”和补充摘要；保持 `scan_followup_confirmation` 存在，保留 `pending_harness_maintainer_review`，不新增 resolved schema，不删除追问，不把用户补充当成扫描 evidence。
- Assumptions / risks：同轮 scan supplement 与 follow-up 的相关性只能保守启发式判断；因此本轮不关闭问题，未来如需机器化 resolved / unresolved 状态应另做 questionnaire schema 设计。
- 边界情况 / 失败模式：无相关补充时不标注；risk 补充不会回应 test evidence follow-up；本轮不修改 LLM self-check、正式 routing policy、Runtime 或 benchmark。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer 审查 scan follow-up 链路，但当前返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮把上一轮结构化 scan supplement 契约接到 human confirmation 产物，形成从追问、用户补充、待复核标注到处理入口的闭环。
- 可执行验收标准及验证方式：unit 测试覆盖 matching / unrelated supplement；guided integration 覆盖 questionnaire、human-input 和 interaction-decisions 对齐；`Questionnaire` schema 校验产物。
- 完成内容：`build_questionnaire()` 接收 `interaction_decisions`，根据 follow-up trigger / affects 保守匹配 scan supplement 并追加待复核标注；`write_initial_assets()` 传入 decisions；工程规则、spec 和 plan 已同步。
- 验证结果：新增测试先按 TDD 失败；实现后 `tests/unit/test_human_confirmation.py tests/unit/test_interaction_decisions.py` 20 passed，目标 guided integration 3 passed，完整 `tests/integration/test_init_on_fixture_projects.py` 38 passed，`git diff --check` 通过，`scripts/test-fast.sh` 通过，387 passed。
- Self-Harness Gate：README 暂不需要暴露该内部待复核细节；`docs/todos/` 暂不新增。下一轮候选 gap：Workflow note review-only routing candidate 安全设计、push 前 full regression / 远端同步，或 follow-up resolved schema 的长期契约设计。

## 2026-06-01 扫描补充结构化决策契约

- North Star 模块：CLI Experience、Deep Scan Evidence、Maturity & Evolution、Experience & Self-Improve、资产生成与审核接管。
- init North Star 旅程阶段：扫描理解对齐、用户补充吸收、机器可读交互决策、写入前 Harness 设计预览。
- Gap Analysis 摘要：当前 open todo 为空。本轮重新读取事实源后，scan / rules / workflow 的返回修改和即时反馈链路已经比较完整；但 `interaction-decisions.yaml` 对 scan 补充仍只记录 notes 和 primary stack override，结构化 `module` / `command` / `risk` 修正只散落在 project inventory、command catalog 或语义资产中。候选还包括 Workflow note review-only routing candidate 和 push 前 full regression；本轮选择先补齐扫描补充的机器决策契约。
- 工程信任故事：作为后续 Self-Improve / 审计链路维护者，当 Harness Maintainer 在 guided `init` 中用 `module=...`、`command=...` 或 `risk=...` 修正扫描理解时，我可以在 `interaction-decisions.yaml` 中读取结构化的模块、验证命令、风险区域、影响范围和“用户补充待审，不是已验证扫描事实”的边界，从而稳定消费这些输入，而不是解析自由文本 notes 或误判它们已经由扫描证据验证。
- 当前代码 gap：`ScanConfirmation` 没有结构化 modules / commands / risk_areas，也没有 scan impact scopes、review 状态或 fact effect；`accepted_interactive_decisions()` 无法把结构化 scan supplement 写入交互决策。
- 关键决策 / 取舍：扩展 `ScanConfirmation` 默认兼容字段；根据补充类型写入 project inventory、command catalog、Sensors、workflow routing review、human-input-needed 和 maturity preview 等影响范围；有补充时统一标记 `pending_harness_maintainer_review` 与 `user_supplied_correction_review_required`。不从自然语言 notes 推断结构化补充，不修改正式 routing policy。
- Assumptions / risks：结构化 scan correction 是高信号用户输入，适合进入机器契约；旧 `interaction-decisions.yaml` 通过默认值兼容；未来若要关闭 questionnaire follow-up，需要单独设计 resolved 状态。
- 边界情况 / 失败模式：无 scan 补充时不制造 pending review；自然语言补充仍只作为 notes；本轮不执行 Runtime、不创建 `.ai/task-runs`、不改 LLM 或 benchmark。
- Sub agent 使用情况：尝试启动只读 explorer 审查 scan supplement contract，但当前返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮把已存在的结构化补充消费链路补成可审计机器契约，不改变资产生成语义；Workflow note routing candidate 继续保留为后续安全设计。
- 可执行验收标准及验证方式：unit 测试覆盖 schema、writer 默认值、structured supplement impact contract 和 Markdown；guided integration 覆盖 `interaction-decisions.yaml` 中 modules / commands / risk_areas / impact scopes / review status / fact effect，并确认既有 inventory、command catalog、Guide、Sensor、init-summary 行为不退化。
- 完成内容：`ScanConfirmation` 增加结构化 scan supplement 和 impact 字段；`accepted_interactive_decisions()` 接收并写入结构化 scan supplement；decision Markdown 展示 scan impact 和结构化补充；guided init 传入 `GuidedScanOverrides` 的 modules / commands / risk areas；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 unit / integration 测试 13 passed；完整 guided init integration 37 passed；`git diff --check` 通过；`scripts/test-fast.sh` 通过，384 passed。
- Self-Harness Gate：`docs/engineering/init-workflow.md` 已同步稳定契约；README 暂不需要描述 schema 细节；`docs/todos/` 暂不新增。下一轮候选 gap：Workflow note review-only routing candidate 的安全设计、scan follow-up 被用户补充后的 resolved / still pending 状态、push 前 full regression / 远端同步。

## 2026-06-01 Guided Init 团队规则与 Workflow 返回修改提示

- North Star 模块：CLI Experience、Maturity & Evolution、Workflow Toolkit、资产生成与审核接管。
- init North Star 旅程阶段：团队规则补充、Workflow 设计、最终确认返回修改、写入前 Harness 设计预览。
- Gap Analysis 摘要：当前 open todo 为空。本轮重新读取事实源后，scan 返回修改已经具备替换 / 清空 / old-current 可见语义；团队规则和 Workflow 补充虽然能替换最终资产中的旧输入，但返回修改前不说明新输入替换旧输入，直接回车清空也没有可见确认。候选还包括 Workflow note review-only routing candidate 和 push 前 full regression；本轮选择同一 final confirmation 纠错旅程下的 rules / workflow 提示补齐。
- 用户故事：作为 Harness Maintainer，当我在最终确认阶段返回修改团队规则或 Workflow 补充时，我可以在重新输入前看到新输入会替换上一版内容、直接回车会清空上一版内容，并在清空后看到系统确认最终资产不会保留旧内容，从而不用担心旧团队规则或旧 Workflow note 悄悄进入正式 `.ai` 资产。
- 当前代码 gap：`back -> rules` 和 `back -> workflow` 分支直接重新收集输入；有旧输入时没有替换提示，清空旧输入时没有清空确认。
- 关键决策 / 取舍：新增 team rules / workflow note 返回修改 notice 和清空 summary；无旧输入时不增加噪音；不新增 schema，不生成候选，不修改 workflow routing policy。
- Assumptions / risks：返回 rules / workflow 后重新输入表达替换上一版而不是累计追加；未来如果支持多条规则逐项编辑，需要升级为更明确的 add/remove/edit 交互。
- 边界情况 / 失败模式：返回后直接回车会清空旧 rules / workflow note，并最终不写入 project-context、human-input-needed 或 interaction decisions notes；本轮不执行 Runtime、不创建 `.ai/task-runs`。
- Sub agent 使用情况：尝试启动只读 explorer 审查 back->rules/workflow 路径，但当前返回 `agent thread limit reached`；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮和上一轮 scan diff preview 一起完成 final confirmation 三类用户补充的纠错信任链路：scan / rules / workflow 都能说明替换或清空边界。
- 可执行验收标准及验证方式：integration 测试覆盖 back->rules 替换提示和清空确认、back->workflow 替换提示和清空确认，并断言旧内容不进入 interaction-decisions、project-context、human-input-needed 或 routing。
- 完成内容：`interactive_init.py` 增加四个 CLI helper；`docs/engineering/init-workflow.md` 固化 rules / workflow 返回修改语义；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 integration 测试 4 passed；完整 guided init integration 37 passed；相关 unit 测试 17 passed；`git diff --check` 通过；`scripts/test-fast.sh` 通过，380 passed。
- Self-Harness Gate：README 当前无需细化该纠错提示；`docs/todos/` 暂不新增。下一轮候选 gap：Workflow note review-only routing candidate 的安全设计、push 前 full regression / 远端同步前置条件，或用户补充对成熟度推荐的更深消费。

## 2026-06-01 Guided Init Scan 返回修改差异预览

- North Star 模块：CLI Experience、Deep Scan Evidence、资产生成与审核接管。
- init North Star 旅程阶段：扫描理解对齐、用户补充吸收、最终确认返回修改、写入前 Harness 设计预览。
- Gap Analysis 摘要：当前 open todo 为空，迁移工作包已经归档。上一轮 Gate 候选包括 Workflow note review-only routing candidate、scan correction diff preview 和 push 前 full regression。本轮核验发现 `workflow_policy` candidate 必须有结构化 `WorkflowPolicyPatch`，不应从自由文本 Workflow note 推断 routing patch；scan 返回修改已经有替换 / 清空语义和资产断言，但缺少稳定的 old/current 差异预览。因此本轮选择 scan 返回修改差异预览。
- 用户故事：作为 Harness Maintainer，当我在最终确认阶段返回 `scan` 并用新模块、验证命令或风险区域替换上一版扫描补充时，我可以在 CLI 中看到稳定的“上一版补充 / 当前生效补充”差异预览，并确认最终写入只会使用当前补充，从而不用在长输出里手动比对旧输入是否仍然生效。
- 当前代码 gap：`_show_scan_back_revision_notice()` 只在重新输入前展示上一版摘要；新输入后只显示新补充理解，没有明确 old/current 替换结果。
- 关键决策 / 取舍：新增 `_show_scan_supplement_replacement_summary()`，复用 `_scan_override_brief()`；只有上一版和当前版都非空时输出替换结果；清空路径保持 `扫描补充已清空`；不修改 schema、LLM、writer、benchmark 或正式资产语义。
- Assumptions / risks：返回 scan 重新输入表达替换而非累计；简短摘要可能截断长输入，完整新补充仍在紧邻的 `扫描补充理解` 区块展示。
- 边界情况 / 失败模式：直接回车清空上一版补充时不输出替换结果；本轮不执行 Runtime、不创建 `.ai/task-runs`、不默认运行 benchmark。
- Sub agent 使用情况：本轮范围集中在单个 CLI 纠错路径，未拆出独立并行子任务；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮补齐 `back -> scan` 的最后一段用户可见纠错信任链路：提示替换 / 清空、展示 old/current 差异、最终资产只保留当前补充。
- 可执行验收标准及验证方式：integration 测试覆盖替换路径输出 `扫描补充替换结果`、上一版 legacy 和当前 final 摘要、最终写入只使用当前生效补充；清空路径继续输出 `扫描补充已清空`；既有资产断言证明旧补充不进入 project inventory、command catalog、Guides、Sensors 或 init summary。
- 完成内容：guided init 在 `back -> scan` 新补充非空时输出替换结果；risk 摘要包含 path 和 reason；`docs/engineering/init-workflow.md` 固化规则；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标替换 / 清空 integration 测试通过；完整 guided init 和 fast regression 见本轮提交前验证。
- Self-Harness Gate：README 当前不需要细化该纠错提示；`docs/todos/` 暂不新增。下一轮候选 gap：Workflow note review-only routing candidate 的安全设计、push 前 full regression / 远端同步前置条件，或继续审视用户补充如何更深影响成熟度推荐。

## 2026-06-01 团队规则结构化影响契约

- North Star 模块：CLI Experience、Maturity & Evolution、Experience & Self-Improve、资产生成与审核接管。
- init North Star 旅程阶段：团队规则补充、用户输入吸收、写入前 Harness 设计预览、可审计决策记录。
- Gap Analysis 摘要：当前 open todo 为空，迁移工作包已经归档为 implemented。团队规则已经有即时复述、preview 约束和语义资产写入，但 `ContextConfirmation` 只有路径和自由文本；相比上一轮已增强的 `WorkflowConfirmation`，后续 self-improve / 审计仍无法稳定判断团队规则影响范围、review 状态和是否改变正式 policy。候选还包括 Workflow note review-only routing candidate、scan correction diff preview 和 push 前 full regression；本轮选择先补齐团队规则的机器契约。
- 工程信任故事：作为后续 Self-Improve / 审计链路维护者，当 Harness Maintainer 在 guided `init` 中输入团队规则、架构约束或测试策略时，我可以在 `interaction-decisions.yaml` 和 `human-input-needed.md` 的 interaction decision 摘要中读取机器可验证的影响范围、review-only 状态和“不直接修改正式 policy”的边界，从而稳定消费团队规则补充，而不是解析自由文本或误以为它已经改变正式 workflow routing。
- 当前代码 gap：`ContextConfirmation` 没有 `impact_scopes`、`review_status` 或 `policy_effect`；`accepted_interactive_decisions()` 无法把团队规则写成可审计影响契约。
- 关键决策 / 取舍：在 `ContextConfirmation` 上新增默认兼容字段；有 context path 或 inline 团队规则时写入 `interaction_decisions`、`project_context`、`human_input_needed`、`guide_context`、`review_only_team_context` impact scopes，`pending_harness_maintainer_review` 和 `context_only_no_direct_policy_change`；无 context 输入 / 非交互未确认路径保持默认。当前不生成 team context candidate，不修改正式 `harness-config.yaml`。
- Assumptions / risks：`--context` 文件和 inline 团队规则都属于 Harness Maintainer 提供的团队上下文，应进入 review-only 审计边界；未来若团队规则需要变成正式 policy，必须另走候选治理或结构化 patch。
- 边界情况 / 失败模式：无团队规则时不制造 pending review；团队规则自由文本不得进入正式 workflow routing policy；本轮不执行 Runtime、不创建 `.ai/task-runs`。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer 审查 context contract，但当前返回 `agent thread limit reached`，未能使用子代理；主线程完成调研、TDD、实现和验证。
- 价值切分说明：本轮把团队规则 CLI 闭环向机器契约推进一步，并与 Workflow note impact contract 对齐；不跨入候选生成或 policy apply。
- 可执行验收标准及验证方式：unit 测试覆盖 schema 字段、默认值、interactive 写入和 decision-log Markdown；guided init integration 覆盖 `interaction-decisions.yaml` 的结构化字段，并断言正式 routing policy 未被团队规则文本污染。
- 完成内容：`ContextConfirmation` 增加 `impact_scopes`、`review_status`、`policy_effect`；interactive decisions 有 context 输入时写入结构化 impact；`interaction_decisions_markdown()` 展示 context impact 字段；`docs/engineering/init-workflow.md` 固化契约；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 unit / integration 测试通过；完整 guided init 片段和 fast regression 见本轮提交前验证。
- Self-Harness Gate：README 当前不需要描述 schema 细节；`docs/todos/` 暂不新增。下一轮候选 gap：Workflow note review-only routing candidate、scan correction diff preview、或 push 前 full regression / 远端同步前置条件。

## 2026-06-01 Workflow 补充结构化影响契约

- North Star 模块：CLI Experience、Workflow Toolkit、Maturity & Evolution、资产生成与审核接管。
- init North Star 旅程阶段：Workflow 设计、用户补充吸收、写入前 Harness 设计预览、可审计决策记录。
- Gap Analysis 摘要：当前 open todo 为空。本轮重新读取事实源后，Workflow 补充已经有即时复述、preview 约束和返回修改能力，但 `WorkflowConfirmation` 仍只有自由文本 notes；后续 self-improve / 审计如果要理解这条输入，只能解析 Markdown 或 note 文本。候选还包括 scan correction diff preview、Workflow note 生成 review-only routing candidate 和 push 前 full regression；本轮选择先把 Workflow 补充影响范围、review-only 状态和 routing policy 边界固化为 Pydantic 机器契约。
- 工程信任故事：作为后续 Self-Improve / 审计链路维护者，当 Harness Maintainer 在 guided `init` 中输入 Workflow 补充说明时，我可以在 `interaction-decisions.yaml` 中读取机器可验证的影响范围、review-only 状态和“不直接修改正式 workflow routing policy”的边界，从而让后续智能改进和人工审查稳定消费这条输入，而不是解析自由文本或误以为它已经改变正式路由策略。
- 当前代码 gap：Workflow note 的影响范围只存在于 CLI 文案和 preview 文案中，机器契约没有 `impact_scopes`、`review_status` 或 `routing_policy_effect`。
- 关键决策 / 取舍：在 `WorkflowConfirmation` 上新增默认兼容字段；有 note 时写入 `interaction_decisions`、`project_context`、`human_input_needed`、`review_only_workflow_note` impact scopes，`pending_harness_maintainer_review` 和 `review_only_no_direct_policy_change`；无 note / 非交互路径保持 `not_required` / `not_applicable`。本轮不生成 routing candidate，不修改正式 `harness-config.yaml` routing policy。
- Assumptions / risks：新字段让新生成的 `interaction-decisions.yaml` 更详细，旧文件通过默认值兼容；未来如果要把 workflow note 候选化，应基于该 review-only contract 设计单独治理流程。
- 边界情况 / 失败模式：有 Workflow note 时正式 routing policy 不能包含 note 文本；无 Workflow note 时不制造 pending review；本轮不执行 Runtime、不创建 `.ai/task-runs`。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer，但当前返回 `agent thread limit reached`，未能使用子代理；主线程完成调研与验证。
- 价值切分说明：本轮把已完成的 Workflow 补充 CLI 闭环向机器契约推进一步，为后续 self-improve / candidate governance 复用打基础；不跨入高风险的 workflow policy candidate 生成。
- 可执行验收标准及验证方式：unit 测试覆盖 schema 字段、默认值和 decision-log Markdown；guided init integration 覆盖 `interaction-decisions.yaml` 的结构化字段，并断言正式 routing policy 未被 workflow note 文本污染。
- 完成内容：`WorkflowConfirmation` 增加 `impact_scopes`、`review_status`、`routing_policy_effect`；guided init 有 note 时写入结构化 impact；`interaction_decisions_markdown()` 展示影响字段；`docs/engineering/init-workflow.md` 固化契约；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 unit / integration 测试通过；相关 guided init 和 fast regression 见本轮提交前验证。
- Self-Harness Gate：README 当前不需要描述 schema 细节；`docs/todos/` 暂不新增。下一轮候选 gap：Workflow note review-only routing candidate、scan correction diff preview、或 push 前 full regression / 远端同步前置条件。

## 2026-06-01 Guided Init Scan 返回修改清空提示

- North Star 模块：CLI Experience、Deep Scan Evidence、资产生成与审核接管。
- init North Star 旅程阶段：扫描理解对齐、用户补充吸收、最终确认返回修改、写入前 Harness 设计预览。
- Gap Analysis 摘要：当前 open todo 为空，本地独有能力迁移包已 implemented。上一轮已经修复 `back -> scan` 的资产替换语义，最终 `.ai` 资产只保留最新 scan 补充；但 CLI 没有在返回 scan 时说明“新输入替换上一版补充，直接回车清空上一版补充”，直接回车清空也没有可见确认。候选还包括 scan correction diff preview、Workflow note 结构化 impact schema 和 push 前 full regression；本轮选择最贴近纠错信任感的 scan 返回修改提示。
- 用户故事：作为 Harness Maintainer，当我在最终确认阶段返回 `scan` 修改或撤销扫描补充时，我可以在重新输入前看到新输入会替换上一版扫描补充、直接回车会清空上一版补充，并在清空后看到系统确认后续预览和资产将回到扫描基线，从而避免误以为旧补充仍会影响正式 Harness。
- 当前代码 gap：`back -> scan` 已基于 clean baseline 重新应用最新补充，但没有用户可见的替换 / 清空边界说明。
- 关键决策 / 取舍：新增 `_has_scan_overrides()`、返回修改提示和清空确认；提示只在上一版 scan 补充非空时展示；本轮不实现逐项 diff preview，不修改 schema、writer、LLM、benchmark 或 Runtime 契约。
- Assumptions / risks：返回 scan 表达重新填写扫描补充，直接回车应清空上一版补充并回到扫描基线；如果未来需要累计补充或部分删除，应另行设计 add / remove / diff 交互。
- 边界情况 / 失败模式：首次 scan 补充为空时不新增额外提示；返回 scan 后输入新补充仍走即时理解 / 影响说明；返回 scan 后直接回车会输出 `扫描补充已清空`。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer，但当前返回 `agent thread limit reached`，未能使用子代理；主线程完成调研与验证。
- 价值切分说明：本轮只补用户纠错路径的可见语义，和上一轮资产替换语义形成完整“返回修改 -> 替换或清空 -> 预览刷新 -> 写入最新资产”闭环；更复杂 diff preview 留给后续。
- 可执行验收标准及验证方式：新增 integration 测试覆盖首次输入 `legacy` scan 补充、最终确认返回 scan 后直接回车清空，断言 CLI 展示替换 / 清空提示和清空确认，且 project inventory、command catalog、interaction decisions、project-context、verification sensor 和 init-summary 不包含旧补充。
- 完成内容：`interactive_init.py` 增加 scan 返回修改提示、清空确认和补充存在性 helper；`docs/engineering/init-workflow.md` 固化返回 scan 的替换 / 清空可见语义；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 integration 测试通过；相关 guided init 测试和 fast regression 见本轮提交前验证。
- Self-Harness Gate：README 已概述 guided init 可返回修改，暂不为这一纠错提示更新；`docs/todos/` 暂不新增。下一轮候选 gap：scan correction diff preview、Workflow note 结构化 impact schema、或 push 前 full regression / 远端同步前置条件。

## 2026-06-01 Guided Init Scan 返回修改替换补充

- North Star 模块：CLI Experience、Deep Scan Evidence、资产生成与审核接管。
- init North Star 旅程阶段：扫描理解对齐、用户补充吸收、最终确认返回修改、正式资产写入。
- Gap Analysis 摘要：当前 open todo 为空。本轮重新读取事实源后发现 `back -> scan` 虽然会重新收集 scan 补充，`interaction-decisions.yaml` 也只记录最新 `scan_overrides`，但 `_apply_scan_overrides()` 会直接追加到已经变异的 `inventory / commands`，导致用户撤销或替换的旧 module / command / risk 仍可能进入 project inventory、command catalog、Guides、Sensors 和 init summary。候选还包括清空补充边界、scan diff preview、Workflow note schema / routing candidate；本轮选择资产正确性更强的 scan override 替换语义。
- 用户故事：作为 Harness Maintainer，当我在最终确认阶段发现扫描补充写错并返回 `scan` 重新输入模块、验证命令或风险区域时，我可以确信最终生成的 project inventory、command catalog、Guides、Sensors 和 init summary 只包含最新补充，而不会继续保留已经撤销的旧补充，从而避免错误扫描事实污染正式 Harness 资产。
- 当前代码 gap：scan 完成后没有保留 clean baseline；初次补充和返回 scan 都在当前内存态上追加，旧补充无法被替换。
- 关键决策 / 取舍：扫描完成后保存 `base_inventory` / `base_commands` 深拷贝；每次应用 scan overrides 都从 baseline 深拷贝后重新应用最新补充；不新增 schema，不改 writer，不增加 scan diff preview 文案。
- Assumptions / risks：返回 scan 重新输入表达“替换上一版 scan corrections”，与 rules / workflow 返回修改语义一致；如果未来需要累计多轮补充，应显式设计 add/remove/diff 交互。
- 边界情况 / 失败模式：返回 scan 后直接回车会清空旧 scan 补充并回到扫描基线；本轮未单独加清空测试，但实现语义支持；本轮不执行 Runtime、不创建 `.ai/task-runs`、不默认运行 benchmark。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer，但当前返回 `agent thread limit reached`，未能使用子代理；主线程完成调研与验证。
- 价值切分说明：本轮修复 scan 补充返回修改的正式资产正确性；CLI diff preview 和更复杂的累计补充模型留给后续 Gap Analysis。
- 可执行验收标准及验证方式：新增 integration 测试先证明旧 `legacy` module / command / risk 会残留，再修复为最终 `project-inventory.json`、`command-catalog.yaml`、project-context、verification sensor 和 init-summary 只包含最新 `final` 补充。
- 完成内容：`interactive_init.py` 增加基线深拷贝和 `_scan_state_with_overrides()`；`back -> scan` 基于 clean baseline 展示和收集补充；`docs/engineering/init-workflow.md` 固化替换语义；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 integration 测试通过；commit 前 fast regression 见本轮提交前验证。
- Self-Harness Gate：README 当前只概述 `back` 返回修改，不细化 scan override 替换语义，暂不更新；`docs/todos/` 暂不新增。下一轮候选 gap：back -> scan 直接回车清空补充测试、scan correction diff preview、Workflow note 结构化 impact schema、或 push 前 full regression 先决条件。

## 2026-06-01 Guided Init Workflow 补充返回修改

- North Star 模块：CLI Experience、Workflow Toolkit、资产生成与审核接管。
- init North Star 旅程阶段：Workflow 设计、写入前 Harness 设计预览、最终确认返回修改。
- Gap Analysis 摘要：当前 open todo 为空。上一轮已经让 Workflow 补充在输入后即时复述，并进入写入前 preview；本轮重新读取事实源后发现 final confirmation 的 `back` 只支持 scan / rules / candidates，用户看到 workflow note 错误时不能只返回修改，容易被迫取消整次 init 或接受错误人工说明。候选还包括 Workflow note 结构化 impact schema、Workflow note 生成 review-only routing candidate、push 前 full regression，同步排序后选择最小但完整的 back->workflow 纠错闭环。
- 用户故事：作为 Harness Maintainer，当我在最终确认阶段发现 Workflow 补充写错或需要清空时，我可以输入 `back` 并选择 `workflow` 只返回 Workflow 补充步骤，重新输入后看到即时影响和设计预览刷新，并且最终 `.ai` 资产只保存最新 Workflow 补充，从而不用取消整次 init 或接受错误人工说明。
- 当前代码 gap：`_confirm_summary()` 的返回菜单不包含 workflow，loop 也没有 workflow 分支；未知返回目标会回到最终确认，后续输入可能被误当成确认。
- 关键决策 / 取舍：只新增 `workflow=Workflow补充` 返回目标，复用 `_show_workflows()` 和 `_show_workflow_note_immediate_summary()` 替换内存态 `WorkflowConfirmation`；不重新跑 candidate review、不修改 routing policy、不新增 schema。
- Assumptions / risks：workflow note 在正式写入前只在内存态中，因此可以安全替换；如果未来 workflow note 影响 routing candidate，需另行设计结构化候选治理。
- 边界情况 / 失败模式：返回 workflow 后直接回车可以清空旧 note；最终持久化以最后一次 `WorkflowConfirmation.notes` 为准；本轮不执行 Runtime、不创建 `.ai/task-runs`、不默认运行 benchmark。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer，但当前返回 `agent thread limit reached`，未能使用子代理；主线程完成调研与验证。
- 价值切分说明：本轮和上一轮共同补齐 Workflow 补充的“输入 -> 即时理解 -> preview -> 可返回修改 -> 写入最新结果”闭环；结构化 impact schema 和 routing candidate 留给后续 Gap Analysis。
- 可执行验收标准及验证方式：新增 integration 测试断言 `back` 菜单包含 `workflow=Workflow补充`、`Workflow 补充理解` 出现两次、最终 preview 展示新 note，且 `interaction-decisions.yaml`、project-context、human-input-needed 只包含新 note 不包含旧 note。
- 完成内容：`interactive_init.py` 支持 `back -> workflow`；`docs/engineering/init-workflow.md` 固化最终确认返回 workflow 的规则；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 integration 测试通过；commit 前 fast regression 见本轮提交前验证。
- Self-Harness Gate：README 只说明摘要阶段可 back 返回修改，未细化每个返回目标，暂不更新；`docs/todos/` 暂不新增。下一轮候选 gap：Workflow note 结构化 impact schema、Workflow note review-only routing candidate、或 push 前 full regression 先决条件。

## 2026-06-01 Guided Init Workflow 补充影响与预览

- North Star 模块：CLI Experience、Workflow Toolkit、资产生成与审核接管。
- init North Star 旅程阶段：Workflow 设计、用户补充吸收、写入前 Harness 设计预览。
- Gap Analysis 摘要：当前 open todo 为空，旧本地独有能力迁移包已 implemented。本轮候选包括 Workflow 补充即时影响与预览、`WorkflowConfirmation` 结构化 impact 字段、Workflow note 参与 routing candidate 生成，以及 push 前 full regression / 远端同步。选择 Workflow 补充即时影响与预览，因为 scan 补充和团队规则已经有即时反馈，workflow note 仍只在最终确认阶段汇总，写入前 preview 也没有说明它不会直接修改正式 routing policy。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 中给推荐 Workflow 输入补充说明时，我可以在进入写入前确认前立即看到 Harness Builder 如何理解这条补充、它会进入哪些审计 / 人工确认资产，并在写入前 Harness 设计预览中看到它不会直接修改正式 workflow routing policy，从而确认我的 workflow 经验被记录和用于审查，但不会越过候选治理边界。
- 当前代码 gap：`_show_workflows()` 收集 `WorkflowConfirmation.notes` 后直接进入 preview / final summary；`_show_prewrite_maturity_preview()` 只展示团队规则、Guides、Sensors 和 routing rules，没有 Workflow 补充约束区块。
- 关键决策 / 取舍：新增 `Workflow 补充理解` / `Workflow 补充影响` 即时 CLI 区块，并在写入前 preview 增加 `Workflow 补充约束`；不新增 schema，不改变 `HarnessConfig.default()`，不让自由文本直接修改正式 workflow routing policy。
- Assumptions / risks：现有 writers 已把 workflow note 写入 `interaction-decisions.yaml`、project-context 和 human-input-needed；本轮只补用户可见闭环。输出长度会增加，因此即时区块仅在用户输入 workflow note 时展示。
- 边界情况 / 失败模式：无 Workflow 补充时不输出即时区块，preview 明确按内置 bugfix / lightweight / standard routing 预览；需要改变正式 routing policy 时仍必须经过候选治理或结构化 workflow policy patch；本轮不执行 Runtime、不创建 `.ai/task-runs`、不默认运行 benchmark。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer，但当前返回 `agent thread limit reached`，未能使用子代理；主线程完成调研与验证。
- 价值切分说明：本轮补齐 scan/team rules/workflow 三类用户补充链路中的最后一个即时反馈缺口；结构化 impact schema 和 workflow routing candidate 生成留给后续 Gap Analysis。
- 可执行验收标准及验证方式：integration 测试断言 `Workflow 补充理解` 和 `Workflow 补充影响` 位于 workflow prompt 后、成熟度预览前；写入前 preview 包含 `Workflow 补充约束`、具体 note、review-only 和不直接修改正式 workflow routing policy 的边界；既有资产持久化断言继续覆盖 interaction decisions、project-context 和 human-input-needed。
- 完成内容：`interactive_init.py` 增加 Workflow 补充即时反馈和 preview 小节；`docs/engineering/init-workflow.md` 固化规则；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 integration 测试通过；commit 前 fast regression 见本轮提交前验证。
- Self-Harness Gate：README 已描述 guided init 会展示推荐 Workflow 和设计预览，暂不为每个即时反馈区块更新；`docs/todos/` 暂不新增。下一轮候选 gap：workflow note 结构化 impact schema、Workflow note 生成 review-only routing candidate、或 push 前 full regression 先决条件。

## 2026-06-01 Guided Init 团队规则影响与预览

- North Star 模块：CLI Experience、Maturity & Evolution、资产生成与审核接管。
- init North Star 旅程阶段：团队规则补充、用户输入吸收、写入前 Harness 设计预览。
- Gap Analysis 摘要：当前 open todo 为空。本轮重新读取事实源后，候选 gap 包括团队规则输入后的即时影响说明、`InteractionDecisions.context_confirmation` 结构化 impact 字段、团队规则参与候选生成或 weapon selection、以及 push 前 full regression 先决条件。选择团队规则即时影响与预览，因为当前 `inline_contexts` 已进入 interaction decisions、project-context 和 human-input-needed，但 CLI 在团队规则输入后直接进入候选审查，写入前 preview 也不展示这些规则如何约束本次 Harness 设计。
- 用户故事：作为 Harness Maintainer，当我在 guided `init` 中输入团队代码规范、架构约束或测试策略时，我可以在进入候选审查前立即看到系统如何理解这些规则、它们会进入哪些 Harness 资产，并在写入前设计预览中看到这些规则作为 Guides / human-input-needed / 后续审查的约束，从而确认团队隐性规则已经进入本次 Harness 设计，而不是只在最终确认阶段被动记录。
- 当前代码 gap：`_collect_team_rules()` 只返回文本；即时反馈缺失。`_show_prewrite_maturity_preview()` 只展示 Guides、Sensors 和 Workflow routing，没有团队规则约束区块。
- 关键决策 / 取舍：新增 `团队规则理解` / `团队规则影响` 即时 CLI 区块，并在写入前 preview 增加 `团队规则约束`；不新增 schema，不声称团队规则已改变 maturity score，也不直接修改正式 workflow routing policy。
- Assumptions / risks：Guide writer 和 human-input writer 已消费 `context_confirmation.inline_contexts`；本轮只提升用户可见闭环。输出长度会增加，因此仅在有团队规则时输出即时区块。
- 边界情况 / 失败模式：无团队规则时不输出即时区块，preview 明确按扫描证据和内置基线生成；团队规则是用户提供约束，不是扫描事实；本轮不执行 Runtime、不创建 `.ai/task-runs`、不默认运行 benchmark。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer，但当前返回 `agent thread limit reached`，未能使用子代理；主线程完成调研与验证。
- 价值切分说明：本轮补齐团队规则输入到候选审查 / 设计预览之间的可见闭环；结构化 impact schema 和团队规则驱动候选生成留给后续 Gap Analysis。
- 可执行验收标准及验证方式：integration 测试断言 `团队规则理解` 和 `团队规则影响` 位于团队规则输入后、`建议生成的规则` 前；写入前 preview 包含 `团队规则约束`、具体规则、Guides、human-input-needed 和不直接修改正式 workflow routing policy 的边界。
- 完成内容：`interactive_init.py` 增加团队规则即时反馈和 preview 小节；`docs/engineering/init-workflow.md` 固化规则；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 integration 测试通过；commit 前 fast regression 见本轮提交前验证。
- Self-Harness Gate：README 当前描述 guided init 会收集团队规则和展示设计预览，但未细到每个即时反馈区块，暂不更新；`docs/todos/` 暂不新增。下一轮候选 gap：context impact schema、团队规则参与候选生成、或 push 前 full regression 先决条件。

## 2026-06-01 Guided Init 扫描补充即时影响说明

- North Star 模块：CLI Experience、Maturity & Evolution、资产生成与审核接管。
- init North Star 旅程阶段：扫描理解对齐、成熟度初评、用户补充吸收、设计预览前的渐进式协作。
- Gap Analysis 摘要：旧 61 提交迁移 todo 已 implemented 并归档，当前 open todo 为空。本轮重新读取事实源后，候选 gap 包括扫描补充后的即时影响说明、`InteractionDecisions` 结构化 impact 字段、团队规则即时影响说明和 push 前 full regression 先决条件。选择扫描补充即时影响说明，因为当前代码已经把补充写入 inventory、command catalog、interaction decisions 和正式语义资产，但 CLI 直到最终确认才系统性复述影响；这晚于 North Star 要求的“收到补充后立即整理理解并说明影响”。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 的扫描理解阶段补充自然语言说明或结构化 `module` / `command` / `risk` 修正时，我可以在进入团队规则和设计候选前立即看到 Harness Builder 如何理解这些补充、会如何影响成熟度缺口判断和后续 Harness 推荐，从而确认交互输入已经进入决策链路，而不是只在最终确认阶段被动展示。
- 当前代码 gap：`_apply_scan_overrides()` 已在团队规则和候选审查前更新内存态 inventory / commands，但用户可见的“已吸收补充 / 补充影响”只在 `_confirm_summary()` 中出现。
- 关键决策 / 取舍：新增 scan 补充后的即时 CLI 区块，复用现有 `GuidedScanOverrides` 和 `human_overrides` 数据流，不新增 schema 字段；最终确认摘要保留，作为写入前复核。
- Assumptions / risks：当前补充应用发生在 weapon selection、candidate generation 和写入前 maturity preview 之前，因此即时复述能准确表达后续影响；文案增加会拉长 guided CLI，本轮限制为两个短区块。
- 边界情况 / 失败模式：无补充时不输出新区块；结构化命令 source 是否真实存在仍由 hard gate command evidence benchmark 负责；本轮不执行 Runtime、不创建 `.ai/task-runs`、不默认运行 benchmark。
- Sub agent 使用情况：按目标模式尝试启动只读 explorer，但当前返回 `agent thread limit reached`，未能使用子代理；主线程完成调研与验证。
- 价值切分说明：本轮只补扫描补充这一处最关键的前置决策反馈；团队规则即时反馈和结构化 impact schema 留给后续 Gap Analysis。
- 可执行验收标准及验证方式：integration 测试断言 `扫描补充理解` 和 `扫描补充影响` 出现在 `你的补充或修正` 之后、`\n团队规则` 之前，并包含自然语言 note、module、command、risk、成熟度缺口判断、Guides、Sensors、Workflow 升级和 human-input-needed；同时保留产物中的 inventory / command catalog / init summary / project context / verification 断言。
- 完成内容：`interactive_init.py` 在首次 scan supplement 和 back-to-scan 修改后立即输出补充理解与影响说明；`docs/engineering/init-workflow.md` 固化该规则；本轮 spec / plan 已写入 `docs/superpowers/`。
- 验证结果：目标 integration 测试通过；commit 前 fast regression 见本轮提交前验证。
- Self-Harness Gate：README 当前已说明 guided init 支持自然语言和结构化修正，暂不需要更新；`docs/todos/` 无需新增，因为后续候选可继续由下一轮 Current State Gap Analysis 评估。下一轮候选 gap 包括团队规则即时影响说明、结构化 impact schema、以及已有 14 个本地 commit push 前的 full regression 先决条件处理。

## 2026-06-01 本地独有能力迁移收口归档

- North Star 模块：Goal Mode / 工程治理、CLI Experience、Deep Scan Evidence、Benchmark / Review Intelligence。
- init North Star 旅程阶段：已有 Harness 维护；扫描理解可解释；质量门禁解释；后续目标模式选题。
- Gap Analysis 摘要：当前唯一 open todo 是“本地独有 / 更细能力合并与迁移”。连续迁移切片已经覆盖 Existing Harness 维护入口、human input 待确认回访、Benchmark / Workflow routing signals、init-summary 待确认入口、hard gate source path、risk context consistency、project-context evidence context、scan-report evidence visibility、init-summary evidence audit、content quality detail 和 evidence reason preservation。剩余 `test/risk/API/llm_requested` 顶层 inventory 字段恢复属于新的 schema 设计，benchmark failed check 系统性全量审计属于后续 hardening，不应继续阻塞旧 61 提交迁移包收口。
- 用户故事：作为 Harness Maintainer，当我查看 `docs/todos/` 和当前 git 分支时，我可以看到本地独有 / 更细能力迁移工作包已经收口归档、已迁移切片和未迁移取舍清楚可追溯，并且本地 commits 已通过 full regression 后同步远端，从而后续目标模式可以回到 init North Star 的新 gap，而不是继续围绕旧 61 提交做重复合并。
- 当前代码 gap：无产品代码 gap 进入本轮；问题在于迁移 todo 仍 open，会持续牵引目标模式围绕旧分支迁移，而不是进入新的 Current State Gap Analysis。
- 关键决策 / 取舍：不恢复旧顶层 evidence schema 字段作为迁移阻塞项；不保留两套 guided init / scanner / completion summary；不把 benchmark failed detail 全量审计塞入本迁移 todo。后续若需要，按新的具体 milestone 进入。
- Assumptions / risks：归档表示本地 61 提交迁移工作包已有第一版完整收口，不表示 Harness Builder 已达到最终 North Star；push 前 full regression 可能受真实 DeepSeek、真实仓库或网络影响，失败时不 push。
- Sub agent 使用情况：尝试启动只读 explorer 审查归档判断，但当前环境返回 `agent thread limit reached`；本轮由主线程完成审计、文档收口和验证。
- 价值切分说明：本轮是工作包治理切片，目的是建立干净远端基线和后续选题边界；不改 CLI、schema 或 Runtime。
- 可执行验收标准及验证方式：todo 状态为 implemented；todo README 无旧迁移 open 项；archive 增加归档记录；fast / full regression 通过后 push。
- 完成内容：`local-unique-capability-migration.md` 增加完成说明；`docs/todos/README.md` 更新当前待办；`archive.md` 增加归档行；新增 closeout spec / plan。
- 验证结果：本地验证和 push 结果见本轮提交后记录。
- Self-Harness Gate：后续候选 gap 回到 init North Star：可重新评估顶层 evidence schema 扩展、benchmark failed detail 系统审计、用户补充如何更深影响成熟度预览与推荐，或 CLI transcript 的下一段真实体验缺口。

## 2026-06-01 Evidence Reason Preservation 迁移

- North Star 模块：Deep Scan Evidence、Benchmark / Review Intelligence、CLI Experience。
- init North Star 旅程阶段：扫描理解可解释；生成资产可审计；质量门禁解释。
- Gap Analysis 摘要：迁移 todo 中 scan evidence 可审计细节仍有 `evidence reason preservation` 未完成。旧备份分支会通过 `_evidence_entry()` 保留 `EvidenceFile.reason`，当前 main 虽然已展示 evidence path、coverage、LLM evidence expansion 和风险路径，但 reconcile 写入 `ProjectInventory` 时会把 key evidence 的 reason 降级为 kind，configs / ci / documents 也常只剩 kind；benchmark 也只校验 path，不校验 reason。
- 用户故事：作为 Harness Maintainer，当我查看 `.ai/scan-report.md`、`.ai/guides/project-context.md` 或 benchmark report 审计扫描 evidence 时，我可以看到每个关键 evidence path 为什么被选中，并且 benchmark 会在 reason 从报告中丢失时指出具体 path，从而判断扫描结论不是只有路径列表，而是有可解释依据。
- 当前代码 gap：`scan_reconciler.py` 没有保留 `EvidenceFile.reason`；`content:scan-report` 和 `content:project-context-evidence-context` 没有 `missing_evidence_reason:<path>` 校验。
- 关键决策 / 取舍：不新增 ProjectInventory 顶层字段；只在现有 evidence / documents / configs / ci_files dict entry 中保留 `reason`。proposal configs / ci_files 如果没有 reason，则从同 path 的 deterministic evidence 补齐；旧 inventory 没有 reason 时不强制失败。
- Assumptions / risks：真实 LLM proposal path 与 deterministic evidence path 不一致时无法补齐 reason；这种情况保留 proposal 原样，不做近似匹配或 silent fallback。
- Sub agent 使用情况：尝试启动只读 explorer 审查旧分支 evidence reason，但当前环境返回 `agent thread limit reached`；本轮由主线程完成旧分支对比、TDD、实现和验证。
- 价值切分说明：本轮只恢复 reason 的扫描调和、语义展示和 benchmark 防漂移，不扩展 test / risk / API / llm_requested 顶层 inventory 字段。
- 可执行验收标准及验证方式：unit 覆盖 reconcile reason 保留和 writer reason 展示；benchmark integration 覆盖 scan-report / project-context 缺 reason 时返回 `missing_evidence_reason:<path>`。
- 完成内容：`reconcile_scan()` 保留 evidence reason；proposal configs / ci_files 补齐 deterministic reason；benchmark 校验 scan-report 和 project-context evidence reason；README、init workflow、LLM contracts、testing strategy、sensor/gate rules、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap：test / risk / API entrypoint / document evidence report visibility 是否需要恢复顶层 schema，或 failed check missing / errors / detail preservation 系统性全量审计。

## 2026-06-01 Content Quality Detail Preservation 迁移

- North Star 模块：Benchmark / Review Intelligence、CLI Experience、Maturity & Evolution。
- init North Star 旅程阶段：已有 Harness 维护；质量门禁解释；语义资产可审计。
- Gap Analysis 摘要：当前唯一 high priority 迁移 todo 仍是本地独有 / 更细能力合并与迁移。scan-report、init-summary、project-context、risk context 和 hard gate command 已逐步保留 missing/errors/weak detail，但 `content:workflow-skills`、`content:guides-quality`、`content:sensors-quality` 和 `content:stack-specific-guides` 仍只返回 `passed=false`，维护者无法从 benchmark report 直接知道缺哪个章节、marker 或 weapon id。
- 用户故事：作为 Harness Maintainer，当我运行 `benchmark` 发现 Guide、Sensor、Workflow Skill 或 stack-specific Guide 内容质量失败时，我可以在 `benchmark-report.yaml` 中看到具体缺失章节、缺失 workflow skill marker 或缺失 weapon id，从而知道应该修哪份语义资产，而不是只看到 `passed=false`。
- 当前代码 gap：四个内容质量 check 的 pass/fail 判断存在，但没有填充 `BenchmarkReport` schema 已支持的 `missing` 字段。
- 关键决策 / 取舍：不新增 schema，不改变 writer 输出，不改变 pass/fail 语义；复用 `missing` 字段承载缺失文件、缺失 marker、缺失章节和缺失 weapon id。
- Assumptions / risks：旧 benchmark report 不会 retroactively 获得 detail；新 report 与维护入口已能消费 `missing`。本轮只覆盖最常见的老内容质量 check，系统性全量审计仍保留为后续 gap。
- Sub agent 使用情况：尝试启动只读 explorer 审查本轮候选，但当前环境返回 `agent thread limit reached`；本轮由主线程完成分析、TDD、实现和验证。
- 价值切分说明：本轮是 failed check detail preservation 的一个纵向小切片，直接保护 benchmark 失败诊断工作流，不混入 scanner schema、writer 生成逻辑或 Runtime。
- 可执行验收标准及验证方式：integration 负向测试断言 Guide 缺章节、standard Workflow Skill 文件缺失、Sensor 缺章节 / hard marker 时，对应 content check 均返回可行动 `missing` detail；stack-specific Guide 缺 weapon id 时返回具体 weapon id。
- 完成内容：`_workflow_skills_check()`、`_guide_quality_check()`、`_sensor_quality_check()` 和 `_stack_specific_guide_check()` 保留 missing detail；README、sensor/gate rules、testing strategy、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap：failed check missing / errors / detail preservation 系统性全量审计，或 evidence reason preservation。

## 2026-06-01 Scan Evidence Failed Check Triage 迁移

- North Star 模块：CLI Experience、Benchmark / Review Intelligence、Maturity & Evolution。
- init North Star 旅程阶段：再次进入已有 Harness；质量门禁解释和维护建议。
- Gap Analysis 摘要：当前迁移 todo 仍 open，上一轮新增 `content:scan-report` 与 `content:init-summary` 后，benchmark report 已保留 missing detail，但已有 Harness 维护入口对这两个新 check id 仍缺少中文 label 和专门 triage reason。本轮候选包括 scan evidence failed check triage、failed check detail preservation 系统审计和 evidence helper 去重，优先选择 scan evidence triage，因为它直接补齐新门禁的用户可见解释。
- 用户故事：作为再次运行 guided `init` 进入已有 Harness 维护入口的 Harness Maintainer，当最近 benchmark 因 `content:scan-report` 或 `content:init-summary` 失败时，我可以在 Benchmark signals 和 Maintenance triage guidance 中看到中文解释、具体 missing detail 和下一步动作，从而知道要补齐 scan-report / init-summary 的扫描证据审计。
- 当前代码 gap：`_benchmark_failed_check_label()` 对 `content:scan-report` 和 `content:init-summary` 返回泛化“查看 benchmark-report.yaml”；`build_maintenance_triage()` 只专门处理 hard gate、risk context 和 project-context evidence，scan evidence 失败被归入泛化 schema/content failed checks。
- 关键决策 / 取舍：不改 BenchmarkReport schema，不改变 benchmark pass/fail；只把两个近期新增的 scan evidence check 专门化为 `reason=scan_evidence_audit_incomplete`，detail 取第一条 missing，完整列表仍在 benchmark report。
- Assumptions / risks：维护入口是已有 Harness 诊断的第一视图；多个 scan evidence check 同时失败时只展示第一条 missing detail，避免 triage 过长。
- Sub agent 使用情况：尝试启动只读 explorer 审查本轮候选，但当前环境返回 `agent thread limit reached`；本轮由主线程完成分析、TDD、实现和验证。
- 价值切分说明：本轮是 failed check detail preservation 的一个小而完整切片，不做全量 benchmark check 审计，也不重构 evidence helper。
- 可执行验收标准及验证方式：unit 覆盖 Benchmark signals 的中文 label / missing detail，以及 Maintenance triage 的 reason/source/detail/guidance。
- 完成内容：为 `content:scan-report`、`content:init-summary` 增加中文 failed check label；Maintenance triage 新增 `scan_evidence_audit_incomplete`；README、init workflow、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit 通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：Runtime 边界未变化；下一轮候选 gap：failed check missing / errors / detail preservation 系统性全量审计，或 evidence helper 去重。

## 2026-06-01 Init Summary Evidence Audit 迁移

- North Star 模块：Deep Scan Evidence、CLI Experience、Maturity & Evolution、Benchmark / Review Intelligence。
- init North Star 旅程阶段：写入后的交付摘要；扫描理解可解释；质量门禁解释。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。project-context 和 scan-report 已经展示并由 benchmark 守住 LLM evidence expansion，但首次交付入口 `.ai/init-summary.md` 还没有摘要化展示 requested/read paths、risk focus、confidence、read file count、rationale 或 coverage selected paths。本轮候选包括 init-summary evidence audit、failed check detail preservation、evidence helper 去重和 evidence reason preservation，优先选择 init-summary，因为它补齐迁移 todo 中 “LLM requested evidence 在 scan report、project-context 和 init summary 中的审计展示” 的最后一环。
- 用户故事：作为首次运行 `init` 后阅读 `.ai/init-summary.md` 的 Harness Maintainer，当本次扫描执行了 LLM-guided evidence expansion 或记录了 coverage selected paths 时，我可以在入口摘要中看到请求补读路径、实际读取路径、风险关注点、置信度、读取数量、rationale 和关键 coverage selected paths；如果这些摘要丢失，benchmark 会用 `content:init-summary` 给出具体 missing detail。
- 当前代码 gap：`build_init_summary_markdown()` 没有扫描证据审计章节；`benchmark.py` 的 `content:init-summary` 只检查成熟度、确认入口和 benchmark readiness；`assess_maturity()` 会重写 `init-summary.md` 且没有传入 inventory / commands，导致 benchmark 前刷新会丢失扫描上下文。
- 关键决策 / 取舍：不新增 schema，继续以 `scan-metadata.yaml` / `project-inventory.json` 为机器事实源；summary 只做摘要，完整审计仍在 scan-report 和 scan-metadata；benchmark 只在 inventory 存在 evidence expansion / coverage 时要求对应 detail。
- Assumptions / risks：`init-summary.md` 是首次 init 后最容易被团队转发的入口，因此应承接深扫摘要；旧 Harness 手工删掉该章节会被 benchmark 标记 failed，这是内容契约升级。
- Sub agent 使用情况：尝试启动只读 explorer 审查下一迁移切片，但当前环境返回 `agent thread limit reached`；本轮由主线程完成分析、TDD、实现和验证。
- 价值切分说明：本轮只连接 init-summary 与扫描证据审计，不做 scanner schema 深化或 failed check detail 全量审计；evidence helper 去重保留为后续技术债候选。
- 可执行验收标准及验证方式：unit 覆盖 init-summary 正向渲染；benchmark integration 覆盖完整 audit 通过和缺 audit section / detail 失败；fast regression 作为提交前验证。
- 完成内容：`init-summary.md` 新增 `## 扫描证据审计`；`assess_maturity()` 刷新 summary 时保留 inventory / commands；`content:init-summary` 校验 evidence expansion detail 和 coverage selected paths；README、init workflow、LLM contracts、testing strategy、sensor/gate rules、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap：failed check missing / errors / detail preservation 系统审计，或 evidence helper 去重。

## 2026-06-01 Scan Report Evidence Visibility 迁移

- North Star 模块：Deep Scan Evidence、Benchmark / Review Intelligence、Maturity & Evolution。
- init North Star 旅程阶段：扫描理解可解释；写入后的扫描审计报告；质量门禁解释。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。上一轮已把 LLM evidence expansion 推到 project-context 并由 benchmark 守住，但 `.ai/scan-report.md` 仍只展示 repo、primary stack、少量 evidence 和 commands，无法承载 coverage、stack validation、warnings、risk areas 或 LLM requested evidence 的审计。本轮候选包括 scan-report evidence visibility、init-summary evidence audit、failed check detail preservation 和 evidence helper 去重，优先选择 scan-report，因为它是扫描链路最直接的审计产物。
- 工程信任故事：作为 Harness Maintainer，当我查看 `.ai/scan-report.md` 或运行 `benchmark` 验收 Harness 时，我可以看到 evidence coverage、selected paths、LLM evidence expansion、stack validation、scan warnings、risk areas 和命令候选置信度；如果这些审计信息丢失，benchmark 会用 `content:scan-report` 给出具体 missing detail。
- 当前代码 gap：`asset_writers/reports.py` 的 `_scan_report()` 只列 `inventory.evidence` 和 command；`benchmark.py` 没有 `content:scan-report`；旧分支实现更完整但依赖当前 schema 不存在的顶层 evidence 字段和旧 `evidence_expansion_plan` 字段。
- 关键决策 / 取舍：适配当前 `scan_metadata.coverage`、`scan_metadata.evidence_expansion`、`scan_validation`、`scan_warnings` 和 `risk_areas`；test/risk/API/document evidence visibility 先通过 coverage bucket selected paths 和现有 inventory documents/configs/CI 展示，不新增 ProjectInventory 顶层字段。
- Assumptions / risks：旧 Harness 缺少 scan-report 审计章节会被 benchmark failed，这是有意暴露质量退化；本轮不改 LLM prompt、planner 策略或 evidence collector 预算。
- Sub agent 使用情况：尝试启动只读审查 agent，但当前 agent thread limit reached；本轮由主线程完成旧分支对比、TDD 和实现。
- 价值切分说明：本轮只强化 scan-report 与 benchmark，不把 init-summary evidence audit 混入；summary 可在下一轮基于稳定 scan-report 摘要化。
- 可执行验收标准及验证方式：unit 覆盖 report writer 的稳定章节和关键字段；benchmark integration 覆盖 Java fixture check id、完整 scan-report context 通过、缺章节、缺 coverage selected path、缺 evidence expansion detail 失败。
- 完成内容：`scan-report.md` 新增 Evidence、LLM Evidence Expansion、Evidence Coverage、Stack Evidence Validation、Scan Warnings、Risk Areas、Command Candidates 审计内容；benchmark 新增 `content:scan-report`；README、init workflow、LLM contracts、testing strategy、sensor/gate rules、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap：init-summary evidence audit，或 failed check missing/errors/detail preservation。

## 2026-06-01 Project Context Evidence Context Gate 迁移

- North Star 模块：Deep Scan Evidence、Sensor & Quality Gate、Maturity & Evolution。
- init North Star 旅程阶段：扫描理解可解释；写入后质量门禁；Maintainer 审查 project-context 证据链。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。本轮候选包括 project-context evidence context gate、scan-report evidence visibility、init-summary evidence audit 和 failed check detail preservation。当前 `ScanMetadata.evidence_expansion` 已记录 LLM 深扫计划和读取结果，但 `project-context.md` 只渲染 `inventory.evidence`，benchmark 没有守住 evidence expansion 审计章节，因此优先补齐 project-context 的用户可见证据闭环。
- 工程信任故事：作为 Harness Maintainer，当我运行 `init` 或 `benchmark` 审查一个刚生成的 Harness 时，我可以在 `.ai/guides/project-context.md` 看到扫描来源证据和 LLM evidence expansion 的 requested/read paths、risk focus、confidence 与 rationale，并且 benchmark 会防止这些证据上下文从 Guide 中丢失。
- 当前代码 gap：Guide writer 没有 `## LLM 证据扩展`，来源证据未合并 documents/configs/CI；`benchmark.py` 没有 `content:project-context-evidence-context`；旧分支实现读取旧字段和旧 inventory 顶层 evidence 字段，不能直接 cherry-pick。
- 关键决策 / 取舍：适配当前 `scan_metadata.evidence_expansion`；只校验 inventory evidence/doc/config/CI 和 expansion requested/read/risk/confidence/rationale；coverage bucket 的 selected paths、scan-report 和 init-summary evidence audit 留作后续。
- Assumptions / risks：旧 Harness 缺少 `## LLM 证据扩展` 会被 benchmark 显式标记 failed；这是质量门禁而非 fallback。真实 LLM prompt 和 schema 不变。
- Sub agent 使用情况：尝试启动 explorer 做只读调研，但当前 agent thread limit reached；本轮由主线程完成旧分支对比、TDD 和实现。
- 价值切分说明：本轮只迁移 project-context evidence context gate，不把 scan-report 和 init-summary 的 evidence visibility 混入，避免一次改变多个交付入口。
- 可执行验收标准及验证方式：unit 覆盖 writer 正向章节和字段；integration 覆盖 Java fixture check id、完整 context 通过、缺 evidence path、缺 LLM section、缺 requested/read/rationale detail 失败。
- 完成内容：`project-context.md` 新增 `## LLM 证据扩展`；来源证据合并 evidence/documents/configs/CI；benchmark 新增 `content:project-context-evidence-context`；README、init workflow、LLM contracts、testing strategy、sensor/gate rules、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap：scan-report evidence visibility，或 init-summary evidence audit，继续从迁移 todo 的 Scan evidence 可审计细节中选择。

## 2026-06-01 Risk Context Consistency Benchmark 迁移

- North Star 模块：Sensor & Quality Gate、Workflow Toolkit、Maturity & Evolution。
- init North Star 旅程阶段：写入后质量门禁；风险区域解释、验证策略和 Workflow routing 的一致性。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。本轮候选包括 risk context consistency、project-context evidence context gate 和 scan evidence reason/report visibility。当前维护入口已能识别 `content:risk-context-consistency`，Guide / Sensor 已渲染风险路径，但 benchmark 主体没有该 check，生成的 `harness-config.yaml` 也不会把扫描风险路径写入 standard escalation，因此优先补齐风险上下文质量门禁闭环。
- 工程信任故事：作为 Harness Maintainer，当我运行 `benchmark` 验收包含扫描风险区域的 Harness 时，我可以确认每个 scan risk path 同时出现在 project-context Guide、verification Sensor 和 standard escalation routing 中；如果任一环缺失，benchmark 会给出精确 `missing_*_risk:<path>` 错误。
- 当前代码 gap：`content:risk-context-consistency` 不存在；维护入口虽然有 risk context triage 分支，但没有 benchmark check 产生该信号；默认 config 只含泛化 `high_risk_module`，不含仓库具体风险路径。
- 关键决策 / 取舍：新增独立 `content:risk-context-consistency`，不塞进 `content:workflow-routing-policy`；routing 认可 `risk_area:<path>` trigger 或 rationale path；只取前 5 个风险路径，避免报告过长；不判断风险是否已人工确认。
- Assumptions / risks：`ProjectInventory.stack_extensions.risk_areas` 或 `llm_scan_proposal.risk_areas` 是 scan risk path 来源；旧 Harness 如果手工删掉 Guide / Sensor / routing 中任一风险路径，会被 benchmark 显式标为 failed。
- Sub agent 使用情况：尝试启动 explorer 做只读方案审查，但当前 agent thread limit reached；本轮由主线程对比旧分支实现和当前代码。
- 价值切分说明：本轮只迁移风险上下文一致性，不混入 project-context evidence context gate 或 scan evidence writer 深化。
- 可执行验收标准及验证方式：integration 覆盖生成风险路径时 benchmark 通过并写出 `risk_area:<path>` trigger；三类负向缺失分别报告 Guide、Sensor、Routing 缺失；Java fixture check id 列表包含 `content:risk-context-consistency`。
- 完成内容：`benchmark.py` 新增 `_risk_context_consistency_check()`；`write_assets.py` 新增 `build_harness_config()`，把扫描风险路径写入 standard escalation trigger / rationale；README、init workflow、sensor/gate 规则、testing strategy、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted benchmark integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：Runtime 边界未变化，未执行任务、不创建 `.ai/task-runs`。下一轮候选 gap 来自迁移 todo：project-context evidence context gate 与 Scan evidence 可审计细节可合并评估。

## 2026-06-01 Hard Gate Source Path Benchmark 迁移

- North Star 模块：Sensor & Quality Gate、Maturity & Evolution、Runtime Boundary。
- init North Star 旅程阶段：质量门禁解释；写入后通过 benchmark 判断第一版 Harness 是否可信。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。对比当前 main 与 `backup/local-61-before-migration` 后，本轮候选包括 hard gate source path 校验、risk context consistency、project-context evidence context gate。当前 main 已能展示 hard gate weak command detail，但 `_hard_gate_command_evidence_check()` 只检查 source 是否为空和 low confidence，不能发现 source 指向不存在文件或逃出目标仓库，因此优先补齐最小的 hard gate 可信来源校验。
- 工程信任故事：作为 Harness Maintainer，当我运行 `benchmark` 验收已有 Harness 时，如果 hard gate command 的 `source` 指向不存在文件或逃出目标仓库，我可以在 `benchmark-report.yaml` 的 `content:hard-gate-command-evidence` 中看到失败和 `weak_commands.reason`，从而知道该 hard gate 缺少可信来源证据，不能被当作已验证质量门禁。
- 当前代码 gap：`content:hard-gate-command-evidence` 对 `docs/testing.md` 这类不存在 source 或 `../outside.md` 这类仓库外 source 仍可能通过。
- 关键决策 / 取舍：复用现有 check id，不新增新 benchmark check；只验证 source path 可追溯，不执行命令；`BenchmarkReport` schema 继续兼容旧报告，但新生成的 weak command 会写 reason。
- Assumptions / risks：`CommandDefinition.source` 应是目标仓库内 evidence path；旧 Harness 如果写 URL、说明文本或组合路径，会被标记为不可追溯，需要 Maintainer 修正为仓库内文件。
- Sub agent 使用情况：尝试启动 explorer 做只读方案审查，但当前 agent thread limit reached；本轮由主线程对比旧分支实现。
- 价值切分说明：本轮只迁移 hard gate source path 校验，不把 risk context consistency 或 project-context evidence context gate 混入同一轮。
- 可执行验收标准及验证方式：benchmark integration 覆盖 source missing、source outside repo 和 source 为空；正常 Java fixture benchmark 继续通过。
- 完成内容：`_hard_gate_command_evidence_check()` 新增 `_hard_gate_command_evidence_issue()`，保留 `missing_source`、`low_confidence`、`source_path_missing`、`source_path_outside_repo`；README、sensor/gate 规则、测试策略、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted benchmark integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；Runtime 边界未变化，未执行 hard gate command、未创建 `.ai/task-runs`。下一轮候选 gap 继续来自迁移 todo：risk context consistency 或 project-context evidence context gate。

## 2026-06-01 Init Summary 待确认处理入口迁移

- North Star 模块：Progressive Collaboration、CLI Experience、Maturity & Evolution、Sensor & Quality Gate。
- init North Star 旅程阶段：写入后的交付摘要；仍需人工确认的问题和下一步处理入口。
- Gap Analysis 摘要：当前唯一 open todo 是本地独有 / 更细能力迁移。对比当前 main 与 `backup/local-61-before-migration` 后，本轮候选包括 Init Summary 待确认处理入口、Benchmark / quality gate 深层迁移、Scan evidence 可审计细节。当前 `human-input-needed.md` 和已有 Harness 维护入口已经有 `.ai/human-input-needed.md#处理方式`，但首次 `init-summary.md` 仍缺少稳定 `## 待人工确认` 章节和 questionnaire ID 对齐，因此优先补齐交付摘要闭环。
- 用户故事：作为首次运行 `init` 后阅读 `.ai/init-summary.md` 的 Harness Maintainer，当我看到 `## 待人工确认` 时，我可以直接知道这些 `confirm:*` 问题应去 `.ai/human-input-needed.md#处理方式` 处理，并且 scan warning 会显示对应 action hint，从而把交付报告里的风险解释连接到可执行补充动作。
- 当前代码 gap：`build_init_summary_markdown()` 没有 `## 待人工确认`；CLI completion 的待确认区只列问题，不说明处理入口；benchmark `content:init-summary` 不校验 confirmation 处理入口或 questionnaire ID 对齐。
- 关键决策 / 取舍：不新增 schema，复用 `Questionnaire`；将 scan warning action hint 从 human confirmation 内部 helper 提取为公共 helper，避免 `human-input-needed.md`、`init-summary.md` 和 CLI completion 文案漂移；summary 只展示前几个问题，完整处理建议仍以 `.ai/human-input-needed.md#处理方式` 为准。
- Assumptions / risks：`init-summary.md` 是首次 init 后团队会共享的持久化入口，因此必须能独立指向人工确认处理方式；旧 Harness 如果没有该章节，benchmark 可暴露为内容契约失败；action hint 只是处理建议，不代表 Builder 自动修正扫描结论。
- Sub agent 使用情况：尝试启动 explorer 做只读旧分支对比，但当前 agent thread limit reached；本轮由主线程用当前文件和 `git show` 完成对比。
- 价值切分说明：本轮聚焦首次 init 交付摘要和待确认处理入口，不把 Benchmark 深层 quality gate 或 Scan evidence writer 迁入同一轮。
- 可执行验收标准及验证方式：unit 覆盖 summary / CLI completion 的 `## 待人工确认`、处理入口、`confirm:*` ID 和 scan warning action hint；integration 覆盖 Java / .NET fixture init 产物；benchmark integration 覆盖 `content:init-summary` 缺处理入口时失败。
- 完成内容：`init-summary.md` 新增 `## 待人工确认`；`render_init_completion_message()` 复用同一待确认摘要；`benchmark` 增强 `content:init-summary` 检查；README、init workflow、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；`git diff --check` 通过；`scripts/test-fast.sh` 通过，结果为 `347 passed in 17.77s`。
- Self-Harness Gate：长期文档已同步；Runtime 边界未变化，未创建 `.ai/task-runs`。下一轮候选 gap 继续来自迁移 todo：优先审视 Benchmark / quality gate 细化，或进入 Scan evidence 可审计细节。

## 2026-06-01 Existing Harness Benchmark / Routing Signals 迁移

- North Star 模块：CLI Experience、Maturity & Evolution、Sensor & Quality Gate、Runtime Boundary。
- init North Star 旅程阶段：再次进入已有 Harness；健康状态、维护建议和下一步动作。
- Gap Analysis 摘要：当前唯一 open todo 仍是本地独有 / 更细能力迁移。对比当前 main 与 `backup/local-61-before-migration` 后，本轮候选包括 Benchmark / Workflow routing 只读信号、Benchmark 深层 quality gate 迁移、Scan evidence 可审计细节。README 与 init workflow 已把 Benchmark signals / Workflow routing signals 描述为维护入口契约，但当前代码只在 Experience signals 中混合展示 `schema_content_failed_checks`，没有独立小节和 failed detail；因此本轮优先修正代码、schema 和测试的事实源漂移。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以直接看到最近 benchmark 失败项的数量、ID、中文解释、可行动错误详情，以及当前 workflow routing 的 default / standard escalation / risk trigger 状态，从而不用先打开多个 YAML 文件也能判断应该先修质量门禁还是调整 routing 策略。
- 当前代码 gap：`BenchmarkReport` schema 没有保留 `errors`、`missing`、`weak_commands`；existing-Harness 入口没有输出 `Benchmark signals` / `Workflow routing signals`；Maintenance triage 不能把 hard gate weak command 或 project-context evidence missing 升级为专属 reason/detail。
- 关键决策 / 取舍：新增宽松的 `BenchmarkWeakCommand` schema，兼容当前 benchmark 只写 `id/source/confidence` 和旧分支带 `reason` 的报告；保留 `schema_content_failed_checks` Experience 行以兼容现有输出；Workflow routing signals 只读解释 `.ai/harness-config.yaml`，不执行 Runtime、不修改 routing policy。
- Assumptions / risks：`standard-escalation` 是当前 routing 健康度的关键观察点；schema 变宽只保留已有 report detail，不改变 benchmark pass/fail 计算；CLI 仍保留 `key=value` 稳定契约，后续可继续人类化展示。
- Sub agent 使用情况：尝试启动 explorer 做旧分支对比，但当前 agent thread limit reached；本轮由主线程用 `git show` / `git grep` 完成只读对比。
- 价值切分说明：本轮把 Benchmark failed preview 与 Workflow routing signals 合并，因为它们共享已有 Harness 维护入口的只读状态视图和同一 CLI 验收；不把更深 benchmark 检查或 scan evidence writer 混入。
- 可执行验收标准及验证方式：unit 覆盖 BenchmarkReport detail schema、benchmark signal helper、workflow routing signal helper、maintenance triage 专属 reason/detail；integration 覆盖已有 Harness `init -> exit` 输出两个独立小节且不扫描、不覆盖正式资产。
- 完成内容：`BenchmarkReport` 保留 check detail；`interactive_init.py` 输出 `Benchmark signals` 和 `Workflow routing signals`；`maintenance_triage.py` 增加 hard gate weak command、risk context、project-context evidence 专属排序与 guidance；README、init workflow、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；下一轮候选 gap 转向迁移 todo 中剩余的人机闭环细节，例如 `init-summary.md` 与 questionnaire `confirm:*` ID 对齐，或进入 Benchmark / quality gate 深层校验迁移。

## 2026-06-01 Human Input 待确认回访入口迁移

- North Star 模块：Progressive Collaboration、CLI Experience、Maturity & Evolution。
- init North Star 旅程阶段：再次进入已有 Harness；深度追问和人工确认回访。
- Gap Analysis 摘要：当前迁移 todo 仍有 Existing Harness human-input-needed signals、benchmark failed preview 和 routing signals。Benchmark preview 依赖更细 BenchmarkCheck 字段，routing signals 主要解释正式 routing policy；human input 回访直接补齐“用户跳过的问题必须能回访处理”的渐进式协作闭环，因此本轮优先。
- 用户故事：作为 Harness Maintainer，当我首次 init 后仍有待确认问题，并在之后再次运行 guided `init` 进入已有 Harness 维护入口时，我可以看到待确认项数量、scan 类确认数量、优先处理的 interaction id 和 `.ai/human-input-needed.md#处理方式` 入口，从而知道哪些人工上下文仍需补齐，以及应该用哪个命令或治理动作处理它们。
- 当前代码 gap：`human-input-needed.md` 只有待确认问题和下一步建议，没有稳定 `## 处理方式`；已有 Harness 入口只显示 `human_input_needed=present/missing`，不能展示 questionnaire backlog。
- 关键决策 / 取舍：复用现有 `Questionnaire` schema，不新增机器契约；scan 类确认项限定为当前 schema 类型；本轮不自动处理确认项，不修改正式 Guides / Sensors / routing policy，不执行 Runtime。
- Assumptions / risks：当前 Questionnaire 还没有 processed 状态，因此本轮展示的是待确认问题总数和前几个 id；后续可结合 candidate governance / Experience evidence 做更细状态。
- Sub agent 使用情况：未使用 sub agent；此前线程 agent 数量达到上限，本轮范围小且主线程可直接完成。
- 价值切分说明：本轮同时更新 `human-input-needed.md` 和已有 Harness 入口，因为它们共享“待确认项回访”这一用户故事，不把 benchmark failed preview 或 routing signals 混入同一轮。
- 可执行验收标准及验证方式：unit 覆盖 Markdown 章节与处理建议、helper 对 questionnaire 的 schema 校验和 missing 边界；integration 覆盖已有 Harness `init -> 1` 输出 backlog status 且 formal assets 不变。
- 完成内容：`human_input_markdown()` 增加 `## 扫描待确认摘要` 和 `## 处理方式`；`interactive_init.py` 增加 `_human_input_needed_status_lines()` 并在 Experience / review signals 中展开 human input backlog；README、init workflow、迁移 todo、spec 和 plan 同步。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；无新增 schema。下一轮候选 gap：benchmark failed preview 与 BenchmarkCheck detail 字段、Workflow routing signals、init-summary 与 questionnaire `confirm:*` ID 对齐。

## 2026-06-01 Existing Harness 编号菜单与维护指引迁移

- North Star 模块：CLI Experience、Maturity & Evolution、Experience & Self-Improve。
- init North Star 旅程阶段：再次进入已有 Harness。
- Gap Analysis 摘要：当前唯一 open todo 是本地独有 / 更细能力迁移。对比当前主线和 `backup/local-61-before-migration` 后，本轮候选包括 Existing Harness 编号菜单与 guidance、benchmark failed preview、human-input-needed backlog、Workflow routing signals。编号菜单与 guidance 最小且直接提升维护入口可用性，因此先迁移。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以看到带编号的维护动作菜单，并按编号选择只读退出或后续维护动作，同时从 Maintenance triage guidance 中理解 top actions 应该如何处理，从而不用记英文命令或自行解读 reason code。
- 当前代码 gap：已有入口只输出英文命令列表和 `top_action_* reason/source/next`，没有编号选择，也没有中文处理建议。
- 关键决策 / 取舍：本轮只迁移编号菜单、action normalization 和 triage guidance；benchmark 失败细节、human-input backlog、routing signals 保留为迁移 todo 的后续候选。
- Assumptions / risks：编号菜单不改变任何正式资产写入边界；未知输入仍默认只读退出。sub agent 已尝试启用但线程 agent 数量达到上限，本轮改为主线程本地对比。
- 边界情况 / 失败模式：`1` 到 `8`、英文命令和常见中文别名都规范化到稳定 action；未知输入保持原有保守退出路径；`exit` 不触发 scan、不覆盖正式 Harness 资产。
- 价值切分说明：该切片围绕“已有 Harness 维护入口能被低成本操作”这一用户故事，不把更细 benchmark/human-input/routing 信号混入同一轮。
- 可执行验收标准及验证方式：unit 覆盖 action normalization 和 guidance 渲染；integration 覆盖输入 `1` 只读退出、编号菜单输出、guidance 输出、formal assets 不变；文档和迁移 todo 同步。
- 完成内容：新增 `render_maintenance_triage_guidance_lines()`；existing-Harness guided entry 输出 `Maintenance triage guidance` 和编号菜单；新增 `_normalize_existing_harness_action()`；同步 README、init workflow、迁移 todo、spec 和 plan。
- 验证结果：targeted unit / integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期文档已同步；无新增 schema 或 benchmark 契约。下一轮候选 gap：benchmark failed preview 与更细 failure detail、human-input-needed backlog 状态、Workflow routing signals，仍需下一轮 Current State Gap Analysis 重新排序。

## 2026-06-01 本地独有能力迁移 Todo 收敛

- 关联 todo：`docs/todos/local-unique-capability-migration.md`。
- North Star 模块：目标模式执行系统、Init Experience、Maturity & Evolution、工程可持续性。
- init North Star 旅程阶段：本轮不改用户旅程，先收敛后续迁移基线，避免并行实现继续污染 `init` 主线。
- Gap Analysis 摘要：最新远端 `origin/main` 已包含 guided init 进度、maturity preview、LLM evidence plan、scan follow-up 和 self-check 等 30 个提交；本地旧 `main` 另有 61 个未 push 提交，且两边在 `interactive_init.py`、`init_summary.py`、`scan_repo.py`、`human_confirmation.py` 等核心文件高度重叠。用户明确要求先处理合并问题、剩余重复 commit 可以丢掉，因此本轮选择基线收敛，而不是继续功能迁移。
- 工程信任故事：作为 Harness Builder 维护者，当本地 61 个提交和远端 30 个提交已经并行演进且决定放弃整包 merge 时，我可以在最新 `origin/main` 基线上保留旧实现备份、把当前 open todo 收敛为“本地独有 / 更细能力迁移”，从而让后续目标模式只按小步迁移独有增量，而不是继续尝试合并两套实现。
- 当前代码 gap：`main` 已 reset 到最新 `origin/main` 后，远端仍有两个 open todo，会让目标模式继续按旧大主题推进；迁移策略 todo 曾在旧工作树里写好，但需要恢复到新基线，并记录备份分支 / stash 事实。
- 关键决策 / 取舍：以最新 `origin/main` 为主线；旧 61 个提交保留在 `backup/local-61-before-migration`；reset 前未提交工作树保留在 `stash@{0}: local-worktree-before-origin-main-reset`；`guided-init-ai4se-real-repo-findings.md` 与 `maturity-driven-init-wizard.md` 暂停为背景参考；本轮不迁移功能代码。
- Assumptions / risks：备份分支是本地引用，后续如需共享旧实现需要单独推送或导出；stash 序号可能变化，因此 todo 记录 stash message；暂停旧 todo 不是否定其价值，而是避免绕开迁移决策。
- Sub agent 使用情况：未使用 sub agent。本轮是 git / 文档基线收敛，范围小且不涉及并行代码调研。
- 价值切分说明：本轮完成后，后续目标模式有一个干净远端基线和唯一迁移入口，能把冲突风险从“整包合并 61 个提交”降为“逐个迁移独有能力”。
- 验收标准及验证方式：`main` 与 `origin/main` 对齐；备份分支存在；`docs/todos` 只有迁移 todo 为 open；`git diff --check` 和 `scripts/test-fast.sh` 通过。
- 完成内容：恢复并更新 `local-unique-capability-migration.md`；更新 todo README；暂停两个旧 open todo；新增本轮 spec / plan。
- 验证结果：open todo 检查只返回迁移 todo；备份分支存在；`git diff --check` 通过；`scripts/test-fast.sh` 通过，334 passed。
- Self-Harness Gate：下一轮应从迁移 todo 的推荐顺序中选择第一个小步迁移切片，优先 Existing Harness 维护入口独有能力；不要直接 merge 或 cherry-pick 整组旧提交。

## 2026-06-01 Guided Init 扫描失败退出边界硬化

- 关联 todo：`docs/todos/maturity-driven-init-wizard.md`、`docs/todos/testing-coverage-and-acceptance-strategy.md`。
- North Star 模块：CLI Experience、Progressive Collaboration、可解释失败边界、可观测 Harness 生成。
- init North Star 旅程阶段：阶段化扫描与进度反馈、错误信息、可审计 trace、正式资产写入边界。
- Gap Analysis 摘要：本轮重新读取事实源后发现工作区已有 guided scan failure 的退出边界改动。候选对比中，用户自然语言补充影响成熟度/推荐和路径型 claim validation 更接近下一阶段深度体验，但当前 dirty diff 已形成独立工程信任故事：扫描失败应由 CLI 友好失败和 scan trace 表达，而不是泄露 traceback 或被外层 `init failed` 混淆。
- 工程信任故事：作为 Harness Maintainer，当首次 guided `init` 的扫描阶段因为 LLM、网络或 schema 问题失败时，我可以看到清晰的中文失败说明和“未写入正式 Harness 资产”的边界，并且后续维护者可以从 trace 中确认失败只发生在 scan 阶段，从而更快定位问题而不误以为系统生成了不可信 Harness。
- 当前代码 gap：已有测试只断言终端失败提示和正式资产未写入，没有验证 `trace.yaml`、`events.jsonl` 和外层 `init failed` 污染；上一轮 scan progress spec/plan 也没有记录 `typer.Exit` 退出语义。
- 关键决策 / 取舍：guided scan failure 在 `interactive_init.py` 中记录 `scan failed` details、输出中文失败说明、finish failed trace 后抛出 `typer.Exit(1)`；`cli.py` 透传 `typer.Exit` / `typer.Abort`，避免通用异常处理重复写入外层失败事件。失败仍显式暴露，不 fallback，不写正式 Harness 资产。
- Assumptions / risks：失败 trace 目录属于过程审计产物，不代表正式 Harness 已生成；隐藏 traceback 不能隐藏错误摘要，因此错误类型和短消息同时进入 CLI、trace summary 和 events。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 dirty diff 和下一轮 init gap。一个建议本轮收口扫描失败边界并补 trace 断言；另一个建议下一轮优先做自然语言补充影响成熟度/推荐。
- 价值切分说明：本轮只硬化 guided scan failure 的退出与 trace 契约，不混入自然语言补充消费、targeted rescan、claim validation 或 benchmark 交互。
- 验收标准及验证方式：integration 覆盖扫描失败输出无 traceback、`CliRunner` 不再暴露原始 `RuntimeError`、`trace.yaml status=failed`、summary 包含 `error_type` / `scan_error`、`events.jsonl` 只有 scan failed 事件、正式 Harness 资产未写入；工程文档和 spec/plan 同步。
- 完成内容：补强 guided scan failure 测试；`interactive_init.py` 在 scan failure 后 finish trace 并 Typer exit；`cli.py` 透传 Typer 控制流异常；新增本轮 spec / plan，更新 init workflow 和演进记录。
- 验证结果：targeted test `1 passed in 0.20s`；commit 前快速回归见本轮提交前验证。
- Self-Harness Gate：长期失败边界已沉淀到 `docs/engineering/init-workflow.md`；本轮没有新增 `.ai` 资产契约。下一轮候选 gap：自然语言补充与 self-check resolution 如何影响成熟度预览、推荐解释和最终资产；路径型 claim validation；已有 Harness schema / contract 损坏时的维护入口修复引导。

## 2026-06-01 Push Gate：Scan Self-check Evidence Source 契约修复

- 触发来源：用户要求当前任务完成后统一 push；push 前 `scripts/test-full.sh` 在真实 eShopOnWeb acceptance 中失败。
- 失败现象：真实 DeepSeek scan self-check 返回 `source_sampling_truncated` 作为 `resolutions[].evidence_sources`，parser 报 `unknown evidence source`，导致非交互 `init` 失败。
- 根因：`source_sampling_truncated` 是 `ScanMetadata.warnings[].code` 中的稳定扫描审计来源；prompt 文案允许引用 scan warning / scan metadata 中已有 evidence 字符串，但 parser allowlist 只接受 warning 的 `evidence` 值，没有接受 warning code，契约两侧不一致。
- 决策：将 scan warning code 明确纳入 self-check evidence source allowlist，并同步 prompt / LLM contract；继续拒绝任意未知路径或字符串，不引入 fallback。
- 验收方式：新增 unit 测试复现 `source_sampling_truncated` 作为 evidence source 的真实 LLM 行为；保留未知 evidence source 失败测试；重新运行 targeted / fast / full regression 后再 push。

## 2026-06-01 Scan Follow-up Self-check

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Scanner & Analyzer、CLI Experience、Progressive Collaboration、Maturity & Evolution、智能化闭环。
- init North Star 旅程阶段：扫描结果友好呈现、深度追问、渐进式深入、人工确认资产。
- Gap Analysis 摘要：上一轮已把扫描不确定性转成 `followup_questions` 并进入 CLI / questionnaire / human input，但追问仍只是待办项，没有被 LLM 再审查；本轮比较了 follow-up self-check、自然语言补充消费、维护入口浏览和 claim-level validation，选择先做 review-only self-check，因为它能最小纵向消费现有追问契约，同时不自动改正式扫描结论。
- 用户故事：作为 Harness Maintainer，当大型或多栈仓库首次 guided `init` 生成深度追问时，我可以看到 Builder 基于当前 evidence 对这些追问执行 LLM 二次自检，并把每个追问的 review-only 结论、风险和下一步写入 scan metadata、CLI 和人工确认链路，从而知道哪些问题仍需人工补充或后续 targeted scan。
- 当前代码 gap：`scan_repo.py` 只在 reconcile 后返回 metadata；`followup_questions` 只被 CLI 和 questionnaire 展示；没有 `ScanSelfCheckReport`、self-check prompt、parser、progress event 或 questionnaire resolution 合并。
- 关键决策 / 取舍：新增 `ScanSelfCheckReport` / `ScanSelfCheckResolution` 和 `ScanMetadata.self_check`；新增集中 prompt `llm_scan_self_check_v1.md`；真实 LLM 路径或显式 mock caller 才运行 self-check；self-check 只做 review-only 审计，不自动修改 inventory、commands、Guides、Sensors 或 Workflow routing。
- Assumptions / risks：真实有 follow-up 的 init 会增加一次 LLM 调用；mock scan 测试如果没有显式传 self-check caller 不会被额外调用；后续仍需要 claim-level support/conflict/unknown validation。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行调研 follow-up 消费链路、实现风险和候选排序；两者均建议本轮优先做审计型 self-check，把自动修正和 claim-level validation 留作后续。
- 价值切分说明：本轮完成“follow-up questions -> LLM self-check -> scan metadata -> CLI -> questionnaire”的纵向闭环，不把 targeted rescan、自动修正或完整 claim map 混入同一 milestone。
- 验收标准及验证方式：schema unit 覆盖 `ScanMetadata.self_check`；LLM parser unit 覆盖合法 JSON、非法 JSON、未知 interaction id 和未知 evidence source；scan repo unit 覆盖有 follow-up 时调用 self-check、无 follow-up 时不调用；guided integration 覆盖“LLM 二次自检”和 questionnaire reason；prompt registry 测试覆盖集中 prompt 管理。
- 完成内容：新增 self-check schema、prompt、parser 和 scan repo 阶段；guided CLI 展示 review-only 二次自检；questionnaire 合并对应 resolution；同步 engineering docs、todo、spec 和 plan。
- 验证结果：targeted suite `25 passed in 0.15s`；commit 前快速回归 `scripts/test-fast.sh` 为 `333 passed in 16.24s`；`git diff --check` 通过。
- Self-Harness Gate：剩余 LLM-planned deep scan 仍 open。下一轮候选 gap 优先考虑 claim-level support/conflict/unknown validation 的第一切片，其次是用户自然语言补充与 self-check resolution 如何共同影响成熟度预览和 Harness 推荐。

## 2026-06-01 Scan Follow-up Questions

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Scanner & Analyzer、CLI Experience、Progressive Collaboration、Maturity & Evolution、智能化闭环。
- init North Star 旅程阶段：扫描结果友好呈现、成熟度初评前的深度追问、可审计 evidence、human-input-needed。
- Gap Analysis 摘要：当前 coverage gap、unsupported stack claim、primary stack unknown、模块边界缺失和测试 evidence 缺失已经会产生 warning 或 CLI 文案，但它们没有统一的机器契约，不能稳定进入 targeted 追问、questionnaire 和 human input。子代理建议最小切片是在现有 warning / metadata / questionnaire 链路上增加 scan self-check trigger，而不是直接引入第二次 LLM 调用。
- 用户故事：作为 Harness Maintainer，当大型或多栈仓库首次 guided `init` 存在源码覆盖不足、LLM 栈判断缺少证据、主要技术栈未知或模块边界不清时，我可以在 CLI、`.ai/scan-metadata.yaml`、`.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md` 中看到明确的补救追问，从而知道应该补充哪些关键路径、技术栈、模块边界或验证线索。
- 当前代码 gap：`ScanMetadata` 只有 warnings、coverage 和 evidence_expansion；`human_confirmation.py` 只把 raw warnings 转成 “接受降级 / 人工修正” 问题；guided CLI 的“不确定性 / 建议补充”缺少稳定、可测试的 follow-up question 契约。
- 关键决策 / 取舍：新增 `ScanFollowupQuestion` 和 `ScanMetadata.followup_questions`；新增 `scan_followup_confirmation` questionnaire 类型；guided CLI 展示 `深度追问`。本轮不新增二次 LLM self-check、不扩大读取预算、不自动修正 proposal、不调整 benchmark scoring。
- Assumptions / risks：follow-up 与原始 scan warning confirmation 会有一定重叠；当前保留原始 warning 作为审计问题，follow-up 用于面向用户的补救追问，后续可以做去重或优先级排序。
- Sub agent 使用情况：使用 explorer 子代理只读调研 coverage warning、planner low confidence、stack conflict / unknown 的产生和消费路径；采纳其“最小切片先加 scan self-check trigger / targeted follow-up”的建议。
- 价值切分说明：本轮完成“warning / validation -> metadata follow-up -> CLI 深度追问 -> questionnaire / human-input”的纵向闭环，不把二次 LLM self-check 和 claim-level validation 扩展混入同一 milestone。
- 验收标准及验证方式：schema unit 覆盖 `followup_questions`；reconciler unit 覆盖 coverage gap、unsupported stack、unknown stack、module boundary 和 test evidence follow-up；human confirmation unit 覆盖 `scan_followup_confirmation`；guided integration 覆盖 CLI `深度追问`、questionnaire 和 human-input。
- 完成内容：新增 `ScanFollowupQuestion` schema；`reconcile_scan()` 根据 warnings / stack validation / proposal 状态生成 follow-up；`interactive_init.py` 展示深度追问；`build_questionnaire()` 写入 scan follow-up confirmation；同步 spec、plan、工程文档和 todo。
- Self-Harness Gate：剩余 LLM-planned deep scan 仍 open。下一轮候选 gap 优先考虑二次 LLM self-check 或 targeted scan 对 `followup_questions` 的消费，其次是 module / risk / config / CI 的 claim-level support / conflict / unknown validation。

## 2026-06-01 Guided Init LLM Evidence Plan 可见化

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Scanner & Analyzer、CLI Experience、Progressive Collaboration、Maturity & Evolution、智能化闭环。
- init North Star 旅程阶段：阶段化扫描与进度反馈、扫描结果友好呈现、深度追问、可审计 evidence。
- Gap Analysis 摘要：上一轮已把 `evidence_expansion` 写入 `.ai/scan-metadata.yaml`，但首次 guided `init` 主界面仍不解释 LLM 为什么补读哪些文件、实际读到哪些文件、planner 低置信度为什么需要人工确认；子代理建议下一步优先处理 coverage gap / conflict / unknown 后的补救和 targeted 追问，本轮选取其中低风险且可独立验收的 planner low-confidence targeted confirmation 切片。
- 用户故事：作为 Harness Maintainer，当大型或多栈仓库首次 guided `init` 触发 LLM-guided evidence expansion 时，我可以在扫描发现阶段看到 LLM 补读了哪些文件、为什么补读、实际读到了哪些文件，以及低置信度补读计划为何需要人工确认，从而在补充上下文前校准扫描理解和风险边界。
- 当前代码 gap：`interactive_init.py` 只展示通用风险、不确定性和验证缺口；`human_confirmation.py` 会把 scan warning 转成确认项，但没有专门的 evidence expansion 交互类型，导致 planner 低置信度缺少可读的问题表达。
- 关键决策 / 取舍：新增 CLI “LLM 深度补充”分组；新增 `evidence_expansion_confirmation` questionnaire 类型和稳定 `confirm:evidence-expansion` id；本轮不做二次 LLM self-check、不扩大读取预算、不调整 planner prompt 或 benchmark scoring。
- Assumptions / risks：planner rationale 可能来自真实 LLM，后续如出现英文或过长表达，再通过 prompt 或渲染层继续收紧；旧 scan metadata 没有 `evidence_expansion` 时不输出空分组。
- Sub agent 使用情况：使用 explorer 子代理只读调研下一轮 gap；采纳其 P0 中“targeted 追问触发”的方向，但把更大的二次 self-check / claim-level validation 留作下一轮候选。
- 价值切分说明：本轮完成“planner metadata -> CLI 可见解释 -> low confidence 待确认资产”的用户可见闭环，不把 claim validation、二次 self-check 和 schema hardening 混入同一 milestone。
- 验收标准及验证方式：integration 覆盖 guided CLI 输出 `LLM 深度补充`、路径、关注原因、rationale 和 low confidence；unit 覆盖 low-confidence evidence expansion 生成 questionnaire；schema unit 覆盖新 interaction type；文档和 todo 同步契约。
- 完成内容：`QuestionnaireQuestion` 支持 `evidence_expansion_confirmation`；`build_questionnaire()` 将 low-confidence planner 转成 `confirm:evidence-expansion`；guided CLI 展示 planner requested/read paths、risk focus、rationale 和 confidence；同步 spec、plan、工程文档和 todo。
- Self-Harness Gate：剩余 LLM-planned deep scan 仍 open。下一轮候选 gap 优先考虑子代理提出的 coverage gap / conflict / unknown 二次 self-check 或 targeted scan，再考虑 claim-level support/conflict/unknown validation 和 `LLMScanProposal` 结构化 hardening。

## 2026-06-01 LLM Evidence Plan 可审计

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Scanner & Analyzer、CLI Experience、Maturity & Evolution、智能化闭环。
- init North Star 旅程阶段：阶段化扫描与进度反馈、扫描结果友好呈现、可审计 evidence、成熟度初评输入。
- Gap Analysis 摘要：上一轮已让全量轻量 manifest 带 bucket / priority / reason，但 `LLMEvidencePlan` 的 requested paths、risk focus、rationale 和 confidence 只在内存中用于读取补充文件，最终 `.ai/scan-metadata.yaml` 仍无法回答“LLM 为什么补读这些文件、实际读到了哪些文件、planner 是否低置信度”。
- 用户故事：作为 Harness Maintainer，当大型多栈仓库的首次 `init` 触发 LLM-guided evidence expansion 时，我可以在 `.ai/scan-metadata.yaml` 中审计 planner 计划、实际读取结果和低置信度风险，从而调试扫描结论并判断哪些判断需要人工确认。
- 当前代码 gap：`scan_repository()` 调用 planner 后没有把 plan 传入 `reconcile_scan()`；`ScanMetadata` 只有 coverage、warnings 和 final scan reasoning summary；planner 低置信度不会改变 `needs_human_confirmation`。
- 关键决策 / 取舍：新增 `LLMEvidenceExpansionMetadata` 作为 `ScanMetadata.evidence_expansion` 可选字段；不把 planner metadata 写入 `llm-scan-proposal.json`；不扩大读取预算、不新增第二轮 LLM scan；planner 低置信度追加 warning 并置位 human confirmation signal。
- Assumptions / risks：旧 scan metadata 可以没有 `evidence_expansion`；真实 LLM planner 的 rationale 会进入机器审计产物，应保持短文本并由现有 planner prompt 约束。
- Sub agent 使用情况：使用一个 explorer 子代理只读调研 scan metadata 数据流、writer、benchmark 和测试落点；采纳其“schema + scan_repo + scan_reconciler 最小切点，writer 大概率透传”的建议。
- 价值切分说明：本轮完成“LLM 规划 -> Python 安全读取 -> 最终 scan -> metadata 审计 -> low confidence 人工确认信号”的纵向闭环，不把 `modules/risk_areas` schema hardening 或 claim-level validation 混入同一 milestone。
- 验收标准及验证方式：schema unit 覆盖 `ScanMetadata.evidence_expansion`；reconciler unit 覆盖 planner audit 和 low confidence warning / human confirmation；scan repo unit 覆盖 planner metadata 透传；init fixture integration 覆盖 `.ai/scan-metadata.yaml` schema 和空 requested paths 的 audit 落盘。
- 完成内容：新增 `LLMEvidenceExpansionMetadata`；`scan_repository()` 向 `reconcile_scan()` 传递 `LLMEvidencePlan`；`reconcile_scan()` 生成 `evidence_expansion` 并处理 low confidence；同步 init workflow、LLM contracts、todo、spec 和 plan。
- Self-Harness Gate：剩余 LLM-planned deep scan 仍 open。下一轮候选 gap 优先考虑严格化 `LLMScanProposal` 中 modules / risk_areas / configs / ci_files schema，其次是 claim-level support/conflict/unknown 调和和 ai4se-like integration / acceptance。

## 2026-06-01 LLM 规划式深度扫描 Manifest 语义增强

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Scanner & Analyzer、CLI Experience、Maturity & Evolution、智能化闭环。
- init North Star 旅程阶段：基础扫描、阶段化扫描与进度反馈、扫描结果友好呈现、成熟度初评输入。
- Gap Analysis 摘要：当前已有 `collect evidence -> LLM evidence plan -> 读取补充文件 -> LLM scan -> reconcile` 链路，但全量轻量 `EvidenceBundle.files` 只有路径和大小，未携带 bucket / priority / reason；这会让 LLM planner 虽然能看到全量路径，却难以区分未采样文件中的风险、API 入口、测试和核心源码优先级。
- 用户故事：作为 Harness Maintainer，当我在大型多栈仓库运行首次 guided `init` 且初始 source sampling 跳过大量文件时，我可以相信 LLM evidence planner 在最终扫描前基于全量轻量 manifest 主动选择未采样但高价值的文件补读，而不是只被确定性采样结果牵引。
- 当前代码 gap：`collect_evidence()` 对 `files[]` 使用 `_evidence_file(..., max_summary_chars=0)`，没有传入 `_bucket_for()`、`_priority_for()` 和 `_reason_for()`；`llm_evidence_plan_v1.md` 没有明确要求 LLM 消费 full manifest 语义和 coverage gap。
- 关键决策 / 取舍：复用 `EvidenceFile` 现有字段，不新增 schema；全量 manifest 仍不读取正文摘要；LLM 只能从 allowlist 中逐字复制路径，Python 继续负责路径校验、预算读取和 no silent fallback。
- Assumptions / risks：bucket / priority / reason 是 evidence classification，不是最终业务判断；真实 LLM 的 requested paths 可能变化，但仍被 schema、max 8、allowlist 和 retry 约束。
- Sub agent 使用情况：使用一个 explorer 子代理只读调研当前 deep scan 链路；其结论确认 full manifest 偏薄，并建议后续补 planner rationale / requested paths 进入 scan metadata、claim-level validation 和 ai4se-like integration。
- 价值切分说明：本轮完成“全量轻量 manifest -> planner prompt -> LLM requested file -> final scan evidence”的最小纵向闭环，不把 metadata 审计、二次 self-check 和完整 claim validation 混进同一 milestone。
- 验收标准及验证方式：unit 覆盖全量 `files[]` 未采样文件带 bucket / priority / reason 且不读 summary；planner prompt 覆盖 full manifest 语义、coverage warnings 和未进入初始摘要的高价值文件；scan repo 测试覆盖 planner 从增强 manifest 请求未采样文件并进入 final scan prompt。
- 完成内容：`collect_evidence()` 为全量轻量文件索引填充 bucket / priority / reason；`llm_evidence_plan_v1.md` 增加 full manifest、coverage warnings、未采样高价值文件的规划规则；同步 spec、plan 和 todo。
- Self-Harness Gate：剩余 LLM-planned deep scan 仍 open。下一轮候选 gap 优先考虑将 `LLMEvidencePlan` 的 rationale、risk_focus、requested_paths、实际读取文件和 planner confidence 写入 scan metadata，并让 coverage gap / low confidence 显式影响 human confirmation；其次是严格化 `LLMScanProposal` 中 modules / risk_areas / configs / ci_files schema 和 claim-level support/conflict/unknown。

## 2026-05-31 成熟度叙事中文化

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：Maturity & Evolution、CLI Experience、可解释性、Harness 推荐质量。
- init North Star 旅程阶段：成熟度初评与差距解释、设计预览、写入摘要、已有 Harness 维护入口。
- Gap Analysis 摘要：真实 `ai4se` guided `init` 暴露“主要差距”中出现 `Guides are structured...` 等英文内部句；代码确认 `maturity_model.py` 的 blocker、evidence summary、next level requirement 和 blocking cap 会被 CLI、`maturity-score.yaml`、`maturity-report.md`、`init-summary.md` 直接消费。
- 用户故事：作为 Harness Maintainer，当我查看首次 `init` 的成熟度初评、写入前 preview、`maturity-report.md` 或 assess 刷新的成熟度报告时，我可以看到中文、面向 L0-L4 工程影响的阻断项和下一步建议，而不是英文内部叙事。
- 当前代码 gap：`maturity_model.py` 源头 user-facing strings 多数是英文；`asset_writers/reports.py` 和 `assess_maturity.py` 还在维度详情中输出 `evidence:` / `blockers:` 英文标签。
- 关键决策 / 取舍：在源头中文化 maturity free-text，保留 dimension key、blocker id、source path 和 schema 字段；新增 `maturity_rendering.py` 只做中文展示 label，不翻译机器 key；保留 `Guides`、`Sensors`、`Workflow`、`Runtime`、`hard gate` 等产品术语。
- Assumptions / risks：LLM reviewer 后续会消费中文 maturity score；这符合仓库“过程文档和用户叙事中文化”的方向，但若需要 LLM 输出也中文化，应单独调整 maturity review prompt。
- Sub agent 使用情况：使用一个只读子代理审查 maturity 出口、测试和 LLM 风险；采纳其“源头翻译为主，渲染层补标签映射”的建议。
- 价值切分说明：本轮修的是同一成熟度叙事出口链路，不改变评分算法和 schema，直接保护用户理解 L0-L4 成熟度、阻断项和下一步建议的体验。
- 验收标准及验证方式：unit 覆盖 `build_maturity_report()` 不含已知英文 blocker / next step；report writer 覆盖 `maturity-score.yaml` 和 `maturity-report.md` 中文文案；assess integration 覆盖刷新报告不含 `evidence:` / `blockers:`；guided init happy path 覆盖 CLI 不再出现已知英文 maturity blocker。
- 完成内容：中文化 maturity evidence / blocker / next requirement / blocking cap；新增中文 maturity report rendering helper；asset writer 和 assess 共用该 helper；同步 todo、spec 和 plan。
- Self-Harness Gate：同一 high priority todo 只剩 LLM-planned deep scan 主线；它风险更高，下一轮应重新做 gap analysis，优先判断是否先做 planner prompt / coverage confidence 的较窄纵向切片。

## 2026-05-31 Guided Init 多栈仓库组合建模

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：LLM-first Repository Understanding、CLI Experience、Guides / Sensors、Maturity & Evolution。
- init North Star 旅程阶段：基础扫描、扫描结果友好呈现、与用户对齐扫描理解、写入前 Harness 设计预览。
- Gap Analysis 摘要：真实 `ai4se` 试跑中扫描看到了 Python、Flask、React、TypeScript、Vite、Docker、Nginx 等线索，但 `primary_stack` 只能在 Java / .NET / Node / unknown 中选择，用户补充提示也只能修正为单栈，导致多栈仓库容易被降级为 `unknown`。
- 用户故事：作为 Harness Maintainer，当我在 Python Flask + React / TypeScript 混合仓库上运行 guided `init` 时，我可以看到系统用中文说明组合技术栈、模块角色和验证能力，并让后续 Guide / Sensor 推荐围绕真实后端与前端模块，而不是误导成单一技术栈或 unknown。
- 当前代码 gap：`LLMScanProposal.primary_stack` 缺少 `python-flask`；`scan_reconciler` 没有 Python Flask evidence validation 和组合栈 profile；`interactive_init` 只显示 `_stack_label(primary_stack)`；`weapon_library` 只按 primary stack 选择一组栈特定 weapons。
- 关键决策 / 取舍：新增 `python-flask` 作为第一批 Python 主栈；React / TypeScript / Vite 暂由既有 `node` canonical 栈承载；新增 `stack_profile` 作为 `stack_extensions` 中的派生用户叙事，不替代 `primary_stack`、`stacks`、`modules` 机器契约；本轮不做完整 LLM-planned deep scan。
- Assumptions / risks：`python-flask` 不能代表所有 Python Web 项目，FastAPI / Django 后续应单独建模；多栈 profile 依赖 LLM proposal 和 evidence validation，扫描覆盖不足仍需通过已有 uncertainty 机制提醒用户。
- Sub agent 使用情况：使用两个只读子代理并行做 gap 排序与测试覆盖审查；两个结论均建议多栈建模优先，成熟度中文叙事与 LLM-planned deep scan 保留为后续切片。
- 价值切分说明：本轮完成“扫描理解 -> schema/reconciler 验证 -> CLI 组合表达 -> weapon selection -> 正式资产保留”的纵向闭环，避免只改字段或只改文案。
- 验收标准及验证方式：unit 覆盖 `python-flask` scan schema、Python Flask + React evidence validation、`stack_profile`、多栈 weapon selection；integration 覆盖 guided CLI 输出 `Python Flask 后端 + React / TypeScript 前端`、补充入口包含 `stack=python-flask` 和自然语言多栈说明，并验证 project inventory / weapon selection 产物。
- 完成内容：扩展 scan schema 与 LLM prompt；reconciler 增加 Python Flask / Node 多栈验证和 `stack_profile`；weapon library 增加 Python Flask 与 Node / 前端 Guide / Sensor；guided CLI 使用组合栈标签并允许 `stack=python-flask`。
- Self-Harness Gate：下一轮候选 gap 优先继续消化同一 todo 中的成熟度英文叙事中文化；更大范围的 LLM-planned deep scan 仍需单独 spec，避免和当前多栈 schema 扩展混在一起。

## 2026-05-31 Guided Init 高风险发现确认链路

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：CLI Experience、Progressive Collaboration、Guides / Sensors、Workflow Routing、Maturity & Evolution。
- init North Star 旅程阶段：扫描结果友好呈现、深度追问、人工确认资产、正式 Guide / Sensor 生成。
- Gap Analysis 摘要：真实 `ai4se` guided `init` 发现 `docs/a.json` 可能包含明文 API key，但 CLI、questionnaire、Guide 和 Sensor 都只把它当作普通风险区域展示，缺少“疑似高影响风险、需要人工确认、命中后升级 workflow / 验证”的连续链路。
- 用户故事：作为 Harness Maintainer，当首次 guided `init` 发现疑似密钥、凭证、安全、支付、权限或数据迁移风险时，我可以在终端、`.ai/questionnaire.yaml`、`.ai/human-input-needed.md`、`.ai/guides/project-context.md` 和 `.ai/sensors/verification.md` 中看到它被标记为待确认高风险，并理解它对人工确认、Sensor 验证和 standard workflow / 人工升级的影响。
- 当前代码 gap：`risk_areas` 已进入 inventory 和正式资产，但 `_risk_attention_lines()`、`build_questionnaire()`、Guide writer 和 Sensor writer 都没有区分普通风险和高影响风险；`write_initial_assets()` 也没有把 risk areas 传给 questionnaire。
- 关键决策 / 取舍：新增轻量 `risk_signals` helper 统一分类风险线索，不迁移 `risk_areas` schema，不自动清理密钥，不执行 Runtime，不把疑似风险写成已确认事实，也不自动修改正式 workflow routing policy。
- Assumptions / risks：关键词分类可能误报，因此所有高风险表达都使用“疑似 / 待确认 / 需人工确认”；更强准确性留给后续 LLM-planned deep scan 和 detector validation。
- Sub agent 使用情况：使用两个只读子代理并行确认 milestone 边界、代码路径和非目标；结论建议把 CLI 高风险展示、human-input 确认、Guide/Sensor 表达合并为一个完整用户故事。
- 价值切分说明：本轮消化同一 high priority todo 中的高风险信任问题，覆盖用户从扫描发现到正式资产审查的完整确认链路；多栈建模、成熟度中文叙事和 LLM-planned deep scan 保持后续独立工作包。
- 验收标准及验证方式：unit 覆盖高风险分类、questionnaire schema、Guide / Sensor 文案；integration 覆盖 guided CLI 在进入团队规则前输出 `高风险，需人工确认`、具体路径和 standard workflow 升级提示；write assets 测试覆盖 `human-input-needed.md` 包含高风险确认问题且 `harness-config.yaml` 不出现具体风险路径 routing rule。
- 完成内容：新增 `risk_signals.py`；CLI 风险摘要和建议补充区标记高风险；questionnaire schema 增加 `risk_area_confirmation`；`write_initial_assets()` 传递 risk areas；Guide / Sensor 对待确认高风险使用专门表达。
- Self-Harness Gate：下一轮候选 gap 继续优先消化 `docs/todos/`，首选同一 todo 中“多栈表达与自然语言用户补充入口”，其次是“成熟度 blocker 中文化”，再其次是“LLM-planned deep scan 架构切片”。

## 2026-05-31 Guided Init 采样覆盖不足中文化

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：CLI Experience、深度扫描、可解释 evidence、Maturity & Evolution。
- init North Star 旅程阶段：基础扫描、扫描结果友好呈现、与用户对齐扫描理解。
- Gap Analysis 摘要：真实多栈仓库中源码 bucket 被抽样时，机器 warning `source:.py skipped 73 files` 会直接出现在 guided CLI “不确定性”区块；`scan-metadata.yaml` 已有 coverage / bucket / skipped 统计，但 CLI 没把这些审计字段翻译成用户可理解的覆盖不足说明。
- 用户故事：作为 Harness Maintainer，当首次 guided `init` 扫描一个源码文件较多的仓库时，我可以在“不确定性”中看到中文说明：某类源码已抽样多少、仍有多少未进入初始摘要、这会影响哪些判断、我应该补充什么，从而理解扫描覆盖边界并校准关键模块或风险路径。
- 当前代码 gap：`evidence_collector._coverage()` 的 warning 只有 code / bucket / 英文 message；`interactive_init._uncertainty_attention_lines()` 原样输出 `scan_warnings[].message`，导致内部 bucket warning 泄露到用户界面。
- 关键决策 / 取舍：本轮只做 source sampling warning 的中文化和 metadata detail；不改变采样上限、不把 coverage gap 变成失败、不实现完整多栈建模、高风险候选治理或 LLM-planned deep scan。未知 warning 仍保留原 message 作为调试线索。
- Assumptions / risks：旧 inventory 如果缺少 coverage 详情，会使用中文通用覆盖不足说明；机器 metadata 继续保留 warning code / bucket / message 和 coverage 详情，避免损失审计能力。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行确认选题优先级、代码路径和测试层级；结论一致建议本轮优先做 skipped / sampled 中文化，把高风险突出和多栈建模留作后续切片。
- 价值切分说明：本轮继续优先消化 high priority todo，但只处理“用户能不能理解扫描覆盖边界”这一条独立信任问题；它直接改善 CLI-first `init` 体验，并为后续 targeted scan / deep scan 留出明确用户补充入口。
- 验收标准及验证方式：unit 覆盖 coverage warning 保留 total / selected / skipped 计数；guided integration 覆盖“不确定性”输出中文抽样说明、包含 `.py` / `20/93` / `73`，且不再出现 raw `source:.py skipped 73 files` 或英文测试证据 warning。
- 完成内容：`EvidenceCoverage.warnings` 补充抽样统计 detail；`interactive_init.py` 新增 warning 中文格式化 helper；guided scan attention summary 测试从英文 warning 断言更新为中文用户语义断言。
- Self-Harness Gate：下一轮候选 gap 首选同一 todo 中的“高风险风险项突出展示并进入人工确认 / 候选链路”，其次是“多栈表达与用户补充入口”，再其次是“成熟度 blocker 中文化”和“LLM-planned deep scan 架构切片”。

## 2026-05-31 Init 工具工作区 Evidence 降噪

- 关联 todo：`docs/todos/guided-init-ai4se-real-repo-findings.md`。
- North Star 模块：CLI Experience、深度扫描、可解释 evidence、LLM-first evidence hygiene。
- init North Star 旅程阶段：基础扫描、扫描结果友好呈现、与用户对齐扫描理解。
- Gap Analysis 摘要：真实 `ai4se` guided `init` 试跑显示 `.claude/worktrees`、`.opencode`、`deploy-package/.opencode` 等工具工作区中的 `package.json` 会进入 key evidence，并可能优先出现在 CLI “判断依据”中；同时 Python 项目根文件如 `pyproject.toml`、`requirements.txt` 还没有被视为关键 evidence。
- 用户故事：作为 Harness Maintainer，当我在包含 AI 工具工作区和真实项目 manifest 的仓库上运行 guided `init` 时，我可以看到根项目和真实应用文件作为优先判断依据，而不是工具工作区里的临时 `package.json`，从而相信 Builder 正在理解项目本身。
- 当前代码 gap：`evidence_collector._walk_files()` 未忽略 `.claude` / `.opencode`；`_is_key_file()` 未覆盖 Python 项目 manifest；`scan_reconciler` 和 guided CLI 会沿用 `evidence.key_files` 作为判断依据。
- 关键决策 / 取舍：本轮只在 evidence collection 层做 hygiene，忽略 `.claude` / `.opencode` 任意层级目录，并把 `pyproject.toml`、`requirements*.txt`、`Pipfile`、`poetry.lock` 纳入 key evidence；不扩展 primary stack 枚举，不实现完整多栈模型，也不忽略整个 `deploy-package`。
- Assumptions / risks：`.claude` / `.opencode` 语义上属于工具状态目录，忽略后如果客户把真实业务代码放在其中，需要用户显式补充或后续高级扫描策略处理；Python 关键文件进入 evidence 只提升输入可信度，不代表当前 schema 已支持 Python primary stack。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 ai4se todo；一个定位 evidence 噪声、skipped 和高风险展示落点，另一个确认多栈表达和英文成熟度 blocker 是后续更大切片。
- 价值切分说明：本轮优先消化 `docs/todos/` 中 high priority 工作项，但只处理第一个可独立验收的信任问题；skipped 中文化、高风险突出、多栈建模和中文成熟度 blocker 继续保留为后续切片。
- 验收标准及验证方式：unit 覆盖 `collect_evidence()` 忽略 `.claude` / `.opencode` / `deploy-package/.opencode` 文件，并确认根 `package.json`、`pyproject.toml`、`requirements.txt` 进入 key / priority evidence。
- 完成内容：扩展 `IGNORED_DIRS` 和 `KEY_FILE_NAMES`；新增 evidence collector 单元测试固定工具工作区降噪行为；同步本 todo 的已完成切片记录。
- Self-Harness Gate：下一轮候选 gap 首选同一 todo 中的 skipped / sampled 文件信息中文化和覆盖不足说明，其次是高风险风险项突出展示，再其次是多栈表达与成熟度英文 blocker 中文化。

## 2026-05-31 Guided Init 启动边界说明

- North Star 模块：CLI Experience、Progressive Collaboration、Maturity & Evolution。
- init North Star 旅程阶段：启动与目标说明、CLI 视觉焦点。
- Gap Analysis 摘要：首次 guided `init` 在扫描前只有泛化的 `.ai` 资产说明和 `继续生成 Harness?`，用户还不知道扫描范围、后续确认范围、预计生成资产，以及 Runtime、`.ai/task-runs`、benchmark 和正式写入边界。
- 用户故事：作为首次使用 Harness Builder 的 Harness Maintainer，我希望在等待扫描前先理解本次流程会做什么、不会做什么、何时才写入正式资产，从而能判断是否继续进入耗时扫描。
- 关键决策 / 取舍：新增稳定的 `== 启动说明 ==` CLI 区块，放在已有 Harness 维护入口之后、`继续生成 Harness?` 之前；本轮只增强首次生成向导，不改变非交互输出、扫描、LLM、成熟度评分或资产 schema；generation trace 从会话开始记录，但文案明确它不同于最终确认后写入的正式 Harness 资产。
- Assumptions / risks：启动说明保持短列表，避免把首次 CLI 变成说明书；目标输出目录和已有 `.ai` 状态的更细展示留给后续阶段标题和状态 contract 切片。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查启动说明缺口和用户补充分流缺口；本轮采纳启动说明切片，将“自然语言补充不应伪装成扫描事实”记录为后续更大契约切片。
- 验收标准及验证方式：integration 覆盖 `== 启动说明 ==` 在 `继续生成 Harness?` 和 `扫描仓库` 之前出现，包含扫描范围、确认范围、生成资产、Runtime / `.ai/task-runs` / benchmark 和最终 `confirm` 写入边界；同时断言 `--non-interactive` 不输出该 guided 启动说明。
- Self-Harness Gate：下一轮候选 gap 首选“用户扫描补充后的结构化吸收与自然语言说明分流”，避免自由文本被表达成已验证扫描事实；其次是 CLI 阶段标题统一。

## 2026-05-31 Init CLI 交付摘要增强

- North Star 模块：CLI Experience、Maturity & Evolution、Guides / Sensors、Progressive Collaboration。
- init North Star 旅程阶段：写入后的交付摘要、CLI 视觉焦点、下一步入口。
- Gap Analysis 摘要：`init` 已经在 CLI 中展示扫描、成熟度初评、用户补充影响和写入前 preview，但写入完成后的 completion message 仍只显示英文资产路径、成熟度、benchmark readiness 和少量入口；它没有完整承担 North Star 要求的 CLI-first 交付摘要职责。
- 用户故事：作为 Harness Maintainer，当我完成首次 `init` 写入后，我可以直接在 CLI 中看到本次生成结果、当前 L0-L4 成熟度、主要证据 / 缺口、Benchmark 状态、优先查看入口、仍需人工确认的问题和下一步命令，从而不用先打开 Markdown 文件也能理解初始化交付。
- 当前代码 gap：`render_init_completion_message()` 只读取 `maturity-score.yaml` 和 benchmark report，缺少生成结果清单、待确认问题摘要、优先入口原因和 CLI / Markdown 边界说明；integration 测试只覆盖“当前成熟度”和 benchmark 字段。
- 关键决策 / 取舍：本轮只增强 completion message，不改扫描、LLM、成熟度评分、资产 schema 或已有 Harness 维护入口；`questionnaire.yaml` 通过 `Questionnaire` schema 只读校验后提取待确认问题，缺失时显式提示查看 `human-input-needed.md`。
- Assumptions / risks：completion message 是交付说明，不是新的交互菜单；首次 `init` 仍不默认运行 benchmark，也不执行 Runtime task-run。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 guided init transcript 和 completion summary gap；两者均建议优先补齐 CLI completion summary，并把更完整 Transcript Contract V1 留作后续切片。
- 价值切分说明：本轮直接回应“CLI 工具第一优先级”，把写入后的理解和下一步从 Markdown 前移到终端，同时保留 Markdown 作为持久化材料。
- 验收标准及验证方式：unit 覆盖 completion message 的 `== 初始化完成 ==`、生成结果、成熟度、Benchmark、优先查看、仍需人工确认和 CLI-first 说明；integration 覆盖非交互与 guided init 输出均包含这些交付摘要要素，并覆盖已有 Harness `exit` / `assess` 不追加首次初始化交付摘要。
- 完成内容：`render_init_completion_message()` 改为中文 CLI-first 交付摘要；新增生成资产摘要、优先入口和待确认问题 helper；`cli.py` 通过 trace summary 区分首次生成与已有 Harness 维护动作；init workflow、todo 和演进记录同步。
- Self-Harness Gate：下一轮候选 gap 首选“首次 guided init 启动说明和阶段标题统一”，其次是“用户补充后区分结构化吸收与 notes 保存”，继续围绕 CLI-first 用户旅程推进。

## 2026-05-31 Init 资产仓库特异性增强

- North Star 模块：CLI Experience、Guides / Sensors、Maturity & Evolution、Progressive Collaboration。
- init North Star 旅程阶段：用户补充影响链路、正式资产生成、初始化交付摘要。
- Gap Analysis 摘要：guided `init` 已经能展示扫描关注点、成熟度初评和用户补充影响，但正式写入后的 `project-context.md`、`verification.md` 和 `init-summary.md` 仍偏模板化；结构化 `module/command/risk` 主要进入 inventory/catalog，团队规则和 workflow 补充进入 interaction decisions，三者缺少在正式语义资产中的完整闭环。
- 用户故事：作为 Harness Maintainer，当我在 `init` 中补充或确认模块、风险区域、验证命令和团队规则后，我希望在正式生成的 Guide、Sensor 和 init summary 中看到这些信息如何进入 Harness 资产并关联成熟度缺口，从而确认生成结果是面向当前仓库定制，而不是模板拼装。
- 当前代码 gap：`write_guide_assets()` 不消费 `CommandCatalog`；`write_sensor_assets()` 不消费 `ProjectInventory` 风险区域；`write_init_summary()` 只消费 `MaturityReport`，没有展示本仓库关键事实、用户补充和资产补缺关系。
- 关键决策 / 取舍：本轮只增强首次 `init` 的语义 Markdown，不新增机器消费 schema、不改 maturity scoring、不改 workflow policy、不把 workflow 自然语言补充直接应用为 routing 规则；扫描事实从 inventory/catalog 渲染，自然语言补充从 interaction decisions 渲染。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行调研资产数据流和 benchmark 质量约束；结论支持本轮先做 Guides / Sensors / Summary 的仓库特异性注入，benchmark 语义质量评分暂缓。
- 价值切分说明：本轮面向用户完成 `init` 后最先审查的正式产物，让用户确认“扫描与补充确实改变了 Harness”，而不是只在 CLI 里看到一次性预览。
- 验收标准及验证方式：unit 覆盖 Guide/Sensor/Summary 渲染模块、风险、命令、用户补充和成熟度缺口关联；integration 覆盖 guided structured scan 补充进入 `project-context.md`、`verification.md` 和 `init-summary.md`。
- 完成内容：Guide writer 增加风险区域、验证入口和成熟度缺口关联；Sensor writer 增加风险与验证映射和成熟度缺口关联；init summary 增加本仓库关键事实、本次吸收的用户补充、资产如何补齐缺口；write assets 编排传递 inventory / commands / interaction decisions。
- Self-Harness Gate：后续继续围绕 `init` 提升交互扫描深度和产出质量；候选 gap 包括 architecture signals 进入 Guide、team rules 对 Sensor/Workflow 的更明确影响、benchmark repository-specific quality score 从 soft score 逐步增强。

## 2026-05-31 Guided Init 扫描后成熟度初评前置

- North Star 模块：CLI Experience、Maturity & Evolution、Progressive Collaboration、深度扫描。
- init North Star 旅程阶段：扫描结果友好呈现、成熟度初评与差距解释、与用户对齐扫描理解。
- Gap Analysis 摘要：guided `init` 已经有扫描发现、风险 / 不确定性 / 验证缺口分组和写入前成熟度设计预览，但成熟度解释发生在团队规则、候选审查和 Workflow 展示之后；用户在扫描补充前还不知道当前扫描会如何影响 L0-L4 等级、下一等级差距和后续 Harness 推荐。
- 用户故事：作为 Harness Maintainer，当我首次 guided `init` 扫描一个遗留仓库并准备补充或修正扫描理解时，我可以先看到基于当前扫描结果的 L0-L4 成熟度初评、下一等级差距和会影响判断的补充方向，从而知道应该优先确认哪些模块、命令、风险或团队规则。
- 当前代码 gap：`_show_prewrite_maturity_preview()` 只服务最终写入前确认；`_collect_scan_supplement()` 之前缺少成熟度语境，用户补充仍偏字段修正。
- 关键决策 / 取舍：本轮只新增 guided CLI 前置初评，复用 `build_maturity_report()`、`HarnessConfig.default()` 和 `select_weapon_library()`；不改 maturity schema、不改评分规则、不改变非交互输出和正式资产契约。
- Assumptions / risks：前置初评是基于当前扫描的写入前预测，不代表正式 Harness 已写入或 benchmark 已通过；用户后续修正后，最终写入前 preview 仍会重新计算。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 guided init 用户旅程和资产质量缺口。一个推荐后续做用户补充影响链路可见化；另一个推荐后续做仓库特异性资产注入与成熟度缺口叙事。
- 价值切分说明：本轮保护的是“扫描发现 -> 用户补充”之间的决策质量，让用户知道为什么要补充 hard gate、模块边界、风险区域和团队规则，而不是盲目回答字段。
- 验收标准及验证方式：integration 覆盖 `扫描后的成熟度初评` 出现在 `扫描发现` 后、`需要你补充或修正的地方` 前，并包含 L0 起步、预计基线、下一目标、主要差距和建议优先补充；非交互输出不出现该 guided 文案。
- 完成内容：`interactive_init.py` 新增扫描后成熟度初评 helper；init workflow、spec/plan 和演进记录同步。
- 全量回归修正：真实 RuoYi-Vue acceptance 暴露 DeepSeek evidence planner 偶发请求未在 `files[].path` 中的近似路径；已补一次契约修正重试，重试仍失败时继续显式失败，不放宽 allowlist、不做 Python 近似匹配、不引入确定性 fallback，并同步 LLM contract 和 prompt 精确路径要求。
- Self-Harness Gate：下一轮候选 gap 首选“用户补充影响链路可见化”或“仓库特异性资产注入”，重点让结构化补充和团队规则更明确进入 preview、summary、Guides / Sensors 和质量断言。

## 2026-05-31 Guided Init 扫描内部阶段进度

- North Star 模块：CLI Experience、Progressive Collaboration、深度扫描、可解释失败边界。
- init North Star 旅程阶段：阶段化扫描与进度反馈、扫描结果友好呈现。
- Gap Analysis 摘要：guided `init` 已有“扫描仓库”和“扫描完成”的粗粒度提示，但 `scan_repository()` 内部的 evidence 收集、LLM evidence plan、补充 evidence 读取、最终 LLM scan 和 reconcile 仍是一个阻塞调用；真实仓库和真实 LLM 场景下，用户无法判断耗时来自哪个内部阶段。
- 用户故事：作为 Harness Maintainer，当我首次 guided `init` 一个真实遗留仓库且扫描和 LLM 调用需要等待时，我可以看到正在收集 evidence、请求 LLM 规划补充 evidence、读取补充 evidence、请求最终 LLM scan 和调和扫描结果的阶段状态，从而判断程序仍在工作，并能在失败时定位失败发生在哪个阶段。
- 当前代码 gap：`scan_repository()` 没有可观察的进度事件；guided init 只能在调用前后输出粗粒度文案；非交互路径不应承担这种 UI transcript 契约。
- 关键决策 / 取舍：给 `scan_repository()` 增加 optional keyword-only progress callback 和 `ScanProgressEvent`，默认 `None`；guided init 通过签名检测兼容旧单参数 fake scan；本轮不改 LLM prompt、schema、reconciler 或正式产物契约。
- Assumptions / risks：progress event 是过程可观察性接口，不是新的落盘机器产物；事件 id 由 unit test 固定，中文文案由 guided renderer 翻译。
- Sub agent 使用情况：使用只读子代理审查 scan pipeline、monkeypatch 兼容点和测试策略；结论建议 unit 精确锁定 callback 事件序列，guided integration 只断言关键中文阶段和顺序。
- 价值切分说明：本轮面向首次 `init` 中最容易长时间等待的用户旅程，不是孤立日志；它让后续更深的交互扫描和智能 evidence expansion 有稳定的阶段可观察性基础。
- 验收标准及验证方式：unit 覆盖 collect / plan / expand / llm-scan / reconcile 的 started/completed 顺序和 details；guided integration 覆盖阶段文案出现在“扫描仓库”和“扫描完成”之间；非交互测试断言不出现 guided 阶段文案。
- 完成内容：`scan_repo.py` 新增 `ScanProgressEvent` 与 progress callback；`interactive_init.py` 接入 guided renderer；init workflow、spec/plan 和演进记录同步。
- Self-Harness Gate：后续循环按用户最新要求优先继续完善 `init` 流程深度、用户交互扫描和产出内容质量。

## 2026-05-31 Guided Init 推荐项成熟度关联

- North Star 模块：Maturity & Evolution、CLI Experience、Guides / Sensors、Progressive Collaboration。
- init North Star 旅程阶段：成熟度驱动的 Harness 设计预览、最终确认前审查。
- Gap Analysis 摘要：写入前 preview 已展示 L0 起步、写入后预计基线、整体阻断项、推荐动作、Guides / Sensors / Workflow routing，但每个 Guide / Sensor 推荐项只显示 action，未说明它关联哪个成熟度维度、解决哪个阻断项、对下一阶段能力有什么贡献。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 写入 `.ai/` 前审查 Harness 设计预览时，我可以看到每个即将生成的 Guide / Sensor 推荐对应的成熟度维度、正在缓解的阻断项和下一阶段贡献，从而判断这套 Harness 是围绕当前仓库的成熟度缺口生成，而不是固定模板拼装。
- 当前代码 gap：`build_maturity_report()` 已有 dimensions、blockers 和 next level requirements；weapon library 已有 kind、tags、gate 和 recommended action；但 `_show_prewrite_maturity_preview()` 没把两者关联后呈现给用户。
- 关键决策 / 取舍：本轮只改 guided CLI preview 渲染层，不改 `WeaponLibraryEntry`、`MaturityReport`、`weapon-library-selection.yaml` 或正式资产 schema；成熟度关联使用内置 weapon tags 和 planned maturity 维度做保守推导。
- Assumptions / risks：这是写入前预计基线叙事，不表示当前仓库已经达到相关成熟度；对无 blocker 的维度展示保持基线和后续 benchmark / Runtime 验证的说明。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 preview gap 和测试策略；结论支持本轮做 CLI 逐项 maturity linkage，并建议补一个小 unit 固定映射规则。
- 价值切分说明：本轮保护的是用户在最终确认前的审查动作，让用户能判断每个 Guide / Sensor 与 L0-L4 缺口的关系，而不是只看到资产清单。
- 验收标准及验证方式：integration 覆盖 preview 区的 Guides 和 Sensors 都出现 `关联成熟度`、`解决阻断`、`下一阶段贡献`；unit 覆盖 Guide 映射到 guides / risk_control 阻断，Sensor 映射到 sensors / verification_sophistication 阻断。
- 完成内容：`interactive_init.py` 新增 weapon preview maturity linkage helper；init workflow、spec/plan 和演进记录同步。
- 验证结果：targeted integration / unit 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：下一轮候选 gap 首选“真正的 scan 内部阶段 callback”，其次是“生成资产 Markdown 中保留推荐项成熟度来源”。

## 2026-05-31 Guided Init 扫描关注点分组

- North Star 模块：CLI Experience、Progressive Collaboration、深度扫描、成熟度叙事输入。
- init North Star 旅程阶段：扫描结果友好呈现、与用户对齐扫描理解和成熟度判断。
- Gap Analysis 摘要：guided `init` 已有扫描前/后进度提示和写入前成熟度预览，但 `_show_scan_findings()` 仍主要展示技术栈、证据、模块和命令；风险区域、scan warning、低置信度命令、无 hard gate、缺失验证类型等关注点没有在用户补充前形成清晰分组，用户不容易判断应该纠正哪里。
- 用户故事：作为 Harness Maintainer，当首次 guided `init` 扫描完成并准备补充或修正扫描理解时，我可以在 CLI 中看到按“风险区域”“不确定性”“验证缺口”“建议补充”分组的关注点摘要，从而知道哪些判断需要优先确认、哪些验证能力会影响后续 Guides / Sensors / 成熟度预览。
- 当前代码 gap：`ProjectInventory.stack_extensions` 已包含 `risk_areas`、`scan_warnings`、`needs_human_confirmation` 和 LLM proposal confidence；`CommandCatalog` 已包含 gate、source、confidence 和 type；但这些数据没有被翻译成面向用户的扫描关注点。
- 关键决策 / 取舍：本轮只改 guided CLI 渲染层，不改 schema、不改 LLM prompt、不改 scan reconciler、不改变非交互输出；缺口表达统一使用“当前扫描未确认 / 建议补充”，避免把 evidence 缺失断言为项目能力不存在。
- Assumptions / risks：旧 inventory 可能没有完整 `stack_extensions`，渲染层必须容错；风险摘要不是成熟度评分，后续成熟度仍由 preview 和 maturity report 负责解释。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查 scan findings gap 和测试策略；结论一致建议本轮做“风险 / 不确定性 / 验证缺口分组展示”，且只用 guided integration 覆盖即可。
- 价值切分说明：本轮保护的是用户在“扫描完成 -> 输入补充”之间的判断动作，不是孤立文案；它让用户在正式生成 Guides / Sensors 前知道哪些扫描判断需要修正。
- 验收标准及验证方式：integration 覆盖 happy path 中四个关注点分组出现在“扫描发现”后、“团队规则”前；专门 fake scan 场景覆盖风险路径、scan warning、低置信度 soft command、无 hard gate 和建议补充真实 hard gate。
- 完成内容：`interactive_init.py` 新增扫描关注点摘要与 helper；README、init workflow、spec/plan 和演进记录同步。
- 验证结果：targeted guided scan attention tests 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：下一轮候选 gap 首选“Guide / Sensor 推荐与成熟度维度、阻断项的逐项关联”，其次是“真正的 scan 内部阶段 callback”。

## 2026-05-31 Guided Init 扫描进度反馈

- North Star 模块：CLI Experience、Progressive Collaboration、深度扫描、可解释失败边界。
- init North Star 旅程阶段：启动与目标说明、阶段化扫描与进度反馈、扫描结果友好呈现。
- Gap Analysis 摘要：首次 guided `init` 在用户确认继续后会直接进入 `scan_repository()`，真实仓库和真实 LLM 场景下可能长时间无输出；扫描失败时虽然 CLI 会显式失败并记录 trace，但用户无法从屏幕上判断失败发生在扫描阶段，也不知道正式 `.ai` Harness 资产尚未写入。
- 用户故事：作为 Harness Maintainer，当我首次运行 guided `init` 并确认继续后，我可以在耗时扫描开始前看到系统正在收集仓库证据、请求 LLM 结构化扫描和调和 evidence；如果扫描失败，我能看到失败阶段、原因摘要和“未写入正式 Harness 资产”的边界。
- 当前代码 gap：`run_guided_init()` 只有 trace event，没有用户可见的扫描进度；`run_non_interactive_init()` 作为自动化路径不应被改变。
- 关键决策 / 取舍：本轮只在 guided 分支的 `scan_repository()` 调用周边增加阶段提示和失败边界，不改变 `scan_repository()` 签名，不加入 callback，不拆分内部扫描 pipeline，避免破坏现有 monkeypatch 测试和非交互输出语义。更细粒度的 evidence / LLM / reconcile 分阶段 callback 保留为后续独立切片。
- 边界情况 / 失败模式及回应：扫描失败继续重新抛出原异常，不吞异常、不 fallback、不写入正式 inventory、config、Guides、Sensors 或 Workflow Skills；异常类型和消息只作为原因摘要展示。
- Sub agent 使用情况：使用两个只读 explorer 子代理并行审查实现切入点和测试策略；一个指出如给 `scan_repository()` 增加 progress 参数会破坏现有 monkeypatch，另一个建议用 `typer.echo` 调用顺序证明进度提示发生在扫描调用前。
- 价值切分说明：本轮解决的是用户在 `init` 第一段耗时等待中的可解释性和失败边界，不是内部扫描智能增强；它为后续更深的交互扫描和阶段 callback 打基础。
- 验收标准及验证方式：integration 覆盖 happy path 中 `扫描仓库` / `扫描完成` 出现在 `扫描发现` 前；失败路径 monkeypatch `scan_repository()` 抛错，断言扫描前已输出进度、失败提示包含原因和未写入正式资产，并断言正式 Harness 资产未生成。
- 完成内容：`interactive_init.py` 新增 guided 扫描开始、完成、失败渲染；init workflow 规则和 spec/plan 同步。
- 验证结果：targeted guided scan progress tests 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：下一轮候选 gap 首选“扫描结果按风险 / 不确定性 / 验证缺口分组展示”，其次是“Guide / Sensor 推荐与成熟度维度、阻断项的更精确关联”。

## 2026-05-31 Guided Init 用户补充复述与影响说明

- North Star 模块：CLI Experience、Progressive Collaboration、Maturity & Evolution、Guides / Sensors。
- init North Star 旅程阶段：扫描理解对齐、成熟度初评、深度追问、设计预览、最终确认。
- Gap Analysis 摘要：guided `init` 已能收集自然语言和结构化补充，并把它们写入部分资产；但最终确认只展示数量，用户无法在写入前看到系统如何理解这些补充，也不知道它们会影响 Guide、Sensor、成熟度预览或 Workflow 说明。CLI 阶段进度、扫描结果分组、推荐项成熟度关联和写入后 summary 一致性仍是后续 gap。
- 用户故事：作为 Harness Maintainer，当我在首次 guided `init` 中补充模块边界、真实验证命令、风险区域、团队规则或工作流说明时，我可以在写入前看到系统如何理解这些补充，以及它们会影响哪些 Guides、Sensors、成熟度预览或 Workflow 说明，从而确认 Harness Builder 不是只记录文本，而是在用我的输入调整 Harness 设计。
- 当前代码 gap：`_collect_scan_supplement()` 和 `_apply_scan_overrides()` 已能记录和应用补充，但 `_confirm_summary()` 只输出团队规则数量、hard gate 命令和 workflow 名称，缺少补充内容与影响面复述。
- 关键决策 / 取舍：不新增 LLM 语义理解；结构化补充继续更新 inventory / commands / risk，非结构化自然语言保持人工补充说明；Workflow note 只进入说明和确认记录，不直接修改 routing policy。
- Assumptions / risks：自然语言补充不能自动变成正式规则；长补充在 CLI 中只展示摘要，完整内容仍进入 interaction decisions 和 Markdown 产物。
- Sub agent 使用情况：使用两个只读 explorer 子代理分别审查 init North Star 旅程 gap 和测试覆盖缺口；两者都把“用户补充复述与影响说明”列为高价值下一步。
- 价值切分说明：本轮保护的是“渐进式协作”用户价值，不是孤立字段或文案；用户在最终确认前能看到自己的输入被系统吸收，并理解其对后续 Harness 设计的影响。
- 验收标准及验证方式：新增 integration 测试断言 `最终确认` 之后包含具体 scan note、团队规则、workflow note 和“补充影响”；断言 `interaction-decisions.yaml`、`project-context.md`、`human-input-needed.md` 保留补充；相关 guided init 测试保持通过。
- 完成内容：`interactive_init.py` 在最终确认前输出“已吸收的用户补充”和“补充影响”；init workflow 规则和 spec/plan 同步。
- 验证结果：targeted guided init tests 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：本轮强化了用户输入消费链路。下一轮候选 gap：CLI 扫描阶段进度反馈、扫描结果按风险/不确定性分组、preview 与落盘资产 / init-summary 的一致性验收。

## 2026-05-31 Guided Init 写入前成熟度预览

- North Star 模块：CLI Experience、Maturity & Evolution、Workflow Routing、Guides / Sensors。
- Gap Analysis 摘要：首次 guided `init` 已能扫描、收集补充、展示候选并写入资产，但成熟度叙事主要发生在写入完成后的 `init-summary.md` 和 CLI completion message。用户在输入 `confirm` 前无法判断当前是否从 L0 起步、写入后预计建立什么基线、下一等级缺什么，以及 `standard` workflow 如何参与高风险任务治理。
- 用户故事：作为 Harness Maintainer，当我第一次对遗留仓库运行 guided `init` 并准备确认写入 `.ai/` 前，我可以先看到当前 Harness 成熟度初评、写入后预计基线、下一目标、阻断项、推荐补齐动作，以及 Guides / Sensors / Workflow routing 设计预览，从而在写入前判断这套 Harness 是否值得接管和如何继续完善。
- 关键决策 / 取舍：不新增 LLM 调用，不提前写入 `.ai/`；复用现有 `build_maturity_report(ai=None, ...)` 计算 planned baseline，并在 CLI 中明确区分当前 L0 起点和确认写入后的预计基线。本轮不实现扫描阶段进度 callback、不重构 scan pipeline、不增强自然语言语义归因。真实 acceptance 暴露 RuoYi-Vue self-improve 的 LLM 输出过长和 evidence source 契约矛盾后，本轮只收紧 review-only LLM 输出长度约束，并把 Runtime repair loop 证据源调整为 `.ai/task-runs/` 契约路径，不引入 silent fallback。
- 边界情况 / 失败模式及回应：启动 trace 可能已创建 `.ai/runs`，但这不代表项目已有 Harness；只有已存在正式 inventory / config 时才按 partial Harness 处理。用户从最终确认返回修改 scan 后，会重新选择武器库并刷新候选报告，让下一次预览基于更新后的 inventory / commands。maturity review / asset candidate 真实 LLM 输出必须保持短 JSON；下游 review evidence source 仍只接受 Builder 提供的 `.ai/` allowlist。
- Sub agent 使用情况：使用两个只读 explorer 子代理分别审查 North Star / 代码旅程 gap 和 guided init 测试覆盖；结论共同推荐“扫描后成熟度初评 + 写入前 Harness 设计预览”作为下一轮最高价值 `init` 切片。
- 价值切分说明：本轮面向首次 `init` 用户旅程，不是内部字段补丁；它把 `init` 从“文件生成器写完后解释”推进到“写入前用成熟度框架解释设计方案”。
- 可执行验收标准及验证方式：guided init integration 覆盖成熟度预览出现在最终确认前、当前从 L0 起步、显示写入后预计基线 / 下一目标 / 阻断项 / 推荐动作、展示 Guides / Sensors / Workflow routing，并包含 `standard-escalation` 高风险升级语义；同时断言 CLI 不暴露内部 schema 字段名。
- 完成内容：`interactive_init.py` 新增写入前成熟度预览；最终确认前渲染 preview；返回 scan 后刷新 weapon selection 和候选报告；maturity review / asset candidate prompt 增加真实 LLM 输出长度约束；repair loop 无 Runtime 证据源改为 `.ai/task-runs/`；README、init workflow、LLM contracts、North Star、spec/plan 和演进记录同步。
- 验证结果：targeted guided init happy path、guided init integration、LLM prompt unit、maturity model unit 和 RuoYi-Vue real self-improve acceptance 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：本轮固定了首次 `init` 的成熟度叙事契约。下一轮候选 gap：扫描阶段进度反馈、用户自然语言补充后的复述和影响说明、Guide / Sensor 推荐与具体成熟度维度的更精确关联。

## 2026-05-31 Workflow 推荐到 Routing Policy 生命周期

- North Star 模块：Workflow Runtime Specification、Experience & Self-Improve、Maturity & Evolution、Governance & Auditability、Benchmark / Review Intelligence。
- Gap Analysis 摘要：`recommend-workflow`、`improve`、`review-maturity`、`generate-asset-candidates`、`review-candidate` 和 `benchmark` 已具备分段能力，但缺少一条可验收的纵向闭环证明智能 workflow recommendation 能进入 review-only policy candidate、经治理应用为正式 routing policy，并被 maturity evidence 与 benchmark 识别。
- 用户故事：作为 Harness Maintainer，当我先为真实任务生成 review-only workflow recommendation，再运行自改进相关命令时，我可以得到结构化 `workflow_policy_patch` 候选，并通过显式 `review-candidate --decision applied` 应用到 `.ai/harness-config.yaml`，随后 benchmark 验证候选、治理记录和正式 routing policy 一致，从而确信智能推荐不会绕过人工治理，也不会停留在孤立报告。
- 当前代码 gap：asset candidates 写出后只刷新 Experience index，没有立即刷新 maturity evidence；CLI trace 没记录派生证据；asset candidate parser 只检查 `.ai/` 前缀；workflow policy applied 未要求 source review 为 support/revise；routing rule upsert 会把替换 rule 移到末尾；benchmark 对手工或旧版本落盘的非法 workflow policy target、路径穿越和未支持 review 的 applied governance 兜底不足。
- 关键决策 / 取舍：不新增命令；复用专家链路 `recommend-workflow -> improve -> review-maturity -> generate-asset-candidates -> review-candidate applied -> benchmark`。recommendation、maturity review 和 asset candidates 仍保持 review-only；只有 candidate governance 的 `applied` 决策能修改正式 `.ai/harness-config.yaml`。
- Assumptions / risks：真实 LLM 可能生成不同 routing patch，因此 parser、schema、candidate governance 和 benchmark 必须共同兜底；maturity evidence 刷新只表示候选进入证据面，不表示候选已应用。
- 边界情况 / 失败模式及回应：`defer` / `missing` 的 workflow policy 候选不能 applied；`.ai/../...` 路径穿越被 parser 与 benchmark 拒绝；workflow policy target 只能是 `.ai/harness-config.yaml`；替换已有 routing rule 原位替换，新增 rule 才追加；benchmark 会拒绝 applied 但 source review 未 support/revise 的手工治理状态。
- Sub agent 使用情况：使用 explorer 子代理只读审查当前 milestone 的 spec、plan、测试和 benchmark 兜底；它指出 benchmark 缺少 support/revise 与安全路径兜底，主线程补充了对应负向测试和实现。
- 价值切分说明：本轮不是单纯增加 parser 校验或测试，而是打通“智能推荐 -> 改进候选 -> LLM review -> 资产候选 -> 人工治理应用 -> benchmark 证明”的完整治理生命周期。
- 可执行验收标准及验证方式：integration 覆盖完整 CLI 链路、不创建 `.ai/task-runs`、asset candidate 后 maturity evidence 计数刷新、应用后 config 顺序保持、benchmark 三个相关 check 通过；unit 覆盖 parser 路径和 workflow target、defer/missing 不能 applied、rule 原位替换；benchmark integration 覆盖旧产物/手工产物的非法 path、target 和 review decision。
- 完成内容：`generate-asset-candidates` 刷新 maturity 派生证据并记录 trace；asset candidate parser 增加安全 `.ai/` 路径和 workflow target 校验；candidate governance 增加 support/revise applied 门禁和原位 upsert；benchmark 增加 workflow policy governance 兜底；README、LLM contracts、init workflow、sensor/gate rules、spec/plan 同步。
- 验证结果：targeted lifecycle / governance / benchmark tests 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：本轮新增稳定治理边界已沉淀到长期工程文档；未恢复 `run`，未引入 Runtime 执行。下一轮候选 gap：self-improve package consumption、existing Harness 主入口对 workflow policy lifecycle 的引导、更细的 acceptance efficiency matrix。

## 2026-05-31 Runtime 运行证据成熟度门禁

- North Star 模块：Maturity & Evolution、Experience & Self-Improve、Workflow Runtime Specification、Governance & Auditability。
- Gap Analysis 摘要：Runtime task-run 已能被 Builder 只读校验并进入 Experience / Maturity evidence，但 `maturity_model.py` 仍主要按命令和 workflow 文件判断 overall，`workflow` 维度在没有 resolved Runtime 证据时也可到 L3，`repair_loop` 固定 L0，导致成熟度语义和真实任务结果脱节。
- 用户故事：作为 Harness Maintainer，当宿主 Runtime 已写出合法 `.ai/task-runs/<task-id>/` 时，我可以运行 `assess` 看到成熟度基于真实 Sensor Report、Decision Log、Handoff Summary 和 repair attempts 更新，从而判断 Harness 是否真的进入 Workflow-bound L3。
- 当前代码 gap：`overall_level` 只看命令和 workflow 文件；`workflow` 维度不区分 runtime sensor passed / failed；`observability` 和 `governance_auditability` 只看 Builder generation trace；`repair_loop` 不消费 Runtime repair attempts。
- 关键决策 / 取舍：继续不恢复 `run`，不生成 Runtime 产物；只复用 `summarize_runtime_task_runs()` 的 schema-valid summary。全部 Runtime sensor resolved 才允许 workflow / overall 到 L3；failed / skipped / unresolved sensor 是成熟度 blocker，不是 Builder 结构校验失败。
- Assumptions / risks：单个 resolved task-run 只能证明已有一次 Workflow-bound 运行证据，不能证明 L4 自适应能力；L4 仍依赖多任务趋势、Experience 治理和策略优化。
- 边界情况 / 失败模式及回应：无 task-runs 不让 `assess` 失败，但保持 L2 ceiling；存在 bad task-run 时 Runtime loader 显式失败；存在 failed/skipped/unresolved sensor 时成熟度保守停在 L2 并列出 blocker。
- Sub agent 使用情况：使用三个 explorer 子代理并行做 North Star gap、代码/测试现状和验收效率调研；结论共同指出 L3/L4 语义、workflow policy lifecycle 和 acceptance efficiency 是高优先候选。本轮选取 Runtime maturity gate。
- 价值切分说明：本轮只做“运行证据影响成熟度”的纵向切片，不实现参考 Runtime、不做 L4 趋势分析、不改变 benchmark 结构校验。
- 可执行验收标准及验证方式：unit 覆盖 passed Runtime task-run 使 workflow / observability / governance / repair_loop 和 overall 提升；failed Runtime sensor 阻止 L3 并生成 blocker；maturity evidence 既有 Runtime 汇总测试保持通过。
- 完成内容：`maturity_model.py` 消费 Runtime summary；新增 runtime resolved 判定；更新 workflow、repair_loop、observability、governance、overall 和 blocking caps；README、init workflow、spec/plan 和演进记录同步。
- 验证结果：targeted maturity tests 已通过；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：长期 Runtime 分工和成熟度门禁规则已同步。下一轮候选 gap：workflow recommendation 到 policy lifecycle 端到端验收、self-improve package consumption、acceptance efficiency matrix、过程文档中文 gate。

## 2026-05-31 Runtime Task-Run 只读摄取

- North Star 模块：Experience & Self-Improve、Maturity & Evolution、Sensors、Governance & Auditability。
- Gap Analysis 摘要：North Star 要求真实任务记录、Sensor Report、Decision Log 和 Handoff Summary 进入 Experience / Maturity；当前 Builder 已删除 `run` 并保留 Runtime artifact contract，但只统计 `.ai/task-runs` 目录数量，benchmark 不校验存在的 Runtime 产物，experience summary 也只向 LLM 注入文件名列表。
- 用户故事：作为 Harness Maintainer，当外部 Runtime 已经在 `.ai/task-runs/<task-id>/` 写出过程产物时，我可以让 Builder 只读校验并汇总这些任务结果，从而让后续 self-improve 基于可审计的运行证据，而不是只基于候选文件计数。
- 当前代码 gap：`experience_index.py` 裸统计 task-run 目录；`maturity_evidence.py` 只记录 has_runtime_task_runs；`benchmark.py` 没有 optional runtime check；`summarize_experience.py` 只注入 task-run 文件名。
- 关键决策 / 取舍：不恢复 `run`，不生成 `.ai/task-runs`，不执行 Sensors；新增 Runtime schema / loader 只读校验外部产物。缺失 task-runs 仍为 optional passed；存在但 schema、task id、workflow 或 sensor status 不一致时 benchmark 失败。
- Assumptions / risks：第一版要求 `harness-map.yaml`、`sensor-report.yaml`、`runtime-summary.yaml`、`decision-log.md` 和 `handoff-summary.md`；未来宿主 Runtime 格式变化时通过 schema 版本演进处理。
- 边界情况 / 失败模式及回应：空缺 task-runs 不阻断；坏 YAML、缺 `runtime-summary.yaml`、failed/skipped sensor 没有 summary、runtime summary 与 sensor report 不一致都会显式失败；合法 failed sensor 被视为真实任务结果，不等同于 Runtime 产物校验失败。
- Sub agent 使用情况：使用 Hume 做 North Star gap 调研，建议 Runtime Task-Run Ingestion；使用 Epicurus 做测试覆盖审查，提出 E2E 和 self-improve 纵向验收后续 gap；两者均已关闭。
- 价值切分说明：本轮只补“外部 Runtime 数据进入 Harness Builder 证据面”的纵向能力，为后续成熟度真实晋级和 self-improve 经验闭环打基础，不直接改成熟度 overall 评分。
- 可执行验收标准及验证方式：unit 覆盖合法 / 缺失 / 不一致 Runtime task-run loader、Experience index、maturity evidence、experience summary source；integration 覆盖 benchmark absent / valid / invalid Runtime task-run。
- 完成内容：新增 `RuntimeSummary` / `RuntimeTaskRunSummary` schema 与 `runtime_task_runs.py`；Experience index 改为统计 schema-valid task-runs；maturity evidence 增加 Runtime sensor / repair 汇总；benchmark 新增 `content:runtime-task-run-artifacts`；experience summary 注入 sensor / handoff / decision 详情；README 和 engineering docs 同步。
- 全量回归修正：真实 DeepSeek 验收发现 maturity review 会引用 Builder 固定生成的 `.ai/guides/project-context.md` 和 Runtime 契约目录 `.ai/task-runs/`；已补精确 evidence allowlist，仍拒绝任意未知 `.ai/guides/**` 或 `.ai/task-runs/<task-id>/**` 路径。
- 验证结果：targeted regression `66 passed`；fast/full/push 结果见本轮提交记录。
- Self-Harness Gate：长期 Runtime 分工和 benchmark 规则已同步。下一轮候选 gap：E2E 产物契约深度、过程文档中文 gate、self-improve 包被 benchmark 全量消费、成熟度 L3/L4 真实晋级语义。

## 2026-05-31 Existing Harness Maintenance Triage

- North Star 模块：CLI Experience、Maturity & Evolution、Experience & Self-Improve、Benchmark / Review Intelligence。
- Gap Analysis 摘要：已有 Harness 维护入口已经展示成熟度、benchmark 和 Experience / review signals，但仍偏计数面板。Maintainer 需要自己理解 `pending_improvements`、`asset_candidates`、`workflow_recommendations`、`schema_content_failed_checks` 的优先级和命令顺序，才能决定下一步。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口时，我可以直接看到当前最该处理的 3 个维护动作、每个动作的原因、来源文件和对应菜单动作，从而不用从一组计数里自行推断下一步。
- 当前代码 gap：`interactive_init.py` 的 `_experience_status_lines()` 已分项展示信号，但没有形成 top action、reason、source 和 next action；状态摘要与菜单之间缺少动作路由层。
- 决策：新增只读 `maintenance_triage.py` helper，基于 `MaturityReport`、`BenchmarkReport` 和 `ExperienceIndex` 生成最多 3 个 `MaintenanceAction`；不新增持久化 `.ai` 产物和 schema。
- 决策：优先级为 maturity 缺失、benchmark 未运行、schema/content benchmark 失败、候选未治理、workflow recommendation 待转化、pending improvements 需要 self-improve package；没有待处理信号时建议 `recommend-workflow`。
- Assumptions / risks：`asset_candidate_count > candidate_governance_decision_count` 只是第一版 pending 近似；后续可按 candidate id 计算 unresolved。workflow recommendation 只代表待 review routing signal，不能解释为已应用 policy。
- 边界与失败模式：triage 不执行动作、不刷新 Experience index、不覆盖正式资产、不重新计算成熟度；schema 错误继续显式失败，不降级成 missing。
- Sub agent 使用：使用 explorer 子代理只读审计 existing-Harness 状态信号来源、Top 3 action 优先级、测试位置和是否需要新 schema；结论支持第一版只读 console triage，不新增 schema。
- 价值切分：本轮服务“回到已有 Harness 后知道下一步做什么”的用户价值，不是单纯增加字段或菜单项。
- 可执行验收标准及验证方式：unit 覆盖 benchmark/schema-content 优先于候选治理和 workflow recommendation、benchmark missing、no pending fallback；integration 覆盖 existing-Harness `init -> exit` 输出 Maintenance triage 且不覆盖正式资产。
- 完成内容：新增 `MaintenanceAction` triage helper；guided existing-Harness entry 在 Experience signals 后输出 Maintenance triage；README、init workflow、todo、spec/plan 和演进记录同步。
- 验证结果：RED targeted failed with missing `maintenance_triage` module；GREEN targeted unit + integration passed；fast regression 见提交前验证。
- Self-Harness Gate：本轮未新增机器产物契约；长期 init 工作流规则已同步。下一轮候选 gap：workflow recommendation 到 routing policy 的 guided 治理闭环、self-improve candidate lifecycle/maturity delta、或真实 acceptance 验证 LLM-guided evidence expansion。

## 2026-05-31 LLM-Guided Evidence Expansion

- North Star 模块：Scanner & Analyzer、Prompt Contract、Maturity & Evolution、智能化职责边界。
- Gap Analysis 摘要：当前扫描已经是 LLM-first，但 evidence 选择仍主要由确定性 bucket、排序和 source sample 上限决定。复杂遗留仓库中关键业务风险文件可能不在固定采样前几项，导致最终 scan proposal 仍受脚本采样偏差限制。
- 用户故事：作为遗留仓库的 Harness Maintainer，当仓库文件结构不规范、关键风险代码没有落在固定采样前几项时，我希望 Harness Builder 先让 LLM 基于初始 evidence 规划需要深入读取的补充文件，再生成最终 scan proposal，从而让模块、风险区和验证建议更贴近真实代码。
- 当前代码 gap：`scan_repository()` 直接执行 `collect_evidence -> analyze_evidence_with_llm -> reconcile_scan`；`EvidenceBundle.files` 虽有完整轻量文件索引，但模型不能先选择补充读取文件。
- 决策：新增 `llm-evidence-plan-v1` 机器 prompt、`LLMEvidencePlan` schema 和 `llm_evidence_planner.py`；planner 只输出路径计划，不生成最终扫描结论。
- 决策：Python 按 allowlist 校验 requested paths，只允许来自 `EvidenceBundle.files` 的仓库内文件；非法、未知、`.ai/` 或仓库外路径显式失败，不能 fallback 成固定采样成功。
- 决策：真实无 caller 扫描路径默认执行 planner；现有 mock `llm_caller` 测试保持只注入最终 scan，显式 `evidence_planner_caller` 才测试两阶段链路。
- Assumptions / risks：多一次真实 LLM 调用会增加 acceptance 成本，但这是提升扫描智能化的核心投入；本轮最多请求 8 个文件，避免 prompt 体积失控。
- 边界与失败模式：不改变最终 `LLMScanProposal` schema，不让 LLM 直接读写文件，不恢复旧 scanner 包，不跳过 reconcile stack conflict 校验。
- Sub agent 使用：使用两个只读 explorer 子代理并行做整体 gap 和 Prompt/LLM 智能化调研；其中 Prompt/LLM 调研明确推荐 LLM-guided evidence expansion 作为最直接回应“确定性脚本太多”的下一 milestone。
- 价值切分：本轮不是单纯新增 prompt 或字段，而是让扫描从“固定采样后 LLM 判断”推进到“LLM 参与选择补充证据”的纵向智能化能力。
- 可执行验收标准及验证方式：unit 覆盖 planner JSON/schema/path allowlist 失败、被固定 source sampling 跳过的文件可进入 `llm_requested_files`、scan_repository 两阶段调用、prompt registry 自动发现资产清单。
- 完成内容：新增 evidence planner prompt / schema / tool；`EvidenceBundle` 增加 `llm_requested_files`；collector 支持 allowlisted expansion；scan_repository 接入两阶段规划；prompt asset 测试移除第二份静态清单；LLM contracts、architecture、scanner todo、spec/plan 同步。
- 验证结果：RED targeted unit failed with missing expansion implementation；GREEN targeted unit 13 passed；fast regression 见提交前验证。
- Self-Harness Gate：长期 LLM / 架构规则已同步；未新增正式 `.ai` 产物契约。本轮未跑真实 DeepSeek acceptance，后续候选 gap 包括真实仓库 acceptance 验证两阶段扫描效果、maintenance triage queue、workflow recommendation 到 routing policy 的治理闭环。

## 2026-05-31 First Init Benchmark Readiness

- North Star 模块：CLI Experience、Benchmark / Review Intelligence、Maturity & Evolution。
- Gap Analysis 摘要：首次 `init` 已生成成熟度摘要和下一步入口，但没有解释 benchmark 是否已运行、质量门禁状态是否已证明通过，以及下一步如何触发验收。已有 Harness 维护入口能显示 benchmark 状态，首次 0->1 用户仍可能把“资产生成成功”误解为“benchmark passed”。
- 用户故事：作为第一次为仓库建立 Harness 的 Harness Maintainer，当 `init` 完成第一版 `.ai` 资产生成后，我可以直接看到 benchmark 健康度目前是未运行、为什么不默认运行、应该用哪个入口完成首次质量验收，以及验收会检查哪些方面，从而知道第一版 Harness 还没有被质量门禁证明通过。
- 当前代码 gap：`init-summary.md` 只有成熟度、阻断项、下一步和 Runtime 边界；CLI completion message 只列成熟度、阻断项、下一步和入口文件；两者都不读取或解释 `.ai/benchmark-report.yaml`。
- 决策：首次 `init` 不默认运行 benchmark，只展示 benchmark readiness 和 next command，保持首次初始化反馈快速且不引入额外质量门禁写入；已有 benchmark report 时通过 `BenchmarkReport` schema 展示 status、quality status 和 failed check count。
- 决策：把 `## Benchmark 健康度` 纳入 `init-summary.md` 稳定章节，并让 benchmark 自身检查该章节和 `benchmark_status=` / `quality_status=`，防止后续摘要退化。
- Assumptions / risks：当前 POC 更适合显式 benchmark；未来可增加“初始化后立即运行 benchmark”的可选动作。本轮只解释 readiness，不改变真实验收边界。
- 边界与失败模式：不调用 `run_benchmark()`，不生成 `.ai/benchmark-report.yaml`，不改变 standalone / existing-Harness guided `benchmark` 行为；已有 benchmark report schema 错误时显式失败。
- Sub agent 使用：使用 explorer 子代理只读审查首次 init benchmark readiness 的边界、是否默认运行 benchmark、验收测试和长期文档影响；结论支持先做 readiness，不默认执行 benchmark。
- 价值切分：本轮服务首次用户“知道 Harness 尚未验收”的独立价值，不是内部字段或测试补丁。
- 可执行验收标准及验证方式：integration 覆盖首次 init Markdown 和 CLI 输出包含 benchmark readiness / next command，并确认不创建 `.ai/benchmark-report.yaml`；unit 覆盖已有 benchmark report 时 readiness 通过 schema 展示 failed checks；benchmark 内容检查覆盖 `## Benchmark 健康度`。
- 完成内容：`init_summary.py` 新增 benchmark readiness helper；`init-summary.md` 和 completion message 输出 readiness；benchmark 检查、README、init workflow、testing strategy、sensor/gate rules、strategy、todo、spec/plan 和演进记录同步。
- 验证结果：RED targeted integration failed；GREEN targeted integration + unit passed；fast regression 见提交前验证。
- Self-Harness Gate：长期规则已同步到 strategy / engineering / todo；无新增机器契约。下一轮候选 gap：更完整的候选列表浏览 / 编号选择；可选立即运行 benchmark 的 guided 交互；或拆分 `interactive_init.py` 维护入口降低后续迭代成本。

## 2026-05-31 Guided Candidate Apply Preview

- North Star 模块：CLI Experience、Experience & Self-Improve、Maturity & Evolution、Governance & Auditability。
- Gap Analysis 摘要：已有 Harness 维护入口已支持 `review-candidate` 并允许单个 Guide / Sensor 候选 `applied`，但 Maintainer 在输入决策前只能看到候选字段，看不到正式资产写入影响、重复 marker 状态或即将追加的内容 diff。open todo 仍要求补 guided apply 前 diff / summary。
- 用户故事：作为 Harness Maintainer，当我在已有 Harness 的 guided `init -> review-candidate` 中审查一个 Guide / Sensor 候选并可能选择 `applied` 时，我可以在输入决策前看到它会写入哪个正式资产、采用什么应用方式、是否已有重复 marker，以及将追加的内容 diff 摘要，从而避免盲目把 review-only 候选固化进正式 Harness。
- 当前代码 gap：`_asset_candidate_detail()` 展示 id、kind、target、risk、evidence 和 acceptance checks；`review_candidate()` 底层已有 marker 防重和路径边界，但这些信息没有在用户决策前暴露。
- 决策：新增 CLI-only `_asset_candidate_apply_preview()`，只读目标文件状态并生成 unified append diff 片段；实际写入、重复应用阻断和 governance 仍由 `review_candidate()` 负责。
- 决策：不新增二次确认；当前 guided 流程已经要求用户显式输入 `applied`，本轮只把 summary / diff 放到 decision prompt 前。workflow policy 继续显示 expert-command preview 并拒绝 guided apply。
- Assumptions / risks：diff 片段覆盖 marker、heading、rationale 和 candidate draft 关键新增行，足以支持第一步审查；完整候选浏览器和结构化 workflow policy diff 仍留给后续。
- 边界与失败模式：不新增 LLM / prompt / schema，不批量 apply，不应用 workflow policy，不创建 `.ai/task-runs`。重复 marker 预览为 `present`，实际 `applied` 仍显式失败并不写 governance。
- Sub agent 使用：使用 explorer 子代理只读审计 review-candidate apply 支持、风险边界和验收建议；主线程采纳 summary + diff 方向，但暂缓二次确认和完整候选浏览器以保持切片小而可验收。
- 价值切分：本轮保护“正式应用候选前的用户审查决策”，不是单纯增加字段，也不是做泛化 UI。
- 可执行验收标准及验证方式：integration 覆盖 Guide candidate apply 前输出 target/mode/target_exists/duplicate_marker/block heading/source report/unified append diff；integration 覆盖 duplicate marker preview 后 applied 显式失败且不写 governance；integration 覆盖 workflow policy preview 显示 expert command required 且仍拒绝 guided apply。
- 完成内容：新增 apply preview helper；guided `review-candidate` 在 decision prompt 前输出 preview；底层治理失败在 guided CLI 中显式记录 trace 并作为 `BadParameter` 暴露；README、init workflow、todo、spec/plan 和演进记录同步。
- 验证结果：RED targeted integration 3 failed；GREEN targeted integration 3 passed；fast regression 见提交前验证。
- Self-Harness Gate：本轮无新增机器契约；长期 init workflow 边界已更新。下一轮候选 gap：更完整的候选列表浏览 / 编号选择；首次 `init` 后 benchmark 健康度解释与下一步治理节奏；或拆分 `interactive_init.py` 维护入口降低后续迭代成本。

## 2026-05-31 Existing Harness Workflow History Status

- North Star 模块：CLI Experience、Workflow Runtime Specification、Experience & Self-Improve、Maturity & Evolution。
- Gap Analysis 摘要：open todo 只剩“成熟度驱动的 init 主向导与命令信息架构重构”；当前 `recommend-workflow` 已保留历史并让 Experience / Maturity 统计多次 recommendation，但已有 Harness 维护入口仍只展示 `workflow_recommendations=<count>`，Maintainer 无法直接看到最近一个待审核 routing signal。Prompt 集中管理经代码、测试和工程文档检查已基本落地，本轮不再重复处理。
- 用户故事：作为 Harness Maintainer，当我再次运行 guided `init` 查看已有 Harness 状态时，我可以直接看到 workflow recommendation 历史中的最新任务、推荐 workflow、风险和待审核状态，从而判断是否需要进入 `improve` 或 `review-candidate` 处理 routing policy gap。
- 当前代码 gap：`interactive_init.py` 的 Experience / review signals 只显示 workflow recommendation count；guided `recommend-workflow` 已写 history artifacts，但输出和 trace artifacts 仍只列 latest recommendation 文件。
- 决策：新增 `_workflow_recommendation_status_lines()`，优先消费 `.ai/review/workflow-routing-recommendations/index.yaml` 的 `WorkflowRecommendationHistory`，没有 history 时兼容 `.ai/review/workflow-routing-recommendation.yaml` 的 `WorkflowRecommendationReport`；schema 无效时显式失败，不伪装成 missing。
- 决策：guided `recommend-workflow` 输出和 trace 同步记录 latest compatibility files、history index、history summary、Experience index 和 maturity evidence，让主向导状态与 standalone 命令产物保持一致。
- Assumptions / risks：一行 latest signal 足以支撑第一步维护入口判断；完整历史浏览、候选 diff / summary 和 workflow policy guided apply 留给后续小切片。旧 latest 与新 history 同时存在时优先信任 history index。
- 边界与失败模式：不执行 Runtime，不创建 `.ai/task-runs`，不修改正式 routing policy，不改变 LLM router prompt/parser，不改变 Experience / Maturity 计数模型；history schema 或 latest schema 错误直接失败。
- Sub agent 使用：使用 explorer 子代理只读审计 open todos、North Star 候选 gap 和 Prompt 集中管理现状；结论支持先收口当前 workflow history status WIP，并确认它属于 maturity-driven init 主向导价值链。
- 价值切分：本轮不是单纯增加字段或测试，而是把已存在的机器历史计数转成 Maintainer 在主入口可审查、可接管的最新 routing signal。
- 可执行验收标准及验证方式：integration 覆盖 history index 有两条 recommendation 时 `init -> exit` 展示 count/latest id/task/workflow/risk/status/source；integration 覆盖 legacy latest 无 history 时仍展示 task/workflow/risk/status/source；integration 覆盖 guided `recommend-workflow` 输出和 trace artifacts 包含 history index / summary，且不创建 `.ai/task-runs`、不覆盖正式资产。
- 完成内容：新增 existing-Harness latest workflow recommendation 状态 helper；guided `recommend-workflow` trace/output 补 history artifacts；README、init workflow、spec/plan 和演进记录同步。
- 验证结果：RED targeted integration 3 failed；GREEN targeted integration 3 passed；fast regression 见提交前验证。
- Self-Harness Gate：本轮更新了长期 init workflow 边界和 README；无需新增 schema 或 benchmark，因为 history schema / benchmark 已在上一轮完成。下一轮候选 gap：guided candidate governance 的候选浏览与 apply 前摘要/diff；首次 `init` 后 benchmark 健康度解释与下一步治理节奏；或 `interactive_init.py` 维护入口拆分以降低后续迭代成本。

## 2026-05-31 Test Loop Slices

- North Star 模块：Benchmark / Review Intelligence、Maturity-driven Evolution、工程验证体系。
- Gap Analysis 摘要：目标模式连续小步演进依赖快速且可信的验证反馈；当前只有 `scripts/test-fast.sh` / `test-full.sh` / `test-acceptance.sh` 三层入口，开发中常要手写 pytest target，commit hook 还可能重复运行刚刚通过的 fast regression。当前工作树已有脚本切片草稿，但缺少测试、文档和 stamp 安全边界。
- 工程信任故事：作为 Harness Builder 维护者或目标模式 Codex，当我在一轮小功能中只修改某类能力时，我可以运行命名清晰的测试切片，并让 pre-commit 复用刚刚通过的 fast regression，从而缩短反馈循环，同时不削弱 push 前 full / acceptance 验收边界。
- 当前代码 gap：`scripts/test-fast.sh` 无 stamp 缓存；没有 unit / integration / guided-init / LLM-contract / acceptance 常用切片入口；脚本行为缺少测试；原草稿把 stamp 写入 `.git`，在 Codex sandbox 中会导致测试已通过但脚本失败。
- 决策：新增共享 `scripts/lib-test-env.sh` 和常用切片脚本；fast stamp 只在完整 fast 通过后写入 `.pytest_cache/harness-builder-test-fast.stamp`，pre-commit 只在指纹匹配时跳过重复 fast。
- 决策：切片脚本只服务开发反馈，不替代 `scripts/test-fast.sh`、`scripts/test-full.sh` 或真实 acceptance；Codex 创建 commit 前仍必须主动运行 fast。
- Assumptions / risks：`.pytest_cache/` 已被 ignore，适合放本地验证缓存；指纹覆盖 HEAD、tracked/staged/untracked 非 ignored 文件，但不覆盖虚拟环境、外部服务或 ignored 文件，因此只表示当前工作树 fast regression 通过。
- 边界与失败模式：pytest 失败不写 stamp；targeted fast 不写 whole-tree stamp；stamp 损坏或指纹缺失时不跳过；acceptance 缺 key / 缺真实仓库仍显式失败。
- Sub agent 使用：使用 explorer 子代理只读审计未提交脚本改动、规则一致性、测试缺口和风险，结论要求补脚本测试、文档和 `.git` stamp 风险修正。
- 价值切分：本轮只优化测试循环入口与 pre-commit 去重，不改变测试覆盖范围、不改变 acceptance 是否进入 CI，也不调整产品功能。
- 可执行验收标准及验证方式：unit 覆盖脚本 bash 语法、README 切片文档、`.pytest_cache` stamp、stamp 匹配/失配和切片脚本选项；shell targeted checks 覆盖 unit/integration/guided-init/LLM-contract 脚本；fast regression 覆盖全量默认快速测试。
- 完成内容：新增测试切片脚本和共享 helper；`test-fast.sh` 支持 target passthrough 和 safe stamp；pre-commit 支持 stamp 命中跳过；README、testing strategy、todo、spec/plan 和演进记录同步。
- 验证结果：targeted regression 见本轮验证；fast regression 见提交前验证。
- Self-Harness Gate：测试脚本行为已纳入 unit 测试，长期规则已沉淀到 README 和 testing strategy。下一轮候选 gap：existing-Harness 状态展示 latest recommendation id、guided apply 前 diff/summary，或 benchmark/interactive init 大文件拆分。

## 2026-05-31 Workflow Recommendation History

- North Star 模块：Workflow Runtime Specification、Experience & Self-Improve、Maturity & Evolution、Benchmark / Review Intelligence。
- Gap Analysis 摘要：`recommend-workflow` 已能生成 review-only 最新推荐并刷新 Experience / Maturity，但每次都会覆盖 `.ai/review/workflow-routing-recommendation.*`；Maintainer 无法审计多次任务路由判断，Experience 也只能把推荐计数为 1，难以识别重复 routing gap。
- 用户故事：作为 Harness Maintainer，当我在已有 Harness 上为多个真实任务运行 `recommend-workflow` 时，我可以保留每一次 review-only workflow recommendation 的独立记录和索引，从而审计任务路由判断的演进，并让 Experience / Maturity 能识别重复 routing gap。
- 当前代码 gap：`recommend_workflow()` 只写 latest 文件；`experience_index` 只读取单个 latest YAML；benchmark 只校验单份 workflow recommendation pair。
- 决策：保留 latest 文件作为兼容出口，同时新增 `.ai/review/workflow-routing-recommendations/<recommendation_id>.*`、`index.yaml` 和摘要 Markdown。Experience index 优先读取 history index，没有 history 时再兼容 legacy latest。
- 决策：history 是确定性审计层；LLM 仍只输出单次 `WorkflowRecommendationReport`，Python 负责 history id、schema、索引、Markdown 摘要和 benchmark 校验。
- Assumptions / risks：保留 latest 是最低风险兼容策略；history 目录增加 review 复杂度，因此用机器 index 和稳定 summary 控制可读性。history 缺失条目或 Markdown 章节时 benchmark 必须失败。
- 边界与失败模式：不实现 Runtime execution history，不创建 `.ai/task-runs`，不应用 routing policy，不改变 LLM router prompt/parser；history index schema 无效或条目 YAML/Markdown 不配对时显式失败。
- Sub agent 使用：使用 explorer 子代理只读调研 integration / benchmark 既有测试模式和 helper 位置；主线程并行完成 RED 测试、实现、文档和验证。
- 价值切分：本轮完整覆盖“多任务 workflow recommendation 可审计历史”这一用户故事；不拆成单纯 schema、字段或文件改动，也暂缓 UI 历史浏览、diff 和 Runtime 任务轨迹。
- 可执行验收标准及验证方式：unit 覆盖 `WorkflowRecommendationHistory` schema 和 Experience history 计数；integration 覆盖两次 CLI recommendation 后 history 有两条、latest 指向第二条、Experience/Maturity 计数为 2、trace 记录 history artifact 且不生成 `.ai/task-runs`；benchmark integration 覆盖 history 缺 Markdown 时失败；README 和 engineering docs 同步。
- 完成内容：新增 workflow recommendation history schema；`recommend-workflow` 写入历史条目、index 和 summary；Experience / Maturity 消费 history count；benchmark 校验可选 history artifacts；README、architecture、init workflow、sensor/gate rules、spec/plan 同步。
- 验证结果：targeted regression 见本轮验证；fast regression 见提交前验证。
- Self-Harness Gate：本轮新增稳定 `.ai/review/workflow-routing-recommendations/` 机器契约，已纳入 schema、integration、benchmark 和长期工程文档。下一轮候选 gap：guided apply 前 diff/summary、测试脚本分层与 fast/full 耗时优化、或 existing-Harness 状态中展示 latest recommendation id。

## 2026-05-31 Guided Candidate Apply

- North Star 模块：CLI Experience、Experience & Self-Improve、Maturity & Evolution、Governance & Auditability。
- Gap Analysis 摘要：已有 Harness 维护入口已支持 `improve`、`self-improve`、`recommend-workflow` 和候选治理；standalone `review-candidate` 已能安全应用 Guide / Sensor Markdown 和结构化 workflow policy patch。但 guided `init` 只能记录 `accepted` / `deferred` / `rejected`，Maintainer 仍需离开主入口使用专家命令才能正式接管低风险 Guide / Sensor 候选。
- 用户故事：作为 Harness Maintainer，当我在已有 Harness 上再次运行 guided `init` 并查看 self-improve 生成的 Guide / Sensor 候选时，我可以审查单个候选的目标路径、证据、风险和验收检查，并明确选择 `applied` 将它写入正式 Markdown，从而完成一条可审计的自改进接管闭环。
- 当前代码 gap：`interactive_init.py` 对所有 `applied` 决策一律失败；候选详情只展示列表摘要，没有在决策前展示 evidence sources、acceptance checks 和 apply boundary。
- 决策：guided 入口复用现有 `review_candidate()`，只放开 Guide / Sensor 单候选 `applied`；workflow policy 在 guided 入口继续失败并提示专家命令，因为它涉及 `.ai/harness-config.yaml` 结构化 patch 审核。
- Assumptions / risks：Guide / Sensor Markdown 追加式应用是当前最低风险的正式接管动作；错误经验固化仍有风险，因此本轮保持单候选、显式 id、rationale 必填、候选详情展示和底层路径校验。
- 边界与失败模式：不批量应用，不开放 guided workflow policy apply，不从自由文本推断配置变更，不执行 Runtime，不创建 `.ai/task-runs`。未知 candidate id、空 rationale、非 `.ai/` suggested path 和重复 applied 继续显式失败。
- Sub agent 使用：使用 explorer 子代理审计 existing-Harness 候选治理闭环，结论建议优先补 guided 单候选安全采纳；另两个 explorer 并行审计 workflow recommendation history 和测试效率脚本，作为后续候选 gap。
- 价值切分：本轮只补 Guide / Sensor 候选的 guided apply 接管闭环；暂缓 workflow recommendation history、guided apply diff/summary、workflow policy guided apply 和测试脚本分层。
- 可执行验收标准及验证方式：integration 覆盖 guided `init -> review-candidate -> applied` 成功追加 Guide candidate marker、记录 governance `applied_paths`、刷新 Experience index、trace artifacts、不重新扫描、不创建 `.ai/task-runs`、不覆盖其他正式资产；integration 覆盖 guided workflow policy `applied` 显式失败且不写 governance。
- 完成内容：guided `review-candidate` 展示候选详情并允许 Guide / Sensor `applied`；candidate governance summary 输出真实 applied path count；README、init workflow 规则、maturity-driven init todo 和演进记录同步更新。
- 验证结果：targeted regression 9 passed；fast regression 见本轮提交前验证。
- Self-Harness Gate：本轮只改变 `init` 维护入口和候选治理文档；不需要新增 schema。下一轮候选 gap：workflow recommendation history、guided apply 前 diff/summary、测试脚本分层与 acceptance 分组。

## 2026-05-31 LLM Evidence Source Whitelist Hardening

- North Star 模块：Benchmark / Review Intelligence、Experience & Self-Improve、Prompt Contract、Maturity & Evolution。
- Gap Analysis 摘要：North Star 要求自改进产物可审计、可追溯；当前 workflow recommendation、maturity review、asset candidates 和 benchmark 已拒绝 `.ai/` 外路径，但仍允许未知 `.ai/` 路径伪装成 evidence source。experience summary parser 已有类似白名单校验，说明该约束应提升为跨 LLM review-only 产物的统一契约。
- 工程信任故事：作为 Harness Maintainer，当我审阅 LLM 生成的 recommendation / review / candidate / experience summary 时，我可以相信每个 `evidence_sources` 都来自 Builder 提供或上游结构化产物中的证据，从而避免无法追溯的智能建议进入自改进闭环。
- 当前代码 gap：`llm_workflow_router.py` 只校验 `.ai/` 前缀；`llm_maturity_reviewer.py` 和 `llm_asset_candidate_generator.py` 未校验 evidence source；benchmark 对可选 review artifact 也只检查前缀，没有验证来源是否在 allowlist 中。
- 决策：新增共享 `tools/evidence_sources.py`，由 LLM 编排函数基于 `MaturityEvidencePack`、`ImprovementCandidateReport`、`MaturityReviewReport` 和 `ExperienceSummaryReport` 构建 allowlist；parser 必须显式接收 allowlist。Benchmark 从落盘 schema artifact 构建 allowlist，不使用任意 `.ai/**` glob。
- Assumptions / risks：核心成熟度输入、experience index source 和上游候选 evidence source 是可引用证据；空 `evidence_sources` 暂不 hard fail，本轮只拒绝明确伪造或未知的路径。真实 LLM 可能因引用未提供路径而更早失败，这是期望的 no silent fallback 行为。
- 边界与失败模式：非 `.ai/` evidence source 继续以 `evidence_source_outside_ai` 失败；未知 `.ai/` evidence source 以 `unknown_evidence_source` 失败；allowlist 依赖的上游 schema 无效时 benchmark 记录 `invalid_evidence_allowlist_source:*`，不静默放行。
- Sub agent 使用：使用两个只读 explorer 子代理并行审计 LLM parser 和 benchmark 的 evidence source 缺口；主线程整合后选择本轮 hardening milestone，并负责测试、实现、文档和验证。
- 价值切分：本轮只做 evidence source 可追溯性 hardening；暂缓 recommendation history、guided apply diff/summary、candidate UX 和 acceptance 测试耗时优化。
- 可执行验收标准及验证方式：unit 覆盖 workflow recommendation、maturity review、asset candidate parser 拒绝未知 `.ai/` evidence source；benchmark integration 覆盖四类落盘 review-only artifact 引用未知 source 时失败；工程文档和 todo/archive 同步。
- 完成内容：新增 evidence source allowlist helper；接入三个 LLM parser 和 benchmark 四类可选 review artifact；归档 todo，更新 LLM contract、sensor/gate rules、spec/plan 和演进记录。
- 验证结果：targeted regression `75 passed`；fast regression 见本轮提交前验证。
- Self-Harness Gate：长期规则已沉淀到 `docs/engineering/llm-contracts.md` 和 `docs/engineering/sensor-and-gate-rules.md`；todo 已归档；未新增正式 `.ai` 产物契约。下一轮候选 gap：existing-Harness guided apply 前 diff/summary、workflow recommendation history、或把 full/acceptance 测试拆成更细的目标模式验证脚本。

## 2026-05-31 Goal Mode Retrospective Hardening

- North Star 模块：CLI Experience、Prompt Contract、Benchmark / Review Intelligence、Experience & Self-Improve。
- Gap Analysis 摘要：用户指出前几轮目标提示词不完整后，本轮用主线程和只读子代理回顾最近 13 个本地提交。结论是功能方向没有明显偏离北极星，但存在审计轨迹与契约硬度缺口：existing-Harness 状态摘要过粗、workflow recommendation LLM 缺字段可被 schema 默认值掩盖、maturity review 缺 review-only 状态与 Markdown 边界、formal asset snapshot 覆盖不完整，以及 todo / README 的少量陈旧描述。
- 当前代码 gap：`interactive_init.py` 只输出 Experience 总数；`llm_workflow_router.py` 和 `llm_maturity_reviewer.py` 未要求模型显式返回所有顶层契约字段；`MaturityReviewReport` 没有 `review_status`；benchmark 未要求 maturity review Markdown 的 `## Review Boundary`；guided 维护测试未 snapshot architecture guide 与 task templates。
- 决策：本轮做 hardening 小切片，不改变正式资产应用语义，不实现 guided apply，不恢复 Runtime / `run`。把 evidence source 白名单作为独立 high-priority todo，避免混入过大的跨 LLM 工具改造。
- Assumptions / risks：显式字段校验可能让真实 LLM 更早失败，这是期望行为；prompt 已同步给出完整模板。状态摘要只读，不刷新 index、不跑 benchmark、不写文件，保持 `exit` 路径不覆盖资产。
- 边界与失败模式：缺失 `experience-index.yaml`、`benchmark-report.yaml`、`self-improve-package.yaml` 等状态文件时显示 missing / not_available；schema 无效继续显式失败，不静默降级。
- Sub agent 使用：启动两个只读 explorer 子代理分别审计文档/spec/plan/evolution 记录和 guided init/self-improve 代码契约；另一个既有 explorer 审计 existing-Harness 状态摘要字段。主线程综合结果后选择本轮修复切片。
- 价值切分：修复 parser / prompt / benchmark / CLI 状态摘要 / 测试盲区 / 文档一致性；暂缓 evidence source whitelist、guided apply diff 和 recommendation history。
- 验收方式：unit 覆盖 LLM 显式 `review_status` 缺失失败；integration 覆盖 maturity review review-only 边界、benchmark 缺边界失败、existing-Harness 分项状态摘要，以及 guided actions formal asset snapshot。
- 验证结果：targeted regression 62 passed；fast regression 见本轮提交前验证。
- Self-Harness Gate：README、init workflow、LLM contracts、guided init todo、follow-up todo、spec、plan 和演进记录已同步；下一轮候选 gap 首选 evidence source whitelist hardening，其次是 existing-Harness guided apply 前 diff / summary 或 recommendation history。

## 2026-05-31 Existing Harness Self-Improve Action

- North Star 模块：CLI Experience、Experience & Self-Improve、Maturity & Evolution。
- Gap Analysis 摘要：已有 Harness 维护入口已支持复评、改进候选、benchmark、workflow recommendation 和候选治理记录，但智能自改进包仍只能通过 standalone `self-improve` 触发。guided apply 和 recommendation history 也有价值，但会引入正式资产变更或新存储模型。
- 当前代码 gap：`interactive_init.py` 没有 self-improve 动作，Maintainer 需要记住专家命令才能触发 LLM maturity review 和 asset candidates。
- 决策：新增 guided `self-improve` 动作，复用 `run_self_improve()`，生成 maturity review、asset candidates 和 self-improve package，并在 init trace 中记录 candidate counts。
- 决策：该动作必须是显式用户选择；首次 `init` 仍不默认执行 self-improve。
- Assumptions / risks：真实 DeepSeek 可能耗时或失败；失败必须显式暴露，不 fallback。用户可能误解为自动应用 Harness，因此输出和文档强调 review-only、applied_paths=0、无 Runtime。
- 边界与失败模式：不重新扫描；不覆盖正式 Guides、Sensors、Workflow Skills、配置、inventory 或扫描产物；不执行 Runtime；不创建 `.ai/task-runs`；不应用 asset candidates。
- Sub agent 使用：启动 explorer 子代理审计 guided self-improve 的适配性、边界、测试和风险；主线程并行完成 RED 测试与实现。
- 价值切分：本轮只把既有 self-improve 能力接入主向导，不修改 prompt、schema、acceptance 或 candidate apply。
- 验收方式：integration mock LLM 覆盖 guided action，断言 SelfImprovePackageManifest schema、Benchmark self-improve package check、trace artifacts、不扫描和正式资产未变。
- 验证结果：targeted integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：README、init workflow、todo 和演进记录已同步；下一轮候选 gap 包括 guided apply diff/summary、candidate list UX 增强、recommendation history 或拆分过大的 `interactive_init.py`。

## 2026-05-31 Existing Harness Candidate Governance Action

- North Star 模块：CLI Experience、Experience & Self-Improve、Maturity & Evolution。
- Gap Analysis 摘要：已有 Harness 维护入口已经支持复评、改进候选、benchmark 和 workflow recommendation，但“处理待确认候选”仍只能通过 standalone `review-candidate`。guided self-improve 和 recommendation history 也有价值，但候选治理更直接补齐接管闭环。
- 当前代码 gap：`interactive_init.py` 没有候选治理入口；Maintainer 必须记住 candidate id、decision、rationale 等专家命令参数。
- 决策：新增 guided `review-candidate` 动作，第一版只支持 `accepted`、`deferred`、`rejected`，复用 `review_candidate()` 写 `.ai/review/candidate-governance.*` 并刷新 Experience index。
- 决策：guided 模式显式拒绝 `applied`；正式资产应用仍留给 standalone 专家命令，因为 apply 会修改 Guides、Sensors 或 `.ai/harness-config.yaml`，需要更完整的 diff / summary UX。
- Assumptions / risks：非 applied 决策足以形成第一步可审计治理闭环；用户可能误以为 accepted 会自动应用，因此菜单、文档和输出都强调 applied_paths=0。
- 边界与失败模式：不重新扫描；不调用 LLM；不执行 Runtime；不创建 `.ai/task-runs`；不覆盖正式 Harness 资产；缺少 asset-candidates、未知 candidate id、空 rationale 或非法 decision 必须显式失败。
- Sub agent 使用：启动 explorer 子代理审计 guided candidate governance 的可行性、是否应排除 applied、风险和验收标准；主线程并行完成 RED 测试和实现。
- 价值切分：本轮只记录治理决策，不实现候选列表浏览、编号选择或 guided apply。
- 验收方式：integration 准备 review-only asset candidate，走 guided `init` 记录 accepted 决策，断言 CandidateGovernanceLog schema、Experience index、trace artifacts、不扫描和正式资产未变。
- 验证结果：targeted integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：README、init workflow、todo 和演进记录已同步；下一轮候选 gap 包括 guided self-improve 入口、候选列表浏览 UX、guided apply 的 diff/summary 设计或 recommendation history，仍以下轮 Current State Gap Analysis 为准。

## 2026-05-31 Existing Harness Recommend Workflow Action

- North Star 模块：CLI Experience、Workflow Runtime Specification、Experience & Self-Improve。
- Gap Analysis 摘要：standalone `recommend-workflow` 已具备 LLM 结构化推荐、schema 校验、review-only artifact、Experience/Maturity 刷新和 benchmark 检查，但普通用户仍需记住专家命令及参数。candidate governance 菜单价值也高，但会涉及正式资产 apply 边界，复杂度更高。
- 当前代码 gap：已有 Harness 维护入口支持 `exit` / `assess` / `improve` / `benchmark` / `reinit`，没有从主向导输入 task brief 生成 workflow recommendation 的入口。
- 决策：新增 guided `recommend-workflow` 动作，收集任务说明和 task id，复用 `recommend_workflow()` 生成 `.ai/review/workflow-routing-recommendation.*`，再刷新 Experience / Maturity 派生证据。
- 决策：推荐产物是单份“最新推荐”review-only 文件；本轮不扩展历史存储模型，不生成多任务 recommendation registry。
- Assumptions / risks：任务说明不能为空；真实 LLM 缺 key、非法 JSON、schema 错误或引用未知 workflow/rule 时显式失败，不 fallback。推荐结果不能被解释为已执行或已应用 routing policy。
- 边界与失败模式：不重新扫描；不覆盖正式 Guides、Sensors、Workflow Skills、配置、inventory 或扫描产物；不创建 `.ai/task-runs`；不执行 Sensors；不修改业务代码。
- Sub agent 使用：使用 explorer 子代理只读审计 guided `recommend-workflow` 的适配性、交互输入、review-only 边界、测试与风险；结论支持作为下一小 milestone，并提醒单份推荐会刷新最新产物。
- 价值切分：本轮只补主向导入口；候选治理菜单、recommendation 历史记录和 guided self-improve 保留后续。
- 验收方式：integration mock LLM 覆盖 guided action，断言 schema、Markdown review boundary、Experience/Maturity 计数、benchmark 可验收、不扫描、不覆盖正式资产和 trace summary。
- 验证结果：targeted integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：README、init workflow、todo 和演进记录已同步；下一轮候选 gap 首选 existing-Harness candidate governance 菜单或 guided self-improve 入口，具体仍以下轮 Current State Gap Analysis 为准。

## 2026-05-31 Existing Harness Benchmark Action

- North Star 模块：CLI Experience、Benchmark / Review Intelligence、Maturity & Evolution。
- Gap Analysis 摘要：再次执行 `init` 已能展示最近 benchmark 状态，并支持 `exit` / `assess` / `improve`，但用户仍需记住 standalone `benchmark` 命令才能刷新质量门禁；这与 North Star 中“向导组织底层能力”的目标不一致。
- 当前代码 gap：`interactive_init.py` 的已有 Harness 维护入口没有 `benchmark` / `bench` 动作，未知输入会默认退出；README 和 init workflow 文档也未说明 guided benchmark 的写边界。
- 决策：在已有 Harness 维护入口加入 `benchmark` 动作，复用 `run_benchmark(repo, profile=inventory.primary_stack, trace=trace)`，输出 hard status、quality status、check 计数和失败项，并将最终 init trace summary 覆盖为 `existing_harness_action: benchmark`。
- 决策：guided `benchmark` 维护动作失败时不返回非零退出码；它是人工维护入口的状态刷新动作，失败必须显式写入输出、trace 和 `.ai/benchmark-report.yaml`。CI / 自动化仍使用 standalone `benchmark`，保持失败时非零退出。
- Assumptions / risks：benchmark 不是只读动作，会刷新 maturity、improvement、experience index 等派生产物；本轮只承诺不覆盖正式 Guides、Sensors、Workflow Skills、配置、inventory 和扫描产物。
- 边界与失败模式：不重新扫描；不调用 LLM；不应用候选；不生成 `.ai/task-runs`；benchmark failed 不能被改写为 passed 或隐藏失败项。
- Sub agent 使用：使用 explorer 子代理审查候选 gap 和实现陷阱，确认该 milestone 优先级最高，并指出要避免把该动作描述为只读。
- 价值切分：一轮只补 existing-Harness guided `benchmark`，暂缓 guided `recommend-workflow` 和 candidate governance 菜单。
- 验收方式：integration 覆盖通过路径与失败项摘要路径，断言 `BenchmarkReport` schema、trace summary、artifact 记录、不扫描和正式资产未变。
- 验证结果：targeted integration 已通过；fast regression 见本轮提交前验证。
- Self-Harness Gate：README、init workflow、todo 和演进记录需要同步，已纳入本轮；下一轮候选 gap 首选 guided `recommend-workflow` 查看/生成 review-only workflow recommendation，其次是 candidate governance 菜单。

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
