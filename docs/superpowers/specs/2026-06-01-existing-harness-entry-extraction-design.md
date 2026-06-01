# Existing Harness 维护入口模块抽取设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/evolution-log.md`、`interactive_init.py`、`existing_harness_action_runner.py`、existing Harness integration tests 和相关 unit tests。
- 当前 todo 状态：`docs/todos/README.md` 显示当前没有 open todo；本轮从 Current State Gap Analysis 重新选择。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`。本轮不改 LLM、prompt、schema、benchmark check、Sensor 或 Runtime 分工。
- Sub agent：按目标模式尝试启动只读 explorer 审查 existing Harness 维护入口拆分边界，环境返回 `agent thread limit reached`；本轮由主线程完成分析、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness 维护入口模块抽取 | 多轮 Gate / 架构规则 / init North Star | 再次进入已有 Harness 的状态读取、健康信号展示、动作选择和 action runner 调用由独立模块承接；`interactive_init.py` 只编排首次 init 状态机和 reinit 回流 | action runner、review actions、signals、status overview 已拆出；`interactive_init.py` 仍约 878 行 | `_handle_existing_harness_entry()` 及 state load / action prompt helper 仍留在主向导文件，后续维护入口改动仍要触碰首次 init 状态机 | 保护“再次进入已有 Harness”旅程，降低后续继续打磨 maintenance overview / triage / actions 时误伤首次 init 的风险 | 中：行为保持型重构，必须保留私有 alias 兼容现有测试和隐藏调用 | 新 unit 检查独立模块、state load 显式失败、interactive delegate；existing Harness integration 回归 | 无外部凭证 | 本轮 |
| B. 首次 init completion summary 视觉紧凑化 | 多轮 Gate / init North Star | 完成摘要更短、更聚焦下一步 | completion message 已有行动优先、benchmark / human input / 优先入口 | 输出仍偏长，但缺少稳定压缩口径，容易误删交付边界 | 改善首次 init 完成体验 | 低到中；文案改动易造成 transcript 漂移 | unit / integration transcript | 需要先定义必留信息和行数口径 | 下一轮候选 |
| C. Push 前 full regression / 远端同步 | Gate / Git 状态 | 本地完整工作包通过 full regression 后同步 GitHub | fast 通过；`.env` 有 DeepSeek key；分支领先远端 | sandbox DNS 失败；非 sandbox full 被策略拒绝，因为会向外部 DeepSeek 发送本地 fixture / benchmark evidence | 降低远端分叉风险 | 高；外部服务和数据外发审批 | `scripts/test-full.sh` + push | 需要用户理解外发风险后的显式授权 | 阻塞于外部前置 |

排序结论：

1. 选择 A。它虽然是工程信任故事，但直接保护 init North Star 的“再次进入已有 Harness”旅程；当前维护入口近期持续被增强，继续留在 `interactive_init.py` 会让后续用户可见改动反复触碰同一大状态机。
2. B 暂不选，因为 completion 已满足主交付说明，压缩口径不够稳定，当前先降低模块耦合更能支撑后续体验迭代。
3. C 暂不选，因为 full gate 受外部 DeepSeek 网络和数据外发策略限制，不能作为本轮可独立完成 milestone。

## 本轮 Milestone

作为 Harness Builder 维护者，当我继续打磨“再次进入已有 Harness”的维护状态摘要、triage 和动作入口时，我可以在独立 `existing_harness_entry` 模块中修改和单测维护入口逻辑，而不触碰首次 guided `init` 的扫描、补充、候选审查和写入确认状态机，从而降低后续维护入口迭代的冲突和回归风险。

## 验收标准

1. 新增 `src/harness_builder_agent/tools/existing_harness_entry.py`，承接已有 Harness detection、state load schema 校验、维护状态渲染、action prompt 和调用 `run_existing_harness_action()`。
2. `interactive_init.py` 不再定义 `_handle_existing_harness_entry()`、`ExistingHarnessStateLoadError` 和 state load helper；改为从新模块导入 alias，保留现有私有 helper 名称给测试和隐藏调用兼容。
3. 新增 unit tests 证明：
   - 新模块存在并暴露 `handle_existing_harness_entry()` / `load_existing_harness_state()`。
   - 有效 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml` 可通过 schema load。
   - 损坏 `harness-config.yaml` 继续抛 `ExistingHarnessStateLoadError`，source 指向 `.ai/harness-config.yaml`。
   - `interactive_init.py` 只代理维护入口，不再内联入口函数定义。
4. 运行 existing Harness integration 切片，覆盖 exit、unknown action reprompt、invalid state failure、benchmark、recommend-workflow failure、self-improve failure，证明行为等价。
5. 不修改 CLI 文案、`.ai` schema、writer、LLM prompt、benchmark、Sensor 或 Runtime 分工。

## 非目标

- 不改变已有 Harness 入口的用户可见输出顺序或菜单文案。
- 不拆 `existing_harness_action_runner.py` 的各动作执行分支。
- 不统一所有短错误 helper。
- 不解决 full regression 外部 DeepSeek / push 前置。

## 决策 / 取舍

- 新模块边界选择“已有 Harness 维护入口编排”，动作执行仍交给 `existing_harness_action_runner.py`，review 类动作仍交给 `existing_harness_review_actions.py`。
- 为降低行为漂移，搬迁时保留 `interactive_init.py` 原 `_normalize_existing_harness_action`、`_benchmark_signal_lines` 等私有 alias。
- 本轮是行为保持型重构，测试失败时优先修边界，不放宽断言。

## Assumptions / Risks

- Assumption：维护入口已形成稳定产品边界，抽成模块能减少后续目标模式反复修改主向导的风险。
- Risk：隐藏测试可能引用 `interactive_init.py` 中的私有 helper；通过 import alias 保持兼容。
- Risk：直接搬迁可能遗漏 import 或导致 state load 错误类型漂移；通过 unit 和 existing Harness integration 切片覆盖。
