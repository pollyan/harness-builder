# AGENTS.md

本仓库是 Harness Builder，一个 Python CLI POC，用于为既有代码库生成 AI Coding Harness 资产，包括项目扫描结果、Guides、Sensors、Workflow Skills、成熟度评估和 benchmark 报告。

本文件是 Codex 的项目级规则入口。它只放稳定的硬约束和渐进式加载索引；详细规则放在 `docs/engineering/` 下，按任务需要读取。

## 渐进式加载

- 修改架构、模块边界或目录结构前，阅读 `docs/engineering/architecture.md`。
- 修改 `init` 命令、扫描到生成的主流程、生成产物或 `.ai` 输出契约前，阅读 `docs/engineering/init-workflow.md`。
- 修改 LLM 扫描、DeepSeek 配置、Prompt、Schema、扫描调和逻辑前，阅读 `docs/engineering/llm-contracts.md`。
- 修改测试、fixture、e2e、acceptance、断言策略或 CI 行为前，阅读 `docs/engineering/testing-strategy.md`。
- 修改 Sensor、hard gate、benchmark 检查、验证报告或质量门禁前，阅读 `docs/engineering/sensor-and-gate-rules.md`。
- 只在任务需要时加载对应专题文档，不要把所有工程文档一次性塞进上下文。

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

默认回归测试：

```bash
.venv/bin/python -m pytest -q
```

真实 DeepSeek / 开源仓库验收不在默认 CI 中运行。需要显式运行 `tests/acceptance`，且缺少 `DEEPSEEK_API_KEY` 时必须失败，不能跳过。

## 提交与 CI 规则

- Codex 在创建 git commit 前，必须先在本地运行默认回归测试：`.venv/bin/python -m pytest -q`。
- 如果本地缺少 `.venv/bin/python`，可以使用当前环境中的 `python -m pytest -q`，但必须在回复中说明。
- 推送代码前，本地 Git hook 会再次运行默认回归测试。
- GitHub Actions 只有 push 后才会触发；推送完成后必须运行 `scripts/check-ci.sh` 查看当前分支最新 CI 状态。
- 不要把“本地测试通过”等同于“远端 CI 通过”，两者都需要明确确认。
