# Guided Init 多栈仓库组合建模与 CLI 表达设计

## Current State Gap Analysis

| 候选 gap | 目标态 | 当前能力 | 缺口 | 价值 | 风险 / 复杂度 | 可测试性 | 排序 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 多栈仓库组合建模与 CLI 表达 | `init` 能表达 Python Flask 后端 + React / TypeScript 前端等组合，并把模块角色、验证命令和推荐资产串起来 | `primary_stack` 只支持 `java-spring`、`dotnet-aspnet`、`node`、`unknown`；`stacks` 是弱字符串；CLI 只展示主栈和技术线索 | 真实多栈仓库容易降级为 `unknown`，用户补充也被诱导成单栈 | 直接提升真实仓库试跑信任度，并服务 init North Star 的深度引导式扫描理解 | 中等；涉及 schema、prompt、reconciler、CLI 和 weapon selection | unit + guided integration 可覆盖 | P0 |
| 成熟度英文叙事中文化 | CLI 和报告中的 blocker / next step 全中文并围绕 L0-L4 | 成熟度 preview 已前置，但 `maturity_model.py` 仍有英文 blocker | 用户界面泄漏英文内部叙事 | 用户可见、范围小 | 低到中 | unit + integration 可覆盖 | P1 |
| LLM-planned deep scan | LLM 基于 manifest 主导深读计划，Python 做 evidence / allowlist / validation | 已有 LLM evidence planner 和 coverage warning | planner 仍是补充读取，不是扫描主线 | 最贴近长期智能化目标 | 高；涉及 token、prompt、真实 LLM acceptance | 可测但范围大 | P2 |

本轮选择 P0，但只做一个可独立验收的纵向切片：支持 `python-flask` 主栈、React / TypeScript 前端作为同仓多栈线索，CLI 用中文组合表达，并让 weapon selection 能按主后端和前端线索选择对应 Guide / Sensor。

## 用户故事

作为 Harness Maintainer，当我在 Python Flask + React / TypeScript + 部署配置混合的真实仓库上运行 guided `init` 时，我可以在 CLI 和生成资产中看到系统识别到的组合技术栈、模块角色和相关验证能力，并能用 `stack=python-flask`、`module=路径|类型|名称` 或自然语言补充修正扫描理解，从而让后续成熟度初评、Guide / Sensor 预览和生成资产围绕真实主模块，而不是把仓库降级成 `unknown` 或误导为单一技术栈。

## 范围

- 扩展 scan schema 的 canonical primary stack，新增 `python-flask`。
- 扩展 LLM scan prompt，要求 Python Flask 和多栈仓库不要因为前端或部署线索混合而降级为 `unknown`。
- 扩展 scan reconciler 的 alias、evidence 验证、unsupported warning 和 impossible veto。
- 在 ProjectInventory `stack_extensions` 中增加稳定的 `stack_profile`，用于描述主栈、组合栈和模块角色摘要。
- guided CLI 展示组合技术栈：例如 `Python Flask 后端 + React / TypeScript 前端`。
- 用户补充入口允许 `stack=python-flask`，并说明多栈可以用自然语言或 `module=...` 补充。
- weapon library 增加 `python-flask` 与 `node` 的基础 Guide / Sensor，并让 selection 从 `primary_stack` 与 `stacks` 中选择多个可支持栈。

## 非目标

- 不实现完整 LLM-planned deep scan 主线改造。
- 不引入语义索引、向量数据库或无限制读取仓库。
- 不支持所有 Python Web 框架；本轮只把真实试跑暴露的 Flask 组合栈纳入第一批。
- 不把自然语言补充解析成任意复杂结构；无法结构化解析的说明继续作为 `scan_notes` 保存，并进入后续 context / decisions。
- 不改变 benchmark profile 的既有 Java / .NET 验收主线。

## 设计

`LLMScanProposal.primary_stack` 增加 `python-flask`。`stacks` 继续是 canonical lowercase 字符串数组，用于保留 `python`、`flask`、`react`、`typescript`、`vite`、`docker`、`nginx` 等组合线索。这样机器契约保持简单，同时避免把多栈仓库压成单个 display name。

`scan_reconciler` 仍由 Python 做 evidence 验证。它把 `python`、`flask`、`pyproject`、`requirements` 等 alias 规范到 `python-flask`，把 `react`、`typescript`、`vite` 等 alias 规范到 `node`。如果 evidence 同时支持后端和前端，`scan_validation.supported_claims` 应同时包含 `python-flask` 和 `node`。如果 LLM 声称 `python-flask` 但没有 `.py`、`pyproject.toml`、`requirements*.txt` 或 Flask 证据，则显式失败或 warning，不能 silent fallback。

`stack_profile` 是派生用户叙事，不替代 schema 字段。它写入 `inventory.stack_extensions["stack_profile"]`，包含：

- `primary_label`：主栈中文标签。
- `composition_label`：组合栈中文标签。
- `supported_stacks`：scan validation 支持的 canonical 栈。
- `module_roles`：从 modules 中抽取的 `{path, kind, name}`。

guided CLI 用 `composition_label` 展示“初步识别技术栈”“主要技术栈”和最终摘要。原始 `primary_stack`、`stacks` 和 `modules` 仍写入 `project-inventory.json`，方便机器消费。

weapon selection 从 `primary_stack` 和 `stacks` 归一化出多个支持栈。多栈仓库至少选择 `common`、`python-flask`，若 `stacks` 中存在 React / TypeScript / Vite / node 线索且有 evidence 支持，则也选择 `node`。这让生成的 Guide / Sensor 不再只围绕单一后端。

## 验收标准

- 解析 LLM scan response 时，`primary_stack="python-flask"` 合法；prompt 明确列出 `python-flask` 和多栈输出要求。
- Reconciler 在 Python Flask + React / TypeScript evidence 上生成 `primary_stack=python-flask`，`scan_validation.supported_claims` 同时包含 `python-flask` 与 `node`，且没有 unsupported warning。
- guided `init` 在 fake ai4se-like 仓库上展示 `Python Flask 后端 + React / TypeScript 前端`，最终产物 `project-inventory.json` 保留 backend / frontend modules 和 `stack_profile`。
- 用户补充提示包含 `stack=python-flask`，并明确可以用自然语言描述多栈、噪声目录和真实主模块。
- weapon selection 对该仓库选择 `common`、`python-flask` 和 `node`，并生成对应 Guide / Sensor id。
- 不降低既有 Java Spring / .NET / unknown 行为，不引入静默 fallback。

## Assumptions / Risks

- `python-flask` 是第一批新增主栈，不代表 Python 生态全部覆盖。Django、FastAPI 等后续应作为独立 gap。
- 前端线索暂用既有 `node` canonical 栈承载，后续可拆成更细的 frontend stack family。
- 多栈展示来自 evidence 与 LLM proposal 的调和结果，不代表扫描已完整理解所有目录；coverage gap 仍通过已有不确定性机制表达。

## Sub Agent 使用情况

本轮使用两个只读子代理并行做 gap 分析和测试覆盖审查。两个子代理均建议优先处理多栈建模，并把成熟度中文化和 LLM-planned deep scan 留作后续切片。

