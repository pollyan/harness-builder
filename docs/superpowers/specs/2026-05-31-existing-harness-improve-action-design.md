# Existing Harness Improve Action Design

## 背景

Harness Builder 的长期目标是 Maturity-driven Self-Improve AI Coding Harness Builder。当前首次 `init` 已能建立成熟度基线，再次 guided `init` 已能识别已有 Harness，并支持 `exit`、`assess` 和 `reinit`。`docs/todos/maturity-driven-init-wizard.md` 仍要求已有 Harness 维护入口能引导用户查看下一步改进建议、处理候选和运行 benchmark，而不是要求用户记住底层命令顺序。

本轮选择把 `improve` 接入已有 Harness 的 guided `init` 菜单，让用户从主入口生成 review-only 改进候选。

## Current State Gap Analysis

| 候选 gap | 目标态要求 | 当前能力 | 缺口 | 价值 | 风险 / 复杂度 | 本轮决策 |
| --- | --- | --- | --- | --- | --- | --- |
| Existing Harness `improve` action | 再次 `init` 能进入成熟度驱动改进建议 | 底层 `improve` 能生成 `improvement-candidates.yaml`、`evolution-plan.md`、`pending-improvements.md` | guided `init` 不能编排该能力 | 把成熟度缺口转成 review-only 候选，最贴近 Self-Improve 主线 | 确定性、无 LLM、不改正式资产 | 本轮实现 |
| Existing Harness `benchmark` action | 再次 `init` 能运行质量门禁 | 底层 `benchmark` 已存在 | guided `init` 尚未接入 | 质量健康度强，但更偏验证而非改进生成 | 会触发 benchmark 编排，耗时和失败路径更多 | 暂缓 |
| 查看下一步建议 | 用户能直接阅读推荐路线 | `init-summary.md`、`evolution-plan.md` 已存在 | guided `init` 只显示状态摘要 | 低风险 | 仅打印文件摘要，独立产品价值较弱 | 暂缓 |
| 处理候选 | 用户能采纳/拒绝候选 | `review-candidate` 已存在 | 需要候选选择、决策和 rationale 交互 | 接管闭环强 | 交互状态、schema 和应用风险更大 | 等 `improve` 菜单先生成候选后再做 |
| 重新扫描更新建议 | 已有 Harness 能发现代码库变化 | `reinit` 会重新生成 | 缺少只生成更新候选 / diff 的安全路径 | 价值高 | 正式资产覆盖和 candidate diff 设计较大 | 暂缓 |

## 目标

- 现有 Harness 的 guided `init` 菜单新增 `improve` 动作。
- 用户选择 `improve` 后，先刷新 Experience index，再复用 `assess_maturity(repo)` 刷新成熟度，然后复用 `generate_improvements(repo)` 生成 review-only 改进候选：
  - `.ai/maturity-score.yaml`
  - `.ai/maturity-report.md`
  - `.ai/maturity-evidence.yaml`
  - `.ai/init-summary.md`
  - `.ai/improvement-candidates.yaml`
  - `.ai/evolution-plan.md`
  - `.ai/experience/pending-improvements.md`
  - `.ai/experience/experience-index.yaml`
- CLI 输出展示 top candidate 摘要，包括候选 id、priority、target dimension 和 suggested target。
- 该动作不重新扫描、不调用 LLM、不覆盖正式 Guides、Sensors、Workflow Skills、`harness-config.yaml` 或 `project-inventory.json`。
- `init` trace 记录 `existing_harness_action: improve` 和生成产物。

## 决策

- `improve` 比 `benchmark` 更适合作为 `assess` 后的下一步，因为它直接把成熟度缺口变成可审查候选，推进 Experience & Self-Improve 闭环。
- Guided `improve` 主动刷新 Experience index 和成熟度，而不是仅在 maturity 文件缺失时复评。维护入口面向普通用户，默认应生成基于当前 Harness 状态的建议。
- 本轮不执行 `self-improve`、LLM maturity review 或 asset candidate generation；那些仍保持专家命令和后续切片。
- 本轮只生成候选，不应用候选。正式 Harness 资产自动更新仍必须经过候选治理。
- `--non-interactive` 语义不变，仍按自动化重新生成 Harness。

## 用户可见行为

已有 Harness 菜单展示：

```text
- improve：基于成熟度缺口生成 review-only 改进候选，不覆盖正式 Harness 资产。
```

用户输入 `improve`、`建议` 或 `改进` 后输出：

```text
正在生成成熟度驱动的改进候选...
改进候选已生成。
优先候选：`maturity-next-step-...`（priority=high，dimension=sensors，target=`.ai/sensors/verification.md`）
- `.ai/improvement-candidates.yaml`
- `.ai/evolution-plan.md`
- `.ai/experience/pending-improvements.md`
- `.ai/experience/experience-index.yaml`
```

随后 CLI 继续打印 refreshed completion summary。

## 验收标准

- Integration：先 `init --non-interactive` 生成 Harness，再 guided `init` 输入 `improve`，命令成功。
- 测试证明该路径不调用 guided init 的扫描函数。
- 测试证明 `project-inventory.json`、`harness-config.yaml`、代表性 Guide、Sensor、Workflow Skill 未被覆盖。
- 测试证明 `improvement-candidates.yaml` 通过 `ImprovementCandidateReport` schema，并且候选保持 `human_confirmation_required: true`、`suggested_target` 指向 `.ai/`，CLI 输出包含 top candidate 摘要。
- 测试证明 `pending-improvements.md` 包含稳定章节和 acceptance checks，`experience-index.yaml` 统计 pending improvements。
- 测试证明当 review-only workflow recommendation 已存在但 index/evidence 过期时，guided `improve` 会刷新 Experience index 和 maturity evidence，并生成 `experience-workflow-recommendation-review` 候选。
- 测试证明最新 init trace 为 `completed`，summary 包含 `existing_harness_action: improve`，artifacts 包含 maturity、init summary、improvement candidates、evolution plan、pending improvements、experience index。
- 更新 README、init workflow 工程规则、todo 和 evolution log。

## 风险

- `generate_improvements` 会重写 `evolution-plan.md` 和 `pending-improvements.md`。这符合 review-only 改进候选生成语义，但会覆盖人工编辑的 pending Markdown；本轮保持现有底层命令行为，不扩大为合并策略重构。
- Guided `improve` 主动调用 `write_experience_index` 和 `assess_maturity`；已有 Harness 入口已验证核心 Harness 文件存在，因此不会依赖缺失 Harness 的自动扫描兼容路径。
