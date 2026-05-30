# 测试策略

本文定义 Harness Builder 自身的测试分层、职责、断言深度和运行策略。修改测试、fixture、CI、acceptance 或断言前，先阅读本文。

## 测试目标

Harness Builder 的测试不仅要证明代码能跑，还要证明生成的 Harness 有最低可用质量。

测试需要回答：

- CLI 命令是否能正确串联主流程。
- LLM 输出是否被严格校验。
- 生成文件是否结构正确、内容足够、引用有效。
- Sensor 和 benchmark 是否能暴露真实失败。
- Java Spring 和 .NET ASP.NET 这两个 POC 技术栈是否被覆盖。

## 测试分层

| 层级 | 目录或命令 | 职责 | 是否默认 CI |
| --- | --- | --- | --- |
| Unit | `tests/unit/` | 单函数、schema、边界条件、错误处理 | 是 |
| Integration | `tests/integration/` | CLI 与多个模块协作，通常使用 mock LLM | 是 |
| E2E fixture | `tests/e2e/` | 本地 fixture 仓库完整链路 | 是 |
| Acceptance | `tests/acceptance/` | 真实 DeepSeek、真实开源仓库验收 | 否 |
| Benchmark | `harness-builder-agent benchmark` | 对生成 Harness 做质量验收 | 间接覆盖 |

快速回归命令：

```bash
scripts/test-fast.sh
```

真实 acceptance 需要显式运行：

```bash
scripts/test-acceptance.sh
```

完整本地验收：

```bash
scripts/test-full.sh
```

## Unit 测试职责

Unit 测试应该覆盖单个模块的确定性行为。

应覆盖：

- Pydantic schema 正向和反向校验。
- evidence collector 的事实收集。
- LLM scan analyzer 的 JSON 解析和错误处理。
- scan reconciler 的冲突处理和置信度处理。
- weapon library 的选择逻辑。
- generation trace 的事件和 artifact 记录。
- sensor runner 的状态判断。
- human confirmation 的 questionnaire 生成。

Unit 测试不应该：

- 依赖真实 DeepSeek。
- 依赖真实开源仓库。
- 依赖本地未清理状态。

## Integration 测试职责

Integration 测试验证多个模块一起工作，尤其是 CLI 命令。

应覆盖：

- `init` 能基于 mock LLM 为 Java fixture 生成完整资产。
- `init` 能基于 mock LLM 为 .NET fixture 生成完整资产。
- `run` 能选择 workflow、生成 harness map、sensor report 和 runtime summary。
- `assess` 能生成成熟度评估。
- `improve` 能生成改进候选。
- `benchmark` 能检查核心文件、schema、trace、guide/sensor 内容和 hard gate。

Integration 测试可以 mock LLM，但不能弱化产物断言。

## E2E fixture 测试职责

E2E fixture 使用本地小型项目模拟真实仓库。

应覆盖：

- Java Spring fixture。
- .NET ASP.NET fixture。
- unknown stack 或 minimal repo 的边界情况。
- 从 `init` 到 `run` 的完整链路。

E2E 重点不是测试 DeepSeek，而是测试工具链在可控项目上的端到端行为。

## Acceptance 测试职责

Acceptance 使用真实 DeepSeek 和真实开源仓库，验证 POC 在真实场景下可运行。

当前重点：

- `RuoYi-Vue` 对应 `java-spring`。
- `eShopOnWeb` 对应 `dotnet-aspnet`。
- 跑通 `init/run/assess/improve/benchmark`。
- benchmark passed 时必须真的通过。
- benchmark failed 时必须有明确 hard gate 失败项和摘要。

规则：

- Acceptance 不进入默认 CI。
- Acceptance 缺少 `DEEPSEEK_API_KEY` 必须失败，不能 skip。
- Acceptance 可以耗时更长，但必须能说明真实验收价值。

## 断言深度要求

文件生成类测试不能只断言文件存在。

每个新增机器消费文件至少断言：

- 文件存在。
- schema 可解析。
- 必填字段存在。
- 关键字段值正确。
- 与其他文件的引用有效。

每个新增 Markdown 文件至少断言：

- 文件存在。
- 必需章节存在。
- 当前 stack 相关内容存在。
- 有来源证据或事实依据。
- 有人工确认点或风险说明。

每个新增 workflow skill 至少断言：

- `SKILL.md` 存在。
- 标题或核心名称正确。
- 被 `harness-config` 或 `harness-map` 引用。
- 引用路径真实存在。

每个新增 sensor 至少断言：

- 包含已发现验证命令。
- 包含缺失验证能力。
- 包含推荐验证活动。
- 包含失败处理策略。
- hard/advisory 语义清楚。

## 针对 init 的最低覆盖

修改 `init` 主链路时，至少检查：

- Java Spring fixture。
- .NET ASP.NET fixture。
- 默认 guided init happy path。
- 非 TTY 未显式传 `--non-interactive` 时失败。
- `--non-interactive` 自动化兼容。
- `--context` 输入。
- `--context` 和交互输入进入 generated guides。
- `interaction-decisions.yaml` schema 和 trace artifact。
- `project-inventory.json` schema。
- `command-catalog.yaml` schema。
- `llm-scan-proposal.json` schema。
- `weapon-library-selection.yaml` schema 和内容。
- guide 必需章节。
- sensor 必需章节。
- skill 模板复制和引用。
- generation trace 阶段和 artifact。
- benchmark 检查项。

## 针对 LLM 的最低覆盖

修改 LLM 行为时，至少检查：

- mock LLM 成功路径。
- 非法 JSON。
- schema 缺字段。
- stack 与 evidence 冲突。
- low confidence 或 unknown stack。
- DeepSeek 真实 acceptance。

## 针对 benchmark 的最低覆盖

修改 benchmark 时，至少检查：

- 缺文件能失败。
- schema 错误能失败。
- 必需章节缺失能失败。
- workflow skill 引用错误能失败。
- hard gate failed/skipped 能被报告。
- 报告自身符合 `BenchmarkReport` schema。

## CI 策略

当前 CI 应运行快速回归：

```bash
python -m pytest -q
```

CI 不应默认运行真实 DeepSeek acceptance，原因：

- 需要 API key。
- 耗时和网络稳定性不可控。
- 真实开源仓库 fixture 不应作为默认 CI 必备依赖。

但 Codex push 到 GitHub 前、目标模式完成前和重要发布前应运行 acceptance。

本地 Git hooks 作为兜底保护：

- `pre-commit`：运行 `scripts/test-fast.sh`。
- `pre-push`：运行 `scripts/test-full.sh`。
- `post-commit`：提醒 push 后运行 `scripts/check-ci.sh`。

Codex 侧的强制规则不依赖 Git hook：创建 commit 前必须主动运行 `scripts/test-fast.sh`；push 前必须主动运行 `scripts/test-full.sh`；push 完成后必须主动运行 `scripts/check-ci.sh` 查看 GitHub Actions 结果。这样小步 commit 保持快速反馈，真实 DeepSeek / 开源仓库 acceptance 仍在代码进入 GitHub 前作为硬验收。Git 没有标准 `post-push` hook，因此远端 CI 状态检查由 Codex 工作流规则保证。

如果缺少 `DEEPSEEK_API_KEY`、真实 benchmark 仓库、网络或 API 可用性，acceptance 必须失败并暴露原因，不能跳过。

## 测试命名和维护

规则：

- 测试名应表达业务行为，而不是实现细节。
- fixture 应尽量小，但要保留真实技术栈特征。
- 不再使用的旧扫描器、旧逻辑和旧测试应删除，避免误导。
- 测试失败信息应能定位缺失字段、缺失章节或错误引用。
