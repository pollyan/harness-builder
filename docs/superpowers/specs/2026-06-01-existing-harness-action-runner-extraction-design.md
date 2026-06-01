# Existing Harness Action Runner 抽取设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、最近的 Existing Harness action summary renderer spec / plan、`docs/evolution-log.md`。
- 当前代码 / 测试检查：`interactive_init.py` 仍有 1694 行；已有 Harness 入口已经拆出 `existing_harness_actions.py`、`existing_harness_status.py`、`existing_harness_signals.py` 和 `existing_harness_action_summaries.py`，但 `exit`、`assess`、`improve`、`benchmark`、`recommend-workflow`、`review-candidate`、`review-human-input`、`self-improve`、`reinit` 和 unknown action 的执行分支仍集中在 `_handle_existing_harness_entry()` 内。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo；`local-unique-capability-migration.md` 已是 implemented，不作为本轮迁移目标。
- 按需未展开：`docs/engineering/llm-contracts.md` 与 `sensor-and-gate-rules.md`；本轮不修改 LLM prompt、scan、schema、benchmark 规则或 Sensor 质量门。
- Sub agent：尝试启动只读 explorer 审查 action runner 抽取风险，但当前会话返回 `agent thread limit reached`；本轮由主线程完成 Current State Gap Analysis、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness action runner 抽取 | Gate / 当前代码 | 主向导只负责已有 Harness 状态展示、菜单选择和首次 init 编排；维护动作执行由独立 runner 承接 | actions / status / signals / summaries 已拆出；integration 已覆盖主要 action | action execution 分支仍和主 guided init 扫描、用户补充、写入前预览混在一个大文件里 | 保护“再次运行 init -> 选择维护动作 -> 获得可审计结果”的旅程，降低后续维护入口功能迭代风险 | 中：涉及 trace、artifact、错误路径、prompt 输入和多个 action；但行为等价抽取，不改 schema / LLM / Runtime | 新 unit 覆盖 runner exit / reinit / unknown / human-input 默认 helper；existing Harness targeted integration 覆盖 action 语义；fast regression | 无外部凭证；依赖现有 Pydantic schema 与 mock LLM integration | 新模块可直接执行 action；`interactive_init.py` 调用 runner；existing Harness action transcript、trace summary、artifact 语义保持 | 本轮 |
| B. 首次 init completion 生成清单进一步紧凑化 | 上一轮 Gate / init North Star | 完成摘要更短、更行动优先 | completion 已行动优先且用户补充已压缩 | 生成资产清单仍偏长，但属于交付确认信息 | 改善首次 init 末尾阅读成本 | 低 | unit / integration transcript | 需要定义资产清单压缩口径 | 暂不处理 |
| C. Push 前 full regression / 远端同步 | Gate / git 状态 | 本地工作包形成独立价值后再 full regression 与 push | 当前 main ahead 46，多个本地 commit 尚未 push | 本轮单独 commit 后仍可能不具备完整 push 工作包边界 | 降低远端分叉风险 | 高：`scripts/test-full.sh` 依赖 acceptance / DeepSeek / 真实仓库，可失败于外部条件 | full regression / push / CI 查询 | 需要完整工作包边界和可能的外部凭证 | 作为后续同步工作包，不混入本轮代码抽取 | 后续候选 |

排序结论：

1. 选择 A，因为它紧接上一轮 action summary renderer 抽取，能把已有 Harness 维护入口的展示、信号、摘要和执行职责进一步分层；它不是新增用户功能，但直接保护 North Star 中“再次进入已有 Harness”的维护旅程。
2. B 暂不选，因为首次 init completion 已经完成行动优先和用户补充压缩，当前用户价值低于 action execution 边界收敛。
3. C 暂不选，因为当前仍处在本地目标模式连续演进阶段；push 需要完整工作包与 full regression，不应和本轮工程抽取混在一个 milestone。

## 本轮 Milestone

作为 Harness Builder 维护者，当我继续打磨已有 Harness 维护入口的维护动作时，我可以在独立 action runner 模块中执行、测试和审查 `assess`、`improve`、`benchmark`、`recommend-workflow`、`review-candidate`、`review-human-input`、`self-improve` 等动作，从而让 `interactive_init.py` 专注于向导编排和状态展示，并降低后续修改维护动作时误伤首次 init 主流程、trace 或 Runtime 边界的风险。

## 验收标准

1. 新增 `src/harness_builder_agent/tools/existing_harness_action_runner.py`，集中承接 existing Harness action execution。
2. `_handle_existing_harness_entry()` 只负责读取现有 Harness 状态、渲染维护入口、收集并 normalize 用户动作，然后调用 runner；行为等价，不改变菜单、默认 `exit`、CLI 文案、trace summary、artifact 或 Runtime 边界。
3. `review-human-input` 默认 interaction id helper 进入 runner 模块；`interactive_init.py` 保留薄 facade，兼容既有 unit / 隐藏调用。
4. 新 unit 直接覆盖 runner 的 `exit`、`reinit`、unknown action 和 human-input 默认 id，证明 runner 可脱离主向导文件测试核心控制流。
5. Existing Harness targeted integration 覆盖 `exit` / numbered exit / `assess` / `improve` / `benchmark` / failed benchmark / `recommend-workflow` / `review-candidate` apply / `review-human-input` / `self-improve` 关键路径仍通过。
6. 不修改 `.ai` schema、LLM prompt、benchmark 检查规则、正式资产生成或 Runtime 分工；Builder 仍不执行 Runtime、不创建 `.ai/task-runs`。
7. 提交前运行 `scripts/test-fast.sh`。

## 关键决策 / 取舍

- 本轮做行为等价抽取，不调整 existing Harness action 文案或流程。
- Runner 可以继续使用 `typer.prompt`，因为它承接的是 guided action execution；CLI 层仍负责 action selection。
- Candidate summary / preview renderer 继续由 `existing_harness_action_summaries.py` 提供，runner 只负责编排调用。
- `interactive_init.py` 保留 `_review_human_input_default_interaction_id()` 等薄 facade，避免破坏现有直接导入测试和隐藏测试。

## Assumptions / Risks

- Assumption：上一轮已抽出 action summaries，当前搬迁 action execution 的主要风险集中在 imports、trace artifact 和异常路径，适合用 existing Harness targeted integration 锁住。
- Risk：直接从 `interactive_init.py` 搬出执行分支可能遗漏某个 artifact 或 trace summary 字段；本轮用所有 existing Harness action integration 和 runner unit 验证。
- Risk：测试或用户可能依赖 `interactive_init.py` 的私有 helper；本轮保留薄 facade，并只把核心实现移到 runner。
