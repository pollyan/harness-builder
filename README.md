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
.venv/bin/harness-builder-agent run --repo tests/fixtures/mini-spring-boot "修复登录接口错误提示不一致的问题"
.venv/bin/harness-builder-agent assess --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent improve --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent benchmark --repo tests/fixtures/mini-spring-boot --profile java-spring
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
  guides/
  sensors/
  skills/
    lightweight/SKILL.md
    bugfix/SKILL.md
  maturity-report.md
  maturity-score.yaml
  evolution-plan.md
```

`run` 会生成任务级产物：

```text
.ai/task-runs/demo-task-001/
  harness-map.yaml
  sensor-report.yaml
  decision-log.md
  handoff-summary.md
  experience-candidates.md
```

`assess` 更新成熟度评估，`improve` 生成待确认改进候选，`benchmark` 会检查文件存在、schema、内容质量和 hard gate Sensor 结果。

## 真实开源仓库验证

真实仓库放在 ignored 的 `.benchmarks/` 下：

```bash
mkdir -p .benchmarks
git clone --depth 1 https://github.com/yangzongzhuan/RuoYi-Vue.git .benchmarks/RuoYi-Vue
git clone --depth 1 https://github.com/dotnet-architecture/eShopOnWeb.git .benchmarks/eShopOnWeb
```

运行完整链路：

```bash
.venv/bin/harness-builder-agent init --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent run --repo .benchmarks/RuoYi-Vue "修复登录接口错误提示不一致的问题"
.venv/bin/harness-builder-agent assess --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent improve --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/RuoYi-Vue --profile java-spring

.venv/bin/harness-builder-agent init --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent run --repo .benchmarks/eShopOnWeb "调整 Catalog 相关低风险文案"
.venv/bin/harness-builder-agent assess --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent improve --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/eShopOnWeb --profile dotnet-aspnet
```

## 测试

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/e2e -q
.venv/bin/python -m pytest tests/acceptance/test_real_llm_scan.py -q
.venv/bin/python -m pytest tests/acceptance/test_real_repositories_e2e.py -q
```

默认测试不运行 `tests/acceptance`，用于 CI 的 mock LLM 验证。显式运行 acceptance 时会实际请求 DeepSeek；没有 `DEEPSEEK_API_KEY` 会失败，不会跳过。

## 本地提交保护

安装仓库内置 Git hooks：

```bash
scripts/install-git-hooks.sh
```

安装后：

- `pre-commit` 会在提交前运行 `.venv/bin/python -m pytest -q`。
- `post-commit` 会提醒推送后运行 `scripts/check-ci.sh` 查看 GitHub Actions。
- `pre-push` 会在推送前再次运行 `.venv/bin/python -m pytest -q`。
- 推送完成后，运行 `scripts/check-ci.sh` 查看当前分支最新 GitHub Actions 结果。
