# JiuwenSwarm Auto-Harness 调研

调研对象：

- GitHub: `https://github.com/openJiuwen-ai/jiuwenswarm`
- 关联核心库: `https://github.com/openJiuwen-ai/agent-core`
- 公开介绍页: `https://openjiuwen.com/`

调研日期：2026-05-30

## 结论摘要

JiuwenSwarm 的 Auto-Harness 不是一个“扫描项目后生成 Guides/Sensors/Workflow 文件”的工具，而是一个运行在 JiuwenSwarm 宿主 Agent 内的自动扩展生成系统。它的核心目标是根据用户提出的优化目标，生成可热加载的 runtime extension package，并可进一步走提交 PR 的自演进流程。

它对我们的最大启发不是直接照搬其多 Agent 或 UI，而是以下三点：

- Harness 产物可以从静态 `.ai` 文件升级为可安装、可启用、可回滚、可导入导出的 package。
- Benchmark 不应只验证“文件存在”，还应验证产物能被真实 runtime 加载、注册和调用。
- 自演进可以拆成两层：项目级 Guides/Sensors 的确定性生成，和运行时能力扩展的受控生成。

## JiuwenSwarm 的机制

### 1. 产品入口

JiuwenSwarm 在 Slash 命令中暴露 `/auto-harness`，包含一次性执行和定时任务两类入口。

它支持两种 Pipeline：

- `optimize_expert_harness`，后端值为 `extended_evolve_pipeline`，用于生成本地 harness extension package。
- `optimize_meta_harness`，后端值为 `meta_evolve_pipeline`，用于提交优化 PR，需要 git 配置。

证据：

- `/private/tmp/jiuwenswarm/docs/zh/Slash命令表.md:710`
- `/private/tmp/jiuwenswarm/docs/zh/Slash命令表.md:714`
- `/private/tmp/jiuwenswarm/docs/zh/Slash命令表.md:736`

### 2. JiuwenSwarm 负责集成外壳

`jiuwenswarm` 本体的 `AutoHarnessService` 做这些事情：

- 初始化 `~/.jiuwenswarm/auto-harness` 下的数据目录、repo 缓存、经验目录和运行日志目录。
- 从配置中读取目标仓库 URL，而不是每次从命令行传入。
- clone / update 目标仓库到本地缓存。
- 构造 `AutoHarnessConfig`，并调用 `create_auto_harness_orchestrator()`。
- 管理 active run、流式事件、取消、定时任务、package 元数据、导入导出、激活和去激活。

证据：

- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/service.py:218`
- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/service.py:1267`
- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/service.py:1292`
- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/service.py:1317`
- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/service.py:1878`
- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/service.py:1997`

### 3. agent-core 负责 Auto-Harness 核心 Pipeline

真正的自动检测、设计、实现、验证在 `agent-core/openjiuwen/auto_harness`。

`extended_evolve_pipeline` 的阶段是：

1. `assess`：评估扩展缺口。
2. `plan`：设计扩展方案。
3. `build_verify`：实现和验证扩展。
4. `activate`：激活扩展。

证据：

- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/pipelines/extended_evolve_pipeline/extended_evolve_pipeline.py:56`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/pipelines/extended_evolve_pipeline/extended_evolve_pipeline.py:65`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/pipelines/extended_evolve_pipeline/extended_evolve_pipeline.py:85`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/pipelines/extended_evolve_pipeline/extended_evolve_pipeline.py:101`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/pipelines/extended_evolve_pipeline/extended_evolve_pipeline.py:152`

`meta_evolve_pipeline` 的阶段是：

1. `assess`
2. `plan`
3. `implement`
4. `verify`
5. `commit`
6. `publish`
7. `learnings`

证据：

- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/pipelines/meta_evolve_pipeline/meta_evolve_pipeline.py:43`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/pipelines/meta_evolve_pipeline/meta_evolve_pipeline.py:49`

### 4. 它生成的是 runtime extension

Auto-Harness 的核心结构是 `ExtensionDesign` 和 `RuntimeExtensionArtifact`。

`ExtensionDesign` 里包含：

- `gap_id`
- `extension_name`
- `kind`
- `depends_on`
- `applies_to`
- `components`
- `file_plan`
- `harness_config_patch`

这些字段说明它的目标是把缺口转化成一个自包含的扩展包，而不是只写 Markdown 规则。

证据：

- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/schema.py:235`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/schema.py:277`

`design_ext` skill 明确要求每个扩展通过 `harness_config.yaml` 声明组件，并允许包含三类组件：

- Rail：拦截与流程控制。
- Tool：可调用动作。
- Skill：知识注入与流程指导。

证据：

- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/skills/design_ext/SKILL.md:20`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/skills/design_ext/SKILL.md:42`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/skills/design_ext/SKILL.md:147`

### 5. 验证机制更偏 runtime acceptance

它的 `verify_ext` 不满足于 import 成功，而是分层验证：

- L1：结构校验，检查 `harness_config.yaml`、module/class、Skill 目录等。
- L2：创建临时 `DeepAgent`，调用真实 `load_harness_config(config_path)`。
- L3：运行时验收，验证 tool 注册、tool 输出、rail 副作用、skill 加载。
- 对文件产物类 Tool，还要求真实文件存在、格式有效、大小大于 0。

代码里对应：

- `ExtendVerifyStage` 最多做 3 次静态修复重试。
- 通过 `run_static_checks_against_runtime()` 做结构/静态检查。
- 生成 pytest 验收测试并复跑。
- 验收通过后才 `promote_runtime()`。

证据：

- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/stages/verify.py:384`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/stages/verify.py:403`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/stages/verify.py:472`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/stages/verify.py:517`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/skills/verify_ext/SKILL.md:19`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/skills/verify_ext/SKILL.md:39`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/skills/verify_ext/SKILL.md:58`
- `/private/tmp/openjiuwen-agent-core/openjiuwen/auto_harness/skills/verify_ext/SKILL.md:126`

### 6. 它有 package 生命周期管理

JiuwenSwarm 会维护 `harness-packages.json`，记录 native agent、已生成 package、active package ids、runtime path、config path 等。

这意味着用户可以看到、激活、去激活、删除、导入、导出 harness package。

证据：

- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/service.py:1878`
- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/service.py:1908`
- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/service.py:1997`

### 7. 它有定时自演进

`/auto-harness schedule` 可以按 1/2/4/8/12/24 小时执行定时任务。服务端有 `Scheduler` 和 `TaskStore`，用 JSON 文件记录任务和执行日志。

这说明它把 Auto-Harness 当成持续运行的优化机制，而不是一次性初始化命令。

证据：

- `/private/tmp/jiuwenswarm/docs/zh/Slash命令表.md:756`
- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/task_store.py:1`
- `/private/tmp/jiuwenswarm/jiuwenswarm/agents/harness/common/auto_harness/scheduler.py:1`

## 和我们当前 POC 的对比

### 我们当前做法

当前 Harness Builder POC 是一个 CLI，核心路径是：

1. 扫描目标仓库，生成 `project-inventory.json` 和 `command-catalog.yaml`。
2. 按技术栈从内置武器库选择 Guides / Sensors。
3. 写出 `.ai` 目录，包括 Guides、Sensors、Workflow Skills、成熟度、演进计划。
4. 通过 benchmark 校验文件存在、schema、内容引用和真实 fixture / benchmark 流程。

证据：

- `/Users/anhui/Documents/myProgram/harness-builder/src/harness_builder_agent/tools/write_assets.py:30`
- `/Users/anhui/Documents/myProgram/harness-builder/src/harness_builder_agent/tools/write_assets.py:38`
- `/Users/anhui/Documents/myProgram/harness-builder/src/harness_builder_agent/tools/write_assets.py:45`
- `/Users/anhui/Documents/myProgram/harness-builder/src/harness_builder_agent/tools/write_assets.py:51`
- `/Users/anhui/Documents/myProgram/harness-builder/src/harness_builder_agent/tools/benchmark.py:23`
- `/Users/anhui/Documents/myProgram/harness-builder/src/harness_builder_agent/tools/benchmark.py:95`
- `/Users/anhui/Documents/myProgram/harness-builder/src/harness_builder_agent/tools/benchmark.py:188`

我们刚补的武器库解决了“每次生成不稳定”的问题。武器库按 `common + primary_stack` 选择，Java Spring 和 .NET ASP.NET 有稳定条目。

证据：

- `/Users/anhui/Documents/myProgram/harness-builder/src/harness_builder_agent/tools/weapon_library.py:8`
- `/Users/anhui/Documents/myProgram/harness-builder/src/harness_builder_agent/tools/weapon_library.py:138`

### 关键差异

| 维度 | JiuwenSwarm Auto-Harness | 我们当前 POC |
|---|---|---|
| 产物形态 | runtime extension package | `.ai` 静态资产 |
| 生成内容 | Rail / Tool / Skill / harness_config | Guides / Sensors / Workflow Skills |
| 触发方式 | `/auto-harness run`、schedule | CLI 命令 |
| 验证方式 | 静态检查 + 热加载 + pytest acceptance | schema + 内容 + benchmark 流程 |
| 生命周期 | package 管理、激活、去激活、导入导出 | 文件生成，暂不管理版本激活 |
| 自演进 | 定时任务 + meta pipeline + PR | maturity / improve 初步产物 |
| 风险控制 | worktree、CI gate、fix loop、回滚 | hard gate / benchmark，尚无自动修复循环 |

## 可以借鉴的点

### P0：把当前 `.ai` 产物包装成 Harness Package

建议增加 `.ai/harness-package.yaml` 或 `.ai/package-manifest.yaml`：

```yaml
schema_version: harness_package.v0.1
package_id: <repo>-<timestamp>
repo_name: ...
primary_stack: ...
assets:
  guides:
    - guides/project-context.md
  sensors:
    - sensors/verification.md
  skills:
    - skills/lightweight/SKILL.md
    - skills/bugfix/SKILL.md
  reports:
    - maturity-score.yaml
    - benchmark-report.yaml
activation:
  type: file_based
  entrypoints:
    workflow_skills:
      - .ai/skills/lightweight/SKILL.md
      - .ai/skills/bugfix/SKILL.md
```

这一步不要求我们拥有 JiuwenSwarm 那样的 runtime，但可以先把产物变成“可安装、可审计、可版本化”的包。

### P0：Benchmark 增加 package-level 验收

我们现在已经验证 `.ai` 内文件存在、schema 和内容引用。下一步应增加：

- `schema:harness-package`
- `content:harness-package-assets-resolve`
- `content:workflow-skills-loadable`
- `content:sensors-hard-gates-map-to-commands`

这样可以从“生成了文件”升级到“生成了一个完整 package”。

### P1：引入 runtime acceptance 测试思想

JiuwenSwarm 的 `verify_ext` 最大价值是把验证分成 L1/L2/L3。我们可以迁移这个思想：

- L1：Markdown/YAML/JSON schema 和路径完整性。
- L2：Workflow Skill 可被 Skill loader 解析，frontmatter / description / body 合法。
- L3：拿真实开源仓库执行一次 `init -> run -> assess -> improve -> benchmark`，并检查 task-run 中是否真的引用了对应 Guide、Sensor、Workflow Skill。

这和我们当前 benchmark 很接近，但可以更明确分层。

### P1：引入 artifact-level Sensor

JiuwenSwarm 对 PPTX/DOCX/PDF/JSON 这类产物要求验证真实文件格式。我们可以把这个思想抽象为 Sensor 类型：

- `command_sensor`
- `artifact_sensor`
- `schema_sensor`
- `workflow_sensor`
- `human_confirmation_sensor`

这会让 Sensors 不再只是命令列表，而是能表达“真实产物是否成立”的验收活动。

### P1：增加 Harness Package 生命周期命令

建议 CLI 后续增加：

- `harness-builder-agent package --repo <path>`
- `harness-builder-agent package list --repo <path>`
- `harness-builder-agent package activate --repo <path> <package_id>`
- `harness-builder-agent package export --repo <path> <package_id>`

POC 可以先实现本地 `.ai/packages/`，不急着做 UI。

### P2：自演进从 improve 升级为可执行闭环

我们已有 `improvement-candidates.yaml`，但还没有“采纳候选改进并更新 Harness”的命令。可以借鉴 JiuwenSwarm 的 schedule / evolve 思路，设计：

- `harness-builder-agent improve --repo <path>`：生成候选。
- `harness-builder-agent apply-improvement --repo <path> <candidate_id>`：把候选升级为 Guide/Sensor/Weapon Library patch。
- `harness-builder-agent benchmark --repo <path>`：验证升级结果。

### P2：不要现在照搬动态扩展生成

JiuwenSwarm 的 runtime extension 依赖宿主 Agent 的 `load_harness_config()`、Rail/Tool/Skill 插件体系和热加载能力。我们现在的目标是 AI Coding 项目的 harness builder，当前 POC 先做静态可见、可编辑、可 benchmark 的 `.ai` 资产更稳。

动态生成 Tool/Rail 可以作为后续版本，不应进入当前 POC 的主路径。

## 建议更新到我们的 POC Roadmap

建议分三步：

1. POC 当前阶段：保留 deterministic weapon library，新增 package manifest 和 package-level benchmark。
2. POC+1：把 Sensors 分层，补 artifact/schema/workflow/human confirmation sensor。
3. POC+2：引入 apply-improvement 和 package lifecycle，形成可回滚、可导出、可演进的 Harness Package。

## 对目标模式提示词的影响

如果下一轮要让目标模式继续实现，建议目标不写成“照着 JiuwenSwarm 做 Auto-Harness”，而写成：

> 基于当前 Harness Builder POC，借鉴 JiuwenSwarm Auto-Harness 的 package lifecycle 和 runtime acceptance 思想，新增本地 Harness Package manifest、package-level benchmark、分层 Sensor 类型设计文档和最小 CLI package 命令。不得引入宿主 Agent 热加载和动态 Rail/Tool 生成，保持当前 POC 的静态 `.ai` 产物和确定性武器库路线。

这个范围既吸收了它的优点，又不会把我们的 POC 带偏到完整 Agent 平台。
