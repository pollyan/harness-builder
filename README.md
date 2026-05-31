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
.venv/bin/harness-builder-agent self-improve --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent recommend-workflow --repo tests/fixtures/mini-spring-boot --task-brief "Fix checkout permission bug." --task-id task-1
.venv/bin/harness-builder-agent review-candidate --repo tests/fixtures/mini-spring-boot --candidate-id guide-project-context-scope --decision accepted --rationale "Reviewed by Harness Maintainer."
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
  init-summary.md
  guides/
  sensors/
  skills/
    lightweight/SKILL.md
    bugfix/SKILL.md
  maturity-report.md
  maturity-score.yaml
  maturity-evidence.yaml
  evolution-plan.md
  experience/experience-index.yaml
```

`init-summary.md` 是首次初始化后的入口摘要，按成熟度框架说明当前等级、主要阻断项、建议下一步和优先查看的文件。

再次运行默认 guided `init` 时，如果目标仓库已经存在 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml`，CLI 会先进入已有 Harness 维护入口，展示当前成熟度、benchmark，以及分项 Experience / review signals，包括 pending improvements、asset candidates、candidate governance、maturity reviews、workflow recommendations、runtime task runs、self-improve package、human-input-needed 和 schema/content failed checks。当前可选动作包括 `exit` 只读退出、`assess` 复评成熟度并刷新 maturity / init summary 产物、`improve` 基于成熟度缺口生成 review-only 改进候选、`benchmark` 运行质量门禁并刷新 benchmark / maturity / improvement 派生产物、`recommend-workflow` 输入任务说明并生成 review-only Workflow 推荐、`review-candidate` 记录候选 `accepted` / `deferred` / `rejected` 治理决策或显式应用单个 Guide / Sensor 候选、`self-improve` 生成 review-only 自改进审查包，以及 `reinit` 显式重新扫描生成。`benchmark` 维护动作不覆盖正式 Guides、Sensors、Workflow Skills、配置或 inventory；如果质量门禁失败，会在输出、trace 和 `.ai/benchmark-report.yaml` 中显式展示失败项。`recommend-workflow` 维护动作会刷新最新 `.ai/review/workflow-routing-recommendation.*`，同时追加 `.ai/review/workflow-routing-recommendations/` 历史索引和摘要，让 Experience / Maturity 识别多次任务路由建议；它不执行任务、不创建 `.ai/task-runs`、不修改正式 routing policy。guided `review-candidate` 的 `applied` 只支持 Guide / Sensor Markdown 单候选应用，会记录 governance 和 applied path；`workflow_policy` 应用仍需使用专家命令和结构化 patch 审核。`self-improve` 是显式 LLM 智能改进动作，会刷新 maturity review、asset candidates 和 self-improve package，但仍保持 review-only，不执行 Runtime 或应用正式资产。CI 或脚本需要失败退出码时仍应直接调用 standalone `benchmark` 命令。

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

`assess` 更新成熟度评估，`improve` 生成待确认改进候选，`self-improve` 串联成熟度评估、改进候选、LLM maturity review 和 review-only asset candidates，生成 `.ai/review/self-improve-package.*`。`self-improve` 不应用正式 Harness 变更，不执行 Runtime workflow，也不创建 `.ai/task-runs`。

`review-candidate` 是 Harness Maintainer 的显式候选治理动作。它读取 `.ai/review/asset-candidates.yaml`，把某个候选记录为 `accepted`、`deferred`、`rejected` 或 `applied`，并写入 `.ai/review/candidate-governance.*`。`applied` 支持 Guide / Sensor Markdown 候选追加到正式 `.ai/**/*.md` 资产；`workflow_policy` 候选必须提供结构化 `workflow_policy_patch`，只能通过 schema 校验后更新 `.ai/harness-config.yaml` 的 routing rule，并会刷新成熟度证据。

`benchmark` 会检查 Harness 资产文件存在、schema、内容质量、Workflow Skill 引用、review-only 智能改进产物、candidate governance 产物和 hard gate command 证据。

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
.venv/bin/harness-builder-agent self-improve --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/RuoYi-Vue --profile java-spring

.venv/bin/harness-builder-agent init --non-interactive --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent assess --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent improve --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent self-improve --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/eShopOnWeb --profile dotnet-aspnet
```

## 测试

```bash
scripts/test-unit.sh
scripts/test-integration.sh
scripts/test-guided-init.sh
scripts/test-llm-contracts.sh
scripts/test-fast.sh
scripts/test-acceptance.sh
scripts/test-acceptance-llm-smoke.sh
scripts/test-acceptance-real-repo.sh
scripts/test-acceptance-self-improve.sh
scripts/test-full.sh
```

`scripts/test-fast.sh` 运行快速回归测试，不包含 `tests/acceptance`，适合本地 Git hook、CI 默认验证和开发过程中的快速反馈。

`scripts/test-unit.sh`、`scripts/test-integration.sh`、`scripts/test-guided-init.sh` 和 `scripts/test-llm-contracts.sh` 是常用开发切片，只用于缩短开发反馈，不能替代 `scripts/test-fast.sh` 或 `scripts/test-full.sh`。

`scripts/test-acceptance.sh` 会实际请求 DeepSeek，并运行真实开源仓库验收；没有 `DEEPSEEK_API_KEY` 或缺少 `.benchmarks/` 真实仓库会失败，不会跳过。

开发时可以把 pytest 目标透传给 acceptance 脚本，只运行当前相关的真实链路，例如：

```bash
scripts/test-acceptance.sh tests/acceptance/test_real_repositories_e2e.py::test_ruoyi_vue_real_repository_with_self_improve
```

也可以使用 `scripts/test-acceptance-llm-smoke.sh`、`scripts/test-acceptance-real-repo.sh` 或 `scripts/test-acceptance-self-improve.sh` 运行命名好的真实验收切片。targeted acceptance 只用于缩短开发反馈；推送或发布前仍以 `scripts/test-full.sh` 为准。

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
