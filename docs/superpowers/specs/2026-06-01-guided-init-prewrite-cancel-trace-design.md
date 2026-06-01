# Guided Init 写入前取消 Trace 审计

## Current State Gap Analysis

事实源快照：
- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、当前 `interactive_init.py` / existing Harness integration tests、最近 spec / plan / evolution log。
- 按需未展开：`docs/engineering/llm-contracts.md`、`sensor-and-gate-rules.md` 和完整 benchmark 实现；本轮不改 LLM、Sensor、benchmark 规则、`.ai` schema 或正式资产 writer。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 写入前最终取消应保留扫描审计 | 上轮 Gate / 新发现 | Maintainer 在扫描、补充、预览之后选择取消时，trace 能说明取消发生在写入前、扫描已完成、识别出的 stack 和 command 数量，并证明未写正式资产 | CLI 已输出“未确认写入，未覆盖正式 Harness 资产，未创建 Runtime 产物”；reinit 取消会保留 action | trace summary 只有 `cancelled=true` 和可选 `existing_harness_action`，无法区分 startup cancel 与 prewrite cancel，也丢失已完成扫描的摘要 | 保护渐进式协作的审计链：用户取消后仍能复盘系统做过哪些判断、为何没有写资产 | 低：只扩展 trace summary 与取消 helper，不改生成资产或 schema | integration CLI transcript + trace summary；formal asset absence / unchanged | 无外部服务；mock scan 即可 | 首次 init final cancel 不写 `.ai/project-inventory.json`，trace failed summary 含 `cancel_stage=prewrite_confirmation`、`scan_completed=true`、`primary_stack`、`command_count`；reinit final cancel 保留正式资产不变并含 `existing_harness_action=reinit` | 本轮 |
| B. full regression / push gate 外部阻塞 | Self-Harness Gate | 完整工作包 push 前可运行 full regression 并通过真实 DeepSeek acceptance | fast 可运行；full 在 sandbox acceptance 请求 DeepSeek 时失败，非 sandbox 申请被拒 | 当前无法在 sandbox 内解析 `api.deepseek.com`；非 sandbox 会向外部服务发送本地 fixture / benchmark 内容而被拒 | 影响远端同步可信度，但不阻塞本地小切片继续演进 | 高：依赖网络、外部 API 和审批 | `scripts/test-full.sh`、审批结果 | DeepSeek API、网络和外发许可 | full 通过后才能 push；当前作为外部前置记录 | Gate 候选，不作为代码 milestone |
| C. existing Harness action runner 进一步拆分 | 代码结构 / 历史 Gate | runner 按动作族分层，降低维护入口迭代冲突 | review 类动作已拆出，runner 仍承载 assess / improve / benchmark / recommend / self-improve / reinit | 文件仍偏大，但当前用户可见价值弱于 A | 降低后续维护风险 | 中：行为保持型重构需较多回归 | unit / integration 等价回归 | 无 | runner API 和现有 action transcript 不变 | 下一轮候选，需重新评估 |

排序结论：
1. 选择 A，因为它直接服务 `init-north-star.md` 的“渐进式协作”和“可审计”：用户已经经历扫描和设计预览后取消，trace 不能只说“取消”，必须保留取消阶段和扫描摘要。
2. B 是外部 push gate，不是本轮可安全代码实现的产品能力。
3. C 是工程债，价值存在但不如 A 的用户旅程审计直接。

本轮 milestone：

作为 Harness Maintainer，当我在 guided `init` 已完成扫描和写入前设计预览后选择取消时，我可以在 CLI 中确认未写入正式 Harness 资产，并在 trace summary 中看到取消发生在写入前、扫描已经完成、识别出的 stack / command 摘要以及 reinit 来源，从而能安全复盘一次未完成的初始化或重新生成会话。

## 设计

1. 扩展取消 summary
   - `_cancel_guided_init()` 增加 `cancel_stage` 和可选 `inventory` / `commands` 参数。
   - startup confirmation 取消写入：
     - `cancel_stage=startup_confirmation`
     - `scan_completed=false`
   - prewrite / final confirmation 取消写入：
     - `cancel_stage=prewrite_confirmation`
     - `scan_completed=true`
     - `primary_stack=<inventory.primary_stack>`
     - `command_count=<len(commands.commands)>`
   - reinit 仍保留 `existing_harness_action=reinit`。

2. 保持用户边界
   - CLI 文案继续使用当前中文取消摘要，不增加长输出。
   - 不写正式 `.ai` Harness 资产；首次 init final cancel 不生成 `project-inventory.json` 等正式资产。
   - reinit final cancel 保持已有正式资产不变。

3. 文档事实源
   - README existing Harness / guided init 说明补充：取消 trace 会记录取消阶段和是否已完成扫描。
   - `docs/engineering/init-workflow.md` 沉淀稳定规则。
   - `docs/evolution-log.md` 记录本轮 gap、取舍、验证和 Gate。

## 验收标准

- integration RED：
  - 首次 guided init final cancel 当前 trace summary 缺少 `cancel_stage`、`scan_completed`、`primary_stack`、`command_count`。
  - reinit final cancel 当前 trace summary 仅保留 action / cancelled，缺少已扫描摘要。
- 实现后：
  - 首次 guided init final cancel exit code 为 1，输出“已取消 init”和“未确认写入”，不输出 `== 初始化完成 ==`，不写 `.ai/project-inventory.json`。
  - trace failed summary 含 `cancelled=true`、`cancel_stage=prewrite_confirmation`、`scan_completed=true`、`primary_stack=java-spring`、`command_count=1`。
  - reinit final cancel 保留正式资产 snapshot 不变，trace failed summary 含上述字段和 `existing_harness_action=reinit`。
  - reinit startup cancel 回归仍含 `cancel_stage=startup_confirmation`、`scan_completed=false`，不调用 scan。
- 文档 diff 同步 README、init workflow 和 evolution log。
- 提交前运行 `scripts/test-fast.sh`。
- push 前必须运行 `scripts/test-full.sh`；若 full gate 仍因 DeepSeek DNS / 外发审批失败，则只本地 commit，不 push。

## Assumptions / Risks

- Assumption：`GenerationTrace.summary` 是审计摘要，不是严格 schema 文件；新增字段不会破坏机器契约。
- Risk：测试输入需要走到 final confirmation；若 guided prompt 数量变化，测试会暴露交互契约漂移。
- Risk：本轮不记录用户补充明细到 failed trace；完整补充审计仍只在确认写入后落入 `interaction-decisions.yaml`。取消场景只记录扫描摘要和取消阶段，避免把未写入决策伪装成正式资产。

## Sub Agent

本轮按目标模式尝试启动只读 explorer 交叉验证候选，环境返回 `agent thread limit reached`。主线程继续完成调研、TDD、实现、验证和提交。
