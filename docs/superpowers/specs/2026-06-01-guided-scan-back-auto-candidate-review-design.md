# Guided Scan Back 自动候选复核设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`src/harness_builder_agent/tools/interactive_init.py` 和 guided init integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`；本轮不修改 LLM prompt/schema、benchmark gate、Sensor 规则、模块边界或 Runtime 契约。
- open todo：`docs/todos/README.md` 显示当前没有 open todo。
- sub agent：尝试启动只读 explorer 审查 scan back candidate gap，当前环境返回 `agent thread limit reached`；主线程继续调研。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 返回 scan 后自动重新审查刷新后的候选 | 上一轮 Gate / init North Star 渐进式协作 | 用户修改 scan 后，依赖 scan 的 LLM Guide / Sensor candidates 立即按新扫描理解重新逐项确认，最终写入只使用当前 candidate decision | 当前返回 scan 会刷新候选、清空旧决策，并在最终确认摘要提示可再返回 candidates；直接输入 `候选` 已降低手动返回成本 | 候选设计依赖扫描理解，但重新审查仍需要用户二次回最终确认再选择 candidates；用户可能直接确认，导致候选默认 kept 而非明确复核 | 把“扫描理解改变 -> 相关候选重新审查”放到同一协作闭环，降低误确认和审查遗漏风险 | 低到中；触碰 guided init 交互顺序和 tests，不改 schema、writer、LLM 或 Runtime | integration transcript 证明 scan back 后第二次 candidate review 自动出现；`interaction-decisions.yaml` 记录新决策；旧备注不进入产物 | 无外部凭证 | CLI 输出、candidate decision schema、candidate report status 和回归测试 | 本轮 |
| B. README 明确最终确认可直接输入返回目标 | 上一轮实现与文档一致性 | README 的用户说明完整覆盖直接 `扫描` / `候选` 返回目标 | 工程文档已记录；README 已说明返回目标支持中英文，但未强调可跳过 `back` | 主文档有轻微不精确，可能让用户少知道一个快捷路径 | 文档一致性提升，但单独价值较小 | 低；纯文档 | 文档 diff | 无 | README diff | 若与本轮相关可顺手补齐，不单独作为 milestone |
| C. full regression / push 工作包 | Git 状态 / 提交规则 | 本地 78 个 ahead commit 通过 full 并 push GitHub | `.env` 和 `.benchmarks` 已存在；fast 通过 | sandbox 下 acceptance 无法解析 `api.deepseek.com`；非 sandbox full 会向 DeepSeek 发送 fixture / benchmark evidence，权限申请被策略拒绝 | 远端同步本地工作 | 外部网络和数据外发权限阻塞 | `scripts/test-full.sh` + push | 需要用户明确批准外部发送 evidence | full 通过、git push 成功 | 继续作为 push gate，不作为本轮功能 milestone |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 的渐进式协作：用户修改扫描理解后，相关设计候选应在继续写入前重新对齐，而不是把关键复核藏到下一次最终确认操作里。它也延续前几轮 scan back candidate 链路，形成完整闭环。
2. B 不单独选择。它是文档精度问题，可以在 A 的文档更新中保持一致，但不值得独立占用一轮。
3. C 受外部服务和数据外发权限阻塞；本轮仍在本地提交层面推进，push 前继续执行规则。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认阶段返回 `scan` 修改扫描理解后，我可以立即重新审查基于新扫描状态刷新的 Guide / Sensor 候选，并让最终 `.ai` 产物只记录这次新审查的决策，从而不会因为旧决策被清空后忘记再次进入候选审查而把候选默认保持。

## 设计

- 在 `action == "scan"` 分支中，重算 `weapon_selection` 和 `candidate_report` 后继续清空旧 `candidate_decisions`，并输出“旧决策已清空”的边界。
- 如果刷新后的 `candidate_report.candidates` 非空，立即进入 `_review_candidates(candidate_report, weapon_selection, commands)`。
- 新审查结果进入下一次写入前预览和最终确认摘要；最终确认不再显示“待重新审查 N 条”，而是显示本次 accepted / rejected / edited / kept 统计。
- 无候选时保持空决策并继续到最终确认。
- 文案从“如需重新审查，请再返回 candidates”调整为“接下来将按当前扫描状态重新审查候选”。

## 非目标

- 不修改 candidate schema、writer、LLM candidate generation 或 review-only 状态机。
- 不自动应用候选到正式 Guides / Sensors。
- 不修改已有 Harness 维护入口的 `review-initial-candidate`。
- 不执行 Runtime、不创建 `.ai/task-runs`。
- 不改变非 scan 返回路径。

## 验收标准

- RED：新增 guided init integration 先证明 `back -> scan` 后不会自动重新进入候选复核，旧决策被清空后默认 kept。
- 实现后：
  - `back -> scan` 后 CLI 输出候选刷新和即将重新审查的提示。
  - transcript 中“逐项审查模型候选”出现两次。
  - 第二次 `a/r/e` 决策写入 `.ai/interaction-decisions.yaml`，旧备注不进入产物。
  - 最终确认摘要展示新审查统计，而不是待重新审查默认 kept 提示。
  - scan 补充替换 / 清空相关回归仍通过。
  - `tests/integration/test_init_on_fixture_projects.py`、`compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：用户返回 scan 代表候选依赖的上游理解已经改变，立即复核候选比默认 kept 更符合写入前审查边界。
- Risk：返回 scan 后交互步数增加；但这是因为候选和 scan 强依赖，且用户可以对单项候选直接回车保持，成本可控。
- Risk：旧文档曾允许用户显式返回 candidates；本轮不删除该能力，只把 scan back 后的候选复核提前执行。
