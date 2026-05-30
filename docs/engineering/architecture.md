# 架构规则

本文描述 Harness Builder 当前架构边界和演进约束。修改模块边界、目录结构、核心流程或跨层调用前，先阅读本文。

## 当前架构概览

Harness Builder 是一个 Python CLI 项目，主入口是 `harness-builder-agent`。当前核心命令包括：

- `init`：扫描目标仓库并生成初始 Harness 资产。
- `run`：基于已生成 Harness 模拟任务级工作流选择、Guide 使用和 Sensor 执行。
- `assess`：生成或更新成熟度评估。
- `improve`：生成待确认的改进候选。
- `benchmark`：对完整链路产物做结构、内容和质量门禁检查。

当前主要目录职责：

| 路径 | 职责 |
| --- | --- |
| `src/harness_builder_agent/cli.py` | CLI 参数解析、命令入口、顶层异常出口 |
| `src/harness_builder_agent/schemas/` | 机器消费数据结构的 Pydantic schema |
| `src/harness_builder_agent/tools/` | 扫描、LLM、调和、资产生成、benchmark 等业务模块 |
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
- `llm_scan_analyzer` 负责 LLM-first 分析，并输出结构化 proposal。
- `scan_reconciler` 负责把 LLM proposal 和 evidence 调和成稳定的 `ProjectInventory` 与 `CommandCatalog`。
- 如果 LLM 输出和 evidence 明显冲突，应该降级置信度、标记人工确认或失败，不能默默接受。
- 不允许新增“LLM 不可用时用确定性扫描冒充成功”的 fallback。

### 资产生成层

资产生成层负责把扫描结果、命令目录、武器库选择和上下文输入写成 Harness 资产。

规则：

- 资产生成应该由确定性程序完成，不能让 LLM 直接随意写文件。
- 生成 Markdown 可以是语义化内容，但必须保留稳定章节，便于测试和人工审查。
- 生成 JSON/YAML 必须符合 schema。
- Workflow Skill 当前来自固定模板，不做动态 LLM 生成。
- 如果 writer 文件持续膨胀，应优先按产物类型拆分，而不是继续堆在单文件中。

### 武器库层

武器库层为不同技术栈提供稳定、可复用的 guide/sensor 基线。

规则：

- 内置武器库负责提供稳定下限，避免每次完全依赖 LLM 生成导致结果漂移。
- LLM 可以提出增强候选，但候选必须标记为 candidate，并要求人工确认。
- 武器库选择结果必须落盘，便于审计和测试。

### 可观测层

可观测层包括 generation trace、runtime trace、artifact list 和 decision log。

规则：

- 关键命令应记录开始、完成、失败和关键阶段事件。
- 生成的重要文件应记录到 artifact list。
- 失败不能只表现为异常栈；应尽量保留可解释的阶段和上下文。
- trace 是调试和验收依据，不是装饰性输出。

### Benchmark 层

`benchmark` 是 POC 的验收器，用来检查生成 Harness 是否达到最低质量要求。

规则：

- benchmark 不应只检查文件存在，还要检查 schema、内容章节、跨文件引用和 hard gate 结果。
- hard gate 失败时，benchmark 可以失败，但必须给出明确失败项。
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

