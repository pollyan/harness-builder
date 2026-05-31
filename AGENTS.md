# AGENTS.md

本仓库是 Harness Builder，一个 Python CLI POC，用于为既有代码库生成 AI Coding Harness 资产，包括项目扫描结果、Guides、Sensors、Workflow Skills、成熟度评估和 benchmark 报告。

本文件是 Codex 的项目级规则入口。它只放稳定的硬约束和渐进式加载索引；详细规则放在 `docs/engineering/` 下，按任务需要读取。

## 渐进式加载

- 修改架构、模块边界或目录结构前，阅读 `docs/engineering/architecture.md`。
- 修改 `init` 命令、扫描到生成的主流程、生成产物或 `.ai` 输出契约前，阅读 `docs/engineering/init-workflow.md`。
- 修改 LLM 扫描、DeepSeek 配置、Prompt、Schema、扫描调和逻辑前，阅读 `docs/engineering/llm-contracts.md`。
- 修改测试、fixture、e2e、acceptance、断言策略或 CI 行为前，阅读 `docs/engineering/testing-strategy.md`。
- 修改 Sensor、hard gate、benchmark 检查、验证报告或质量门禁前，阅读 `docs/engineering/sensor-and-gate-rules.md`。
- 修改产品定位、成熟度框架、Experience / Self-Improve、智能改进、Workflow Toolkit 或长期路线图前，阅读 `docs/strategy/README.md`，再按需阅读其中的全景规划或 POC 历史规划。
- 只在任务需要时加载对应专题文档，不要把所有工程文档一次性塞进上下文。

## 目标模式选题规则

- 每轮选择新的 milestone / 话题前，必须先检查 `docs/todos/` 中未完成的工作项。
- 如果存在未完成 todo 且符合当前产品北极星和用户最新优先级，应优先消化 todo；只有没有合适 todo 时，才从新的 gap analysis 中选择全新话题。
- milestone 粒度应以“一个完整用户故事或工程信任故事”为边界，而不是以单个字段、单条文案、单个 warning 或单个测试为边界。
- 如果同一 todo 下的多个小问题服务同一个用户可感知体验、共享同一数据流，并且可以在一次 spec / plan / TDD 中清楚验收，应合并为一个 milestone，允许形成多个本地 commit。
- 合并 milestone 不能变成无边界大重构；如果会跨越独立用户旅程、引入高风险 schema 迁移、触碰多个不相关模块或需要不同验收语义，应继续拆分。
- 选择 todo 时仍需保持单轮只做一个独立可验收工作包，并在 spec / plan / evolution log 中说明该工作包对应的 todo、用户价值和拆分/合并理由。

## 硬约束

- 不允许添加静默 fallback 逻辑。No silent fallback.
- 需要 DeepSeek 或真实 LLM 时，如果不可用，必须显式失败。
- 确定性扫描只能收集 evidence，不能替代 LLM-first 分析。
- 机器消费的输出必须有 Pydantic schema，并在测试中校验。
- 语义上下文消费的 Markdown 可以自然语言化，但必须保留稳定章节和可审计来源。
- 文件生成测试不能只断言文件存在，必须断言 schema、关键字段、关键章节和跨文件引用。
- 修改 `init` 主链路时，必须同步考虑 integration/e2e/benchmark 覆盖。
- 不提交 `.env`、`.benchmarks/`、缓存、`__pycache__` 或临时生成物。
- 工作流过程遵循当前 Codex/Superpowers 会话要求；本仓库文档只补充 Harness Builder 的工程约束。

## 常用验证

快速回归测试：

```bash
.venv/bin/python -m pytest -q
```

本地全量回归：

```bash
scripts/test-full.sh
```

真实 DeepSeek / 开源仓库验收不在默认 CI 中运行。需要显式运行 `tests/acceptance`，且缺少 `DEEPSEEK_API_KEY` 时必须失败，不能跳过。

## 提交与 CI 规则

- Codex 的本地 commit message 必须使用中文；`docs/superpowers/specs/`、`docs/superpowers/plans/` 和 `docs/evolution-log.md` 等过程文档也必须用中文撰写。
- Codex 在创建 git commit 前，必须先主动运行快速回归：`scripts/test-fast.sh`。
- 本地 commit 可以按独立切片或阶段性检查点创建；不要把“每个 commit”自动等同为“必须 push 到 GitHub”。
- push 到 GitHub 的粒度应以完整 todo、完整工作包或已经产生独立用户价值的功能批次为边界；允许多个本地 commit 累积后再统一 push。
- Codex 在 push 到 GitHub 前，必须先主动运行本地全量回归：`scripts/test-full.sh`。降低 push 频率不豁免 push 前全量验证，只减少触发次数。
- 如果本地缺少 `.venv/bin/python`，可以使用当前环境中的 `python -m pytest -q`，但必须在回复中说明。
- 本地 `.githooks` 只是兜底机制，不是 GitHub hook，也不是 Codex 产品层面的 hook；Codex 仍必须按本文件规则主动执行验证。
- 推送代码前，本地 Git hook 会运行本地全量回归测试。
- GitHub Actions 只有 push 后才会触发；`scripts/check-ci.sh` 只作为人工需要时的手动查询工具，不是 Codex push 后的阻塞步骤。
- 不要把“本地测试通过”等同于“远端 CI 通过”；如果没有手动查询远端 CI，回复中只能说明本地验证结果和已 push 状态。
