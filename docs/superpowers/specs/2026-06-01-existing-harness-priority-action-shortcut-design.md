# Existing Harness 推荐动作编号提示设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/architecture.md`、`docs/engineering/testing-strategy.md`、相关 `docs/superpowers/specs/` / `docs/superpowers/plans/` / `docs/evolution-log.md` 摘要、`interactive_init.py`、`maintenance_triage.py`、相关 unit / integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md` 和 `sensor-and-gate-rules.md`，本轮不修改 LLM、prompt、schema、scan reconciler、Sensor 或 benchmark 规则。
- Sub agent：已尝试启动 explorer 做 completion summary / milestone 交叉调研，但当前会话达到 `agent thread limit reached`，本轮改为主线程完成调研并记录限制。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness 推荐动作编号提示 | init North Star / Gate 新发现 | Maintainer 再次运行 `init` 时，不仅知道 top action，还能直接知道应该输入哪个菜单编号 | 维护入口已展示 Benchmark / Workflow / Experience signals、Maintenance triage、中文 guidance 和 1-9 编号菜单 | triage guidance 只说运行 `benchmark` / `review-human-input` 等动作，用户仍需手动把动作名映射到菜单编号；菜单越长越容易选错 | 降低已有 Harness 维护入口的认知负担，让“看到问题 -> 选择动作”形成更直接闭环 | 低：只新增渲染 helper 和 CLI 输出，不改 schema / LLM / Runtime / 正式资产 | unit 覆盖 action 到编号映射和 unknown action；integration 覆盖 existing Harness 输出中出现推荐编号且仍可 exit 不覆盖资产 | 依赖现有 `MaintenanceAction` 和编号菜单稳定顺序 | guided `init` existing Harness 输出包含 `建议优先选择：4. benchmark` 等编号提示；未知动作不伪造编号 | 本轮 |
| B. Completion summary 视觉紧凑化 | 上轮 Gate | 首次 init 完成摘要短而清晰，不和 `init-summary.md` 过度重复 | completion message 已展示生成资产、成熟度、证据 / 缺口、用户补充、benchmark、入口和待确认问题 | 用户补充和入口列表可能偏长，但当前仍满足主交付说明；缺少真实 transcript 的体验基线 | 进一步改善首次 init 终端体验 | 低到中：需要重新界定哪些内容必须保留，容易误删审计边界 | unit / integration transcript 行数和关键内容断言 | 需要先定义“短摘要”的稳定口径 | 下一轮候选 |
| C. Existing Harness 维护入口模块拆分 | 上轮 Gate / 工程债 | 维护入口代码边界清晰，便于继续打磨已有 Harness 用户旅程 | `prewrite_preview` 已抽出，但 `_handle_existing_harness_entry()` 仍在 `interactive_init.py` 中承载大量分支 | 后续每次维护入口体验调整都要改大文件；不过本轮有更直接的用户可见缺口 | 降低维护风险 | 中：纯重构，容易和行为变更混杂 | unit 保持 helper 行为、integration 确认菜单动作 | 依赖先稳定维护入口用户文案 | 下一轮候选 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的“再次进入已有 Harness”旅程，把已存在的 triage 判断连接到实际菜单选择；范围小、可本地测试、无外部凭证依赖。
2. B 暂不选，因为 completion message 刚增强过用户补充闭环，继续压缩前需要更明确的 transcript 标准，避免误删主交付摘要。
3. C 暂不选，因为它主要是工程信任切片；在已有 Harness 菜单继续增加动作前值得做，但本轮先解决用户看得见的选择摩擦。

## 本轮 Milestone

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口并看到 Maintenance triage 推荐动作时，我可以直接看到推荐动作对应的菜单编号，从而不用在长菜单中手动映射动作名，也能更稳地选择下一步维护动作。

## 验收标准

1. Existing Harness 维护入口在 `Maintenance triage guidance` 之后展示推荐选择提示，例如 `建议优先选择：4. benchmark` 或 `建议优先选择：7. review-human-input`。
2. 推荐选择提示必须来自同一份 action normalization / 菜单编号映射，不能写死单一场景；未知 action 必须显示不可通过菜单直接选择，而不是伪造编号。
3. 输出只做指导，不自动执行动作、不覆盖正式 Harness 资产、不创建 `.ai/task-runs`。
4. Unit 测试覆盖 benchmark、review-human-input、recommend-workflow 和 unknown action 的编号提示。
5. Integration 测试覆盖已有 Harness guided `init` 只读 exit 输出推荐编号，并保持正式资产不变。
6. 文档记录本轮决策、验证结果和 Self-Harness Gate；不新增 open todo，除非 Gate 发现新的较大缺口。

## 关键决策 / 取舍

- 只增强 CLI 文案和 helper，不改变 `MaintenanceAction` schema、不改变 triage 排序、不改变 existing Harness 动作执行语义。
- 编号提示是 “建议优先选择”，不是自动默认动作；默认输入仍保持 `1` 只读退出，避免误触发写入或 LLM 动作。
- 继续保留英文 action 名，方便和 trace / 文档 / standalone 命令对应；中文说明只负责降低选择成本。

## Assumptions / Risks

- Assumption：现有 1-9 菜单顺序是当前稳定用户界面，可以作为编号提示来源。
- Risk：如果未来菜单编号调整，编号提示可能漂移；因此本轮把编号映射集中到 helper，并用 unit 测试防漂移。
- Risk：推荐提示可能让用户误以为默认会执行该动作；文案使用“建议优先选择”且默认仍是 `1` exit。
