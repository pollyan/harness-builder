# Harness Builder

Harness Builder 是一个面向既有代码库的 AI Coding Harness POC。当前仓库提供 `harness-builder-agent` CLI，用来生成项目级 `.ai/` Harness、Workflow Skills、Guides、Sensors、成熟度评估和改进候选。

当前仍是 POC，不是生产级产品。

## 工程规则文档

本仓库使用 Codex 进行开发，项目级约束入口是 `AGENTS.md`。详细工程规则放在 `docs/engineering/`，按任务渐进式加载：

- `docs/engineering/architecture.md`：架构边界和模块职责。
- `docs/engineering/init-workflow.md`：`init` 工作流、生成产物和失败行为。
- `docs/engineering/llm-contracts.md`：DeepSeek、LLM-first 扫描、schema 和 no fallback 规则。
- `docs/engineering/testing-strategy.md`：测试分层、断言深度和 acceptance 策略。
- `docs/engineering/sensor-and-gate-rules.md`：Sensor、hard gate 和 benchmark 质量门禁规则。

## 环境准备

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[test]"
```

真实 DeepSeek 扫描验收使用本地 `.env`，不要提交：

```bash
DEEPSEEK_API_KEY=你的 DeepSeek API Key
HARNESS_BUILDER_LLM_PROVIDER=deepseek
HARNESS_BUILDER_LLM_BASE_URL=https://api.deepseek.com
HARNESS_BUILDER_LLM_MODEL=deepseek-v4-pro
```

## Agent CLI

核心命令：

```bash
.venv/bin/harness-builder-agent init --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent assess --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent improve --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent benchmark --repo tests/fixtures/mini-spring-boot --profile java-spring
```

`init` 默认是本地人机引导式向导。它会用中文解释扫描发现，说明主要技术栈、模块、证据和验证命令，允许用户输入补充，或用 `stack=<value>`、`module=路径|类型|名称`、`command=ID|命令|类型|gate|来源|置信度`、`risk=路径|原因` 修正关键扫描结论；随后会收集团队代码规范、架构约束、测试策略等团队规则，逐项展示 Guide / Sensor 候选，说明推荐 Workflow，并在写入前展示最终摘要。摘要阶段可以输入 `back` 返回修改，也可以输入 `confirm` 写入资产。

自动化、测试、CI 或 acceptance 场景必须显式使用非交互模式：

```bash
.venv/bin/harness-builder-agent init --non-interactive --repo tests/fixtures/mini-spring-boot
```

`init` 会在目标仓库生成 `.ai/`：

```text
.ai/
  project-inventory.json
  command-catalog.yaml
  harness-config.yaml
  scan-metadata.yaml
  llm-scan-proposal.json
  weapon-library-selection.yaml
  interaction-decisions.yaml
  guides/
  sensors/
  skills/
    lightweight/SKILL.md
    bugfix/SKILL.md
  maturity-report.md
  maturity-score.yaml
  evolution-plan.md
```

Harness Builder 不提供任务级 `run` 命令。真实 AI Coding 工具执行 Workflow Skill 时，应按 Skill 中的 runtime artifact contract 生成任务级可观测产物：

```text
.ai/task-runs/demo-task-001/
  harness-map.yaml
  sensor-report.yaml
  runtime-summary.yaml
  workflow-events.jsonl
  used-guides.yaml
  decision-log.md
  handoff-summary.md
  experience-candidates.md
```

`assess` 更新成熟度评估，`improve` 生成待确认改进候选，`benchmark` 会检查 Harness 资产文件存在、schema、内容质量、Workflow Skill 引用和 hard gate command 证据。

`benchmark-report.yaml` 中：

- `status` 表示硬验收是否通过，缺文件、schema 错误、Workflow Skill 引用错误或 hard gate command 证据不足会让它变成 `failed`。
- `quality_status` 表示质量评分结论：`passed`、`degraded` 或 `failed`。
- `quality_scores` 给出 scan、guide、sensor、workflow 的分项评分、原因和建议。

## 真实开源仓库验证

真实仓库放在 ignored 的 `.benchmarks/` 下：

```bash
mkdir -p .benchmarks
git clone --depth 1 https://github.com/yangzongzhuan/RuoYi-Vue.git .benchmarks/RuoYi-Vue
git clone --depth 1 https://github.com/dotnet-architecture/eShopOnWeb.git .benchmarks/eShopOnWeb
```

运行完整链路：

```bash
.venv/bin/harness-builder-agent init --non-interactive --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent assess --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent improve --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/RuoYi-Vue --profile java-spring

.venv/bin/harness-builder-agent init --non-interactive --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent assess --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent improve --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/eShopOnWeb --profile dotnet-aspnet
```

## 测试

```bash
scripts/test-fast.sh
scripts/test-acceptance.sh
scripts/test-full.sh
```

`scripts/test-fast.sh` 运行快速回归测试，不包含 `tests/acceptance`，适合本地 Git hook、CI 默认验证和开发过程中的快速反馈。

`scripts/test-acceptance.sh` 会实际请求 DeepSeek，并运行真实开源仓库验收；没有 `DEEPSEEK_API_KEY` 或缺少 `.benchmarks/` 真实仓库会失败，不会跳过。

`scripts/test-full.sh` 先运行 fast，再运行 acceptance，适合发布前、目标模式完成前或扫描/LLM/真实仓库验收相关改动后执行。

## 本地提交保护

安装仓库内置 Git hooks：

```bash
scripts/install-git-hooks.sh
```

安装后：

- `pre-commit` 会在提交前运行 `scripts/test-fast.sh`，作为快速兜底。
- `post-commit` 会提醒推送后运行 `scripts/check-ci.sh` 查看 GitHub Actions。
- `pre-push` 会在推送前运行 `scripts/test-full.sh`，包含真实 DeepSeek 和真实开源仓库验收。
- 推送完成后，运行 `scripts/check-ci.sh` 查看当前分支最新 GitHub Actions 结果。

Codex 侧的规则写在 [AGENTS.md](/Users/anhui/Documents/myProgram/harness-builder/AGENTS.md)：创建 commit 前必须主动运行 `scripts/test-fast.sh`，push 前必须主动运行 `scripts/test-full.sh`，push 完成后必须主动运行 `scripts/check-ci.sh`。
