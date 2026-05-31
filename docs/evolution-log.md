# Harness Builder 演进记录

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
