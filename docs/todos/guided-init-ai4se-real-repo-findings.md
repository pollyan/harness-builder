# guided init 在 ai4se 真实仓库上的体验与扫描深度问题

## 状态

- 状态：open
- 优先级：high
- 发现日期：2026-05-31
- 相关命令：`harness-builder-agent init`
- 触发样本：`/Users/anhui/Documents/myProgram/ai4se`
- 相关工程规则：`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`
- 相关产品方向：`docs/strategy/init-north-star.md`
- 已完成切片：
  - `2026-05-31 Init 工具工作区 Evidence 降噪`：忽略 `.claude` / `.opencode` 工具工作区，并把 Python 项目 manifest 纳入 key evidence。
  - `2026-05-31 Guided Init 采样覆盖不足中文化`：`source_sampling_truncated` 不再把 `source:.py skipped 73 files` 作为 CLI 主界面文案，而是用中文说明抽样范围、未进入初始摘要数量、影响和补充建议；metadata 保留 bucket / selected / skipped / total 计数。
  - `2026-05-31 Guided Init 高风险发现确认链路`：疑似 API key / 凭证 / 安全 / 支付 / 权限 / 数据迁移风险会在 CLI 中标记为待确认高风险，并进入 questionnaire、human-input-needed、Guide 和 Sensor 的确认与升级说明。
  - `2026-05-31 Guided Init 多栈仓库组合建模`：scan schema 支持 `python-flask`，reconciler 可验证 Python Flask + React / TypeScript 组合栈并派生 `stack_profile`，guided CLI 用中文展示组合技术栈，weapon library 可同时选择 Python Flask 后端和 Node / 前端 Guide / Sensor。
  - `2026-05-31 成熟度叙事中文化`：`MaturityReport` 源头的 blocker、evidence summary、next level requirement 和 blocking cap 改为中文；`maturity-report.md` 使用中文维度标签和“证据 / 阻断”展示标签，guided CLI 不再泄漏已知英文 maturity blocker。
  - `2026-06-01 LLM 规划式深度扫描 Manifest 语义增强`：全量轻量 `files[]` manifest 为每个文件保留 bucket、priority、reason，让 LLM evidence planner 在 coverage gap 下能主动选择未采样但高价值的风险、入口、测试或业务文件深度读取；仍不无限制读取全仓。
  - `2026-06-01 LLM Evidence Plan 可审计`：`.ai/scan-metadata.yaml` 通过 `evidence_expansion` 记录 planner prompt version、requested paths、risk focus、rationale、planner confidence、实际读取 paths 和读取文件数量；planner 低置信度会进入 warning 和 human confirmation 信号。
  - `2026-06-01 Guided Init LLM Evidence Plan 可见化`：首次 guided `init` 在扫描发现阶段展示“LLM 深度补充”，说明 planner 补读路径、关注原因、规划说明、实际读取结果和置信度；planner 低置信度进入 `confirm:evidence-expansion` 待确认项和 `human-input-needed.md`。
  - `2026-06-01 Scan Follow-up Questions`：coverage gap、LLM stack claim 缺少 evidence、primary stack unknown、模块边界不清和测试 evidence 缺失会进入 `ScanMetadata.followup_questions`，guided CLI 展示“深度追问”，并进入 `questionnaire.yaml` / `human-input-needed.md`。
  - `2026-06-01 Scan Follow-up Self-check`：存在 `followup_questions` 时，真实 LLM 链路或显式 mock caller 会执行 review-only 二次自检，写入 `ScanMetadata.self_check`，guided CLI 展示“LLM 二次自检”，questionnaire 把 resolution 追加到对应追问的 reason；自检不自动修正正式扫描结论。
- 剩余 LLM-planned deep scan 仍保持 open。

## 背景

用户在真实仓库 `ai4se` 上手工执行首次 guided `init`，CLI 已经展示扫描进度、扫描发现、风险、不确定性、验证缺口、扫描后的成熟度初评和补充入口。整体旅程骨架已经可用，但这次真实样本暴露出一组影响用户信任和扫描深度的问题。

这些问题不应被当作单个 fixture 的偶发现象。`ai4se` 是多技术栈、含工具工作区、历史部署包和较多源码文件的真实项目，正好代表企业仓库中常见的不规范结构、噪声目录、多栈混合和安全风险。

## 已发现问题

### 1. 扫描 evidence 被工具工作区和历史产物污染

CLI 的判断依据优先展示了 `.claude/worktrees/`、`.opencode/`、`deploy-package/.opencode/` 等路径下的 `package.json`。这些更像工具工作区、临时工作树、历史产物或部署包，不应成为主要技术栈判断和用户展示的优先证据。

理想状态：

- 工具工作区、缓存、历史部署包和生成物应被降权或明确标记为 secondary evidence。
- CLI 优先展示根目录配置、主应用目录、真实源码入口、CI、README、`pyproject.toml`、`requirements.txt`、主 `package.json` 等证据。
- 如果噪声目录仍被纳入 evidence，应向用户解释其来源和可信度，而不是当作主项目事实。

### 2. 多栈仓库的 primary stack 建模不足

扫描识别出 `python`、`flask`、`react`、`typescript`、`tailwind`、`vite`、`docker`、`nginx` 等线索，但最终 primary stack 仍是 `unknown`，用户补充提示也只提供 `java-spring`、`dotnet-aspnet`、`node`、`unknown`。

理想状态：

- 多栈仓库应能表达为 Python Flask + React / TypeScript 这类组合，而不是只能降级为 `unknown`。
- primary stack、stack family、modules 和 workflow recommendations 应能区分“主业务后端”“前端门户”“工具子项目”“部署产物”等角色。
- 用户补充入口应支持多栈说明，而不是诱导用户误选单一 `node` 或 `unknown`。

### 3. 用户补充入口仍偏结构化参数

当前 CLI 虽然允许自然语言补充，但视觉焦点仍落在 `stack=...`、`module=...`、`command=...`、`risk=...` 这类内部格式上。真实用户可能不知道应该如何描述“这是多栈项目”“这些目录是噪声”“这个风险应升级到人工确认”。

理想状态：

- 先用自然语言问题引导用户确认关键判断，再把结构化格式作为高级选项。
- 针对当前扫描的不确定性动态给出示例，例如“如果 `.claude/worktrees` 不是主项目，请直接说明”。
- 用户补充后，CLI 应明确复述这些补充如何影响技术栈、模块、风险、成熟度和 Harness 推荐。

### 4. 成熟度差距说明出现英文和内部化表达

“主要差距”中出现了英文句子，例如 `Guides are structured but not yet dynamically loaded by task risk and context.`。这不符合中文、面向用户、解释性输出的要求。

理想状态：

- 所有面向用户的成熟度叙事应使用中文。
- 表达应围绕 L0-L4 主线，说明“当前等级是什么、为什么、下一等级差什么、推荐怎么补齐”。
- 内部维度、Runtime、dynamic loading 等概念需要翻译成用户能理解的工程影响。

### 5. skipped files 信息过于内部化，且扫描深度需要重新审视

CLI 直接展示了 `source:.js skipped 74 files`、`source:.py skipped 73 files`、`source:.ts skipped 88 files`、`source:.tsx skipped 52 files`。这些信息有审计价值，但不适合作为用户主要界面语言。同时，用户明确提出：深度扫描不能只是浅尝辄止，关键文件被跳过不能不解释、不补救。

理想状态：

- 用户界面应把 skipped files 翻译成“仓库较大，本次只抽样读取了部分文件；可能遗漏核心模块，需要继续补充 evidence 或请用户确认”。
- skipped / truncated / sampled 信息应进入可审计 metadata，但 CLI 要解释其影响。
- 对关键 bucket 或高风险目录，不能仅因为采样上限跳过；应通过 LLM-guided evidence expansion、用户确认或后续 targeted scan 补足。

### 6. 高风险发现没有足够突出

扫描发现 `docs/a.json` 可能包含明文 API key，这是高价值安全风险，但 CLI 只是把它作为普通风险列表展示。

理想状态：

- 疑似密钥、凭证、权限、安全、支付、数据迁移等高风险发现应被显著标记。
- CLI 应提示是否加入 Guide、Sensor、Workflow escalation 或 `human-input-needed`。
- 高风险风险项不能自动写入正式治理规则为事实，应作为需要人工确认的强引导项。

### 7. 扫描架构需要重新评估 LLM 与确定性扫描的主从关系

当前实现先收集确定性 evidence，再让 LLM 基于 evidence 做结构化分析和补充 evidence planning。虽然确定性扫描按工程规则只应收集 evidence、不做最终业务判断，但真实体验中，采样、过滤、路径排序和 evidence 展示会影响 LLM 看到什么，也可能把工具工作区、历史产物或噪声路径放大，进而误导 LLM 判断。

评审结论：这个方向是合理的，但不应被理解为“完全先 LLM、后确定性脚本”，更不应允许 LLM 无限制读取全仓库。更准确的目标是 **LLM-planned、evidence-grounded 的深度扫描**：LLM 负责决定应该理解什么、下一步该看什么、哪些地方可疑；Python / 确定性逻辑负责安全列目录、读取文件、控制 token、校验 schema、验证 claim、记录证据。

用户期望的目标态是：

- 扫描应以 LLM 对代码库的深度理解为主线。
- LLM 首先基于全量轻量文件树、目录语义、README、CI、配置和关键入口形成探索计划，而不是只被确定性脚本预先采样后的 evidence 牵引。
- 确定性脚本主要承担 evidence collection、allowlist、安全读取、token 控制、schema 校验、detector 验证、冲突检查和加速，而不是决定哪些信息值得理解。
- 当 LLM 遇到确定性强的文件或 claim 时，再调用针对性 detector / parser 做补强和验证。
- 对大仓库不能简单“跳过很多文件后继续生成”，必须让跳过、抽样和覆盖不足显式影响置信度、用户追问和后续推荐。

建议后续重新审视扫描链路：

```text
目标态候选：
1. 生成全量轻量 file manifest 和目录概览。
2. LLM 基于 manifest / README / CI / 根配置提出深度扫描计划。
3. Python 按 allowlist 和预算读取 LLM 请求的文件摘要。
4. LLM 形成 stack / module / command / risk / maturity 输入的结构化判断。
5. Python detector / parser 验证 LLM claim，记录 support / conflict / unknown。
6. 对 conflict、unknown、coverage gap 触发二次 LLM self-check 或用户确认。
7. 再进入 maturity snapshot、Harness 推荐和写入前 preview。
```

这不是要求 LLM 无限制读取所有文件；而是要求“扫描主线由智能探索和风险意识驱动，确定性脚本做安全、证据、验证和加速支撑”，避免确定性采样结果提前决定系统理解边界。

推荐的工程边界：

- Python 第一阶段可以生成全量轻量 file manifest，但只应包含路径、大小、扩展名、目录层级、疑似依赖 / 工具 / 生成物分类等轻量事实，不直接给出业务结论。
- Python 可以先读取少量稳定入口，例如 README、根配置、CI、`pyproject.toml`、`package.json`、`pom.xml`、`.sln`、Docker / deploy 配置等，用于给 LLM 初始上下文。
- LLM 基于 manifest 和稳定入口提出 scanning plan，判断哪些目录像主项目、哪些像工具噪声、哪些文件值得深入读取。
- Python 只能按 LLM plan 读取仓库内 allowlist 路径，并受 token、安全和目录策略限制；不得因为路径相似而自动纠正 LLM 请求。
- LLM 形成结构化理解后，Python detector / parser 再验证 stack、module、command、risk 等 claim，输出 support / conflict / unknown。
- 对冲突、unknown、coverage gap，不应静默降级为成功；应进入二次 LLM self-check、用户确认或 `human-input-needed`。
- 确定性扫描仍然必要，但它的角色是 evidence、护栏、验证和加速，不是提前决定仓库理解边界。

## 影响范围

- `harness-builder-agent init` 首次 guided init 的真实用户体验。
- LLM evidence planning、evidence collection、scan reconcile、scan metadata 和 CLI scan findings 展示。
- 多栈仓库的 ProjectInventory / stack 建模。
- 成熟度初评和写入前 preview 的中文表达。
- 高风险发现进入 Guide / Sensor / Workflow escalation / human-input-needed 的策略。
- `init` 真实仓库验收样本和 CLI transcript 级测试。

## 初步验收标准

进入实施前，应先产出 spec，明确扫描链路是否调整为更强的 LLM-planned / LLM-first deep scan，以及哪些能力只做展示修复。

第一批可独立验收目标可以包括：

- 在 `ai4se` 或等价多栈 fixture 上，`.claude/worktrees`、`.opencode`、`deploy-package` 等噪声路径不会作为主要判断依据优先展示。
- CLI 能用中文解释多栈扫描结果，并支持 Python Flask + React / TypeScript 这类组合表达。
- skipped / sampled 文件信息转化为人类可读的不确定性和后续补充建议。
- 成熟度差距、阻断项和推荐动作全部使用中文，并围绕 L0-L4 叙事。
- 疑似密钥等高风险发现被突出展示，并进入人工确认或候选治理链路。
- 用户补充“某些目录是噪声、某些模块是真实主模块、某些命令是 hard / soft gate”后，能影响后续 inventory、command catalog、maturity preview 和生成资产。
- 测试或真实 CLI transcript 覆盖上述行为，不只断言文件存在。

## 非目标

第一轮不要求：

- 一次性实现完整语义索引或向量数据库。
- 无限制读取仓库所有文件全文。
- 支持所有语言生态的完美 primary stack 枚举。
- 自动清理目标仓库中的疑似密钥。
- 自动应用高风险治理规则到正式 Harness。

重点是把真实仓库中暴露出的信任问题、扫描深度问题和用户体验问题沉淀为后续可设计、可测试、可验收的工作项。
