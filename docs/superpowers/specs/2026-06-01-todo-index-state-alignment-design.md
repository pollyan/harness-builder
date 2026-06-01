# Todo 索引状态对齐设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`docs/todos/archive.md`、`docs/todos/local-unique-capability-migration.md`、`docs/todos/guided-init-ai4se-real-repo-findings.md`、`docs/todos/maturity-driven-init-wizard.md` 和当前 git 状态。
- 按需未展开：`docs/engineering/init-workflow.md`、`llm-contracts.md`、`sensor-and-gate-rules.md`；本轮不修改 `init` 行为、LLM 契约、benchmark 或 Runtime 分工，只收敛 todo 事实源。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. `docs/todos` 索引与文件状态对齐 | 用户追问 / Self-Harness Gate | Maintainer 能从 `docs/todos/README.md` 直接判断当前 open todo，不被历史文件数量误导 | README 写着当前待办暂无，多个历史文件内写 `implemented` 或 `paused` | README 管理规则仍说“已完成条目移动到 archive.md”，但实际是文件留存 + archive 索引；两个 paused 文件还指向已经完成的迁移 todo，且 ai4se 文档保留“剩余 open”措辞 | 降低目标模式选题误判，保护 todo 优先规则和合并工作包判断 | 低；文档收敛，不碰代码或 schema | `rg` 检查状态、文档 diff、`scripts/test-fast.sh` | 无外部凭证；push 仍依赖 full acceptance 前置 | README 明确 open/paused/implemented 索引，过期迁移引用移除，fast regression 通过 | 本轮 |
| B. push 68 个本地提交 | 用户最新提醒 / Git 状态 | 有独立价值的本地工作包应同步 GitHub | 本地 `main` 相对 `origin/main` ahead 68 / behind 0，fast 阶段通过 | `scripts/test-full.sh` acceptance 因缺 `DEEPSEEK_API_KEY` 和 `.benchmarks` 真实仓库失败，按规则不能 push | 让远端获得已完成迁移和 init 增强 | 中；需要外部凭证和真实仓库 | `scripts/test-full.sh`、`git push` | DeepSeek key、`.benchmarks/RuoYi-Vue`、`.benchmarks/eShopOnWeb` | full regression 通过后 push | 外部前置满足后处理 |
| C. Existing Harness action runner 失败 trace 全量保真 | 上一轮 Gate / 新发现 | 所有已有 Harness 维护动作失败都保留 action-specific trace | 已修复 `review-candidate` 早期候选预检失败 | 其他 action 分支仍可能写完 action-specific failed trace 后被顶层 `init` 泛化覆盖 | 提升维护入口审计可信度 | 中；触碰 CLI 失败行为和 integration tests | guided integration failure-path tests | 无外部凭证 | 失败路径 trace summary 保留 action / id / decision | 下一轮候选 |

排序结论：

1. 选择 A，因为它直接回应用户关于迁移 todo 和“目录里到底还有哪些 todo”的困惑，也保护 `goal-mode-playbook.md` 的 todo 优先规则。当前如果不先收敛事实源，后续 milestone 选择会继续被历史文件误导。
2. B 暂不选为本轮实现，因为 push 前必须通过 `scripts/test-full.sh`，当前环境缺 DeepSeek 凭证和真实 benchmark 仓库；不能把失败的 full regression 说成通过。
3. C 暂不选，因为它是代码行为增强，价值明确但不如当前文档事实源收敛紧急；完成 A 后可作为下一轮候选。

本轮 milestone：

作为 Harness Maintainer，当我检查 `docs/todos/` 决定下一轮目标模式是否应优先处理已有 todo 时，我可以从 README 和每个保留文件的状态清楚区分 open、paused background 和 implemented archive，从而不会把历史 todo 文件误判成仍待执行的当前任务。

## 决策

- 不删除历史 todo 文件。它们仍保留背景、完成说明和可回溯链接。
- `docs/todos/README.md` 改为显式声明：当前 open todo 以“当前待办”表为准；目录中保留的 implemented / paused 文件不等同于 open todo。
- `archive.md` 继续作为已完成条目索引，不再要求物理移动每个已完成文件。
- 两个 paused 文件不再指向已经完成的 `local-unique-capability-migration.md` 作为当前优先事项。

## 非目标

- 不新增产品功能。
- 不重新打开旧的 ai4se 或 maturity wizard 宽泛 todo。
- 不修改 `init`、LLM、benchmark、schema 或 Runtime 分工。
- 不绕过 push 前 `scripts/test-full.sh` 要求。

## 验收标准

- `docs/todos/README.md` 能明确说明当前没有 open todo，同时列出 retained implemented / paused background 文件。
- `guided-init-ai4se-real-repo-findings.md` 与 `maturity-driven-init-wizard.md` 不再把已完成的本地迁移 todo 描述为当前优先事项。
- `docs/todos/archive.md` 的归档规则与实际文件留存方式一致。
- `rg` 检查不再出现“当前优先事项改为 local-unique-capability-migration”的过期措辞。
- `scripts/test-fast.sh` 通过；full / push 仍按外部凭证和真实仓库前置另行处理。

## Assumptions / Risks

- Assumption：历史 todo 文件对回溯仍有价值，删除或大规模移动会破坏已有链接和上下文。
- Risk：目录中仍保留多个 `.md` 文件，用户如果不读 README 仍可能误判；本轮通过状态表和管理规则降低风险。
- Risk：push 仍被 full acceptance 环境挡住；本轮只记录事实，不降低规则。

## Sub Agent

尝试启动只读 explorer 审查 todo 状态，当前环境返回 `agent thread limit reached`。主线程继续完成调研、设计和验证。
