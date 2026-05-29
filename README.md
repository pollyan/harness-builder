# Harness Builder Agent POC 使用说明

Harness Builder Agent 是一个面向既有代码库的 AI Coding Harness 生成器 POC。它会扫描目标仓库，生成项目级 `.ai/` 控制资产，并基于一个小任务跑出任务级 Harness Map、Sensor Report、Decision Log、Handoff Summary 和经验候选。

当前 POC 重点验证三件事：

- 能不能为 Java / Spring Boot / Vue 项目生成第一版 `.ai/` Harness。
- 能不能为 .NET / ASP.NET Core 项目生成同结构的 `.ai/` Harness。
- 能不能在 fixture 和真实开源仓库上跑通 `init -> run -> benchmark` 的端到端闭环。

## 1. 环境准备

进入项目目录：

```bash
cd /Users/anhui/Documents/myProgram/harness-builder
```

创建并安装本地虚拟环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[test]"
```

安装完成后，可以先确认 CLI 可用：

```bash
.venv/bin/harness-builder-agent --help
```

应该能看到三个命令：

- `init`
- `run`
- `benchmark`

## 2. 配置 DeepSeek API Key

真实大模型 smoke test 使用 DeepSeek。仓库根目录可以放一个本地 `.env` 文件：

```bash
cat > .env <<'EOF'
DEEPSEEK_API_KEY=你的 DeepSeek API Key
HARNESS_BUILDER_LLM_PROVIDER=deepseek
HARNESS_BUILDER_LLM_BASE_URL=https://api.deepseek.com
HARNESS_BUILDER_LLM_MODEL=deepseek-v4-pro
EOF
```

注意：

- `.env` 已经被 `.gitignore` 忽略，不要提交。
- API key 不会写入 `.ai/` 产物、测试快照或日志。
- 如果 `.env` 中有 `DEEPSEEK_API_KEY`，真实 DeepSeek smoke test 会实际请求 DeepSeek。
- 如果没有 key，DeepSeek smoke test 会跳过，fixture 测试仍然可以跑。

## 3. 用内置 fixture 快速体验

项目内置两个最小 fixture：

- `tests/fixtures/mini-spring-boot`
- `tests/fixtures/mini-dotnet-webapi`

### 3.1 初始化 Java fixture

```bash
.venv/bin/harness-builder-agent init --repo tests/fixtures/mini-spring-boot
```

执行后会生成：

```text
tests/fixtures/mini-spring-boot/.ai/
  project-inventory.json
  command-catalog.yaml
  harness-config.yaml
  scan-report.md
  maturity-report.md
  evolution-plan.md
  guides/
  sensors/
  experience/
```

### 3.2 跑 Java fixture 的任务闭环

```bash
.venv/bin/harness-builder-agent run --repo tests/fixtures/mini-spring-boot "修复登录接口错误提示不一致的问题"
```

执行后会生成：

```text
tests/fixtures/mini-spring-boot/.ai/task-runs/demo-task-001/
  harness-map.yaml
  sensor-report.yaml
  decision-log.md
  handoff-summary.md
  experience-candidates.md
```

### 3.3 对 Java fixture 做 benchmark

```bash
.venv/bin/harness-builder-agent benchmark --repo tests/fixtures/mini-spring-boot --profile java-spring
```

成功时会输出：

```text
Benchmark passed for tests/fixtures/mini-spring-boot
```

### 3.4 .NET fixture 命令

```bash
.venv/bin/harness-builder-agent init --repo tests/fixtures/mini-dotnet-webapi
.venv/bin/harness-builder-agent run --repo tests/fixtures/mini-dotnet-webapi "调整 Catalog 相关低风险文案"
.venv/bin/harness-builder-agent benchmark --repo tests/fixtures/mini-dotnet-webapi --profile dotnet-aspnet
```

## 4. 用真实开源仓库体验

真实仓库放在本地 ignored 目录 `.benchmarks/`，不会提交到 Git。

### 4.1 拉取两个真实仓库

```bash
mkdir -p .benchmarks
git clone --depth 1 https://github.com/yangzongzhuan/RuoYi-Vue.git .benchmarks/RuoYi-Vue
git clone --depth 1 https://github.com/dotnet-architecture/eShopOnWeb.git .benchmarks/eShopOnWeb
```

如果目录已经存在，可以跳过 clone。

### 4.2 在 RuoYi-Vue 上跑完整闭环

```bash
.venv/bin/harness-builder-agent init --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent run --repo .benchmarks/RuoYi-Vue "修复登录接口错误提示不一致的问题"
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/RuoYi-Vue --profile java-spring
```

检查关键产物：

```bash
find .benchmarks/RuoYi-Vue/.ai -maxdepth 3 -type f | sort
```

应该能看到项目级产物：

- `.ai/project-inventory.json`
- `.ai/command-catalog.yaml`
- `.ai/harness-config.yaml`
- `.ai/scan-report.md`
- `.ai/maturity-report.md`
- `.ai/evolution-plan.md`
- `.ai/guides/project-context.md`
- `.ai/guides/coding-rules.md`
- `.ai/guides/architecture.md`
- `.ai/guides/task-templates/bugfix.md`
- `.ai/guides/task-templates/lightweight-feature.md`
- `.ai/sensors/verification.md`
- `.ai/sensors/test-strategy.md`
- `.ai/benchmark-report.yaml`

也应该能看到任务级产物：

- `.ai/task-runs/demo-task-001/harness-map.yaml`
- `.ai/task-runs/demo-task-001/sensor-report.yaml`
- `.ai/task-runs/demo-task-001/decision-log.md`
- `.ai/task-runs/demo-task-001/handoff-summary.md`
- `.ai/task-runs/demo-task-001/experience-candidates.md`

### 4.3 在 eShopOnWeb 上跑完整闭环

```bash
.venv/bin/harness-builder-agent init --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent run --repo .benchmarks/eShopOnWeb "调整 Catalog 相关低风险文案"
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/eShopOnWeb --profile dotnet-aspnet
```

检查关键产物：

```bash
find .benchmarks/eShopOnWeb/.ai -maxdepth 3 -type f | sort
```

产物结构应与 RuoYi-Vue 保持一致，技术栈差异进入 inventory、command catalog 和 guide 内容中。

## 5. 输出文件怎么看

### 5.1 `project-inventory.json`

记录扫描得到的项目事实，例如：

- 仓库名
- 主技术栈
- 技术栈列表
- 模块列表
- 证据来源
- 配置文件、文档、CI 文件候选

### 5.2 `command-catalog.yaml`

记录可执行命令候选，例如：

- `mvn test`
- `mvn package`
- `dotnet test`
- `dotnet build`

每条命令会带上：

- `id`
- `type`
- `gate`
- `source`
- `confidence`
- `verified`

### 5.3 `harness-config.yaml`

定义 POC 阶段支持的 workflow：

- `lightweight`
- `bugfix`

也定义 Sensor runtime 的最小策略，例如失败后是否只重跑失败项、最大修复尝试次数等。

### 5.4 `guides/`

给 AI Coding Agent 使用的项目知识和约束，包括：

- `project-context.md`
- `coding-rules.md`
- `architecture.md`
- `task-templates/bugfix.md`
- `task-templates/lightweight-feature.md`

这些文件目前都是候选态，需要人类审查后再提升为正式规则。

### 5.5 `sensors/`

记录验证策略：

- `verification.md`
- `test-strategy.md`

POC 会根据扫描到的命令生成最小验证说明。

### 5.6 `task-runs/demo-task-001/`

一次任务闭环的输出目录：

- `harness-map.yaml`：任务类型、workflow、相关 guides、sensor policy。
- `sensor-report.yaml`：Sensor 执行结果，可能是 `passed`、`failed` 或 `skipped`。
- `decision-log.md`：本次任务的关键决策。
- `handoff-summary.md`：交接摘要和剩余风险。
- `experience-candidates.md`：经验候选，不会自动进入正式规则。

## 6. 跑测试和验收

### 6.1 全量测试

```bash
.venv/bin/python -m pytest -q
```

### 6.2 端到端测试

```bash
.venv/bin/python -m pytest tests/e2e -q
```

这会覆盖：

- fixture 端到端测试
- 真实 DeepSeek smoke test
- 真实仓库 E2E 测试

如果 `.env` 有 `DEEPSEEK_API_KEY`，DeepSeek smoke test 会实际请求 DeepSeek。

### 6.3 只跑真实仓库 E2E

```bash
.venv/bin/python -m pytest tests/e2e/test_real_repositories_e2e.py -q
```

这个测试会对 RuoYi-Vue 和 eShopOnWeb 都执行：

```text
init -> run -> benchmark
```

并检查 benchmark report 和任务级 workflow 产物。

### 6.4 只跑 DeepSeek smoke

```bash
.venv/bin/python -m pytest tests/e2e/test_real_llm_smoke.py -q
```

有 key 时会实际请求 DeepSeek；没有 key 时会跳过。

## 7. 常见问题

### 7.1 为什么 Sensor 是 skipped 或 failed？

POC 会尝试运行扫描出的低风险命令。例如 Java 项目可能尝试 `mvn test`，.NET 项目可能尝试 `dotnet test`。

如果本机没有安装 `mvn`、`dotnet`，或者目标项目依赖不完整，`sensor-report.yaml` 会记录 `skipped` 或 `failed`，但任务闭环仍会生成结构化失败摘要。这符合 POC 边界：首轮验证控制闭环，不强制真实修复业务代码。

### 7.2 会不会真的修改业务代码？

不会。当前 POC 的 `run` 命令只生成任务级 Harness 控制资产和交接文档，不自动修改目标仓库业务代码。

### 7.3 `.ai/` 要提交吗？

默认不提交。`.ai/` 是目标项目的生成产物，当前仓库已把 `.ai/` 加入 `.gitignore`。

### 7.4 `.benchmarks/` 要提交吗？

不要提交。`.benchmarks/` 里是克隆下来的真实开源仓库，已经被 `.gitignore` 忽略。

### 7.5 为什么真实仓库 E2E 需要先 clone？

因为 POC 要证明 Harness Builder 能处理真实仓库，而不是只处理人工构造的 fixture。真实仓库 E2E 使用：

- RuoYi-Vue：Java / Spring Boot / Vue
- eShopOnWeb：.NET / ASP.NET Core

### 7.6 如何清理生成产物？

```bash
rm -rf tests/fixtures/mini-spring-boot/.ai
rm -rf tests/fixtures/mini-dotnet-webapi/.ai
rm -rf .benchmarks/RuoYi-Vue/.ai
rm -rf .benchmarks/eShopOnWeb/.ai
```

如果要彻底清理真实仓库：

```bash
rm -rf .benchmarks
```

## 8. 当前 POC 边界

当前已经实现：

- 本地 CLI
- Java / .NET fixture 扫描
- 真实仓库扫描
- `.ai/` Harness 资产生成
- 任务级控制闭环
- fixture E2E
- 真实仓库 E2E
- DeepSeek smoke test

当前没有实现：

- IDE 插件
- Web UI / Dashboard
- 完整 Self-Improve
- 自动修改业务代码
- 高风险任务无人值守执行
- 复杂可组合 Workflow Toolkit

这些内容属于后续 MVP 或产品化阶段。
