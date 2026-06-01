# Guided Scan 补充解析诊断设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`、最近 completion / existing Harness specs、`docs/evolution-log.md`。
- 当前代码 / 测试检查：`interactive_init.py` 仍承载首次 guided init 的扫描展示、扫描补充解析、团队规则、候选审查、Workflow 补充和最终确认；其中 `_collect_scan_supplement()` 支持 `stack=`、`module=`、`command=`、`risk=` 结构化片段，但格式不完整或 gate/type 非法时，会把原始片段直接追加到 notes。用户能看到“用户补充”，但看不到该片段没有进入 `command catalog` / `project inventory` / `risk hints`。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo；本地独有能力迁移 todo 已归档为 implemented。
- 按需未展开：`docs/engineering/llm-contracts.md`；本轮不修改 LLM prompt、schema、DeepSeek、evidence planner 或 scan reconciler。
- Sub agent：按 goal-mode playbook 尝试启动只读 sub agent 审查本轮 gap，但当前会话返回 `agent thread limit reached`；本轮由主线程完成 Gap Analysis、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Guided scan 结构化补充解析诊断 | init North Star / 当前代码 | 用户输入 `command=`、`module=`、`risk=` 等结构化片段后，CLI 明确说明哪些片段已进入结构化补充，哪些因格式不完整只作为自然语言补充保留 | `_collect_scan_supplement()` 能解析合法片段，并把非法片段加入 notes | 非法结构化片段没有诊断，用户可能误以为 command 已进入 command catalog 或 risk 已进入 risk hints | 保护扫描理解对齐阶段，降低用户输入被“看似吸收但未结构化生效”的信任风险；符合 no silent fallback | 低到中：只抽出解析器和 CLI 诊断，不改 `.ai` schema 或 writer | unit 直接测解析器；guided integration 可继续覆盖 scan supplement 链路；fast regression | 无外部凭证；依赖现有 `GuidedScanOverrides` | 非法 `command=unit|mvn test|test|hard` 产生诊断 note，`commands` 为空；合法片段行为不变；CLI immediate summary 明确“不进入结构化补充” | 本轮 |
| B. 抽取 scan presentation renderer | 上一轮 Gate / 工程架构 | `interactive_init.py` 中扫描发现、风险/不确定性/验证缺口和成熟度 snapshot 渲染进入独立模块 | prewrite preview、existing Harness runner/signals 已拆分，scan presentation 仍在主文件 | 主向导仍 1200+ 行，后续修改 scan 体验容易误碰状态机 | 降低维护风险，便于单测 CLI 文案 | 中：搬迁函数多，hidden test 可能依赖私有 helper | unit + guided integration | 无外部依赖 | 新 renderer 模块，facade 兼容旧私有 helper，guided tests 通过 | 下一轮候选 |
| C. Push 前 full regression / 远端同步 | Git 状态 / Gate | 完整工作包形成后同步 GitHub | 当前 `main` 线性领先 `origin/main` 48 个提交 | push 前 full regression 因缺少 `DEEPSEEK_API_KEY` 与 `.benchmarks/*` acceptance 依赖失败 | 降低本地远端分叉风险 | 高：外部凭证和真实仓库依赖 | `scripts/test-full.sh` + push | 需要外部环境补齐 | 当前不 push；保留为工作包完成后的同步动作 | 后续 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的“低门槛自然语言补充 + 高精度结构化修正 + 用户补充后复述理解和影响”目标。当前问题不是解析能力完全缺失，而是错误结构化输入的生效边界不够可见。
2. B 暂不选，因为它更偏工程重构；本轮先修一个用户可感知且可审计的解析诊断，再把 scan presentation 拆分作为后续工程信任故事。
3. C 暂不选，因为 push gate 当前受 acceptance 外部依赖阻塞，不应把外部环境问题混入本轮 init 用户体验切片。

## 本轮 Milestone

作为 Harness Maintainer，当我在首次 guided `init` 的扫描对齐阶段输入结构化补充但格式不完整或字段非法时，我可以立即看到该片段没有进入结构化 project inventory / command catalog / risk hints，只会作为自然语言补充保留，从而避免误以为 Harness 已经吸收了一个实际验证命令或风险区域。

## 验收标准

1. 扫描补充解析逻辑从 `_collect_scan_supplement()` 中抽出为可单测模块，合法 `stack`、`module`、`command`、`risk` 行为保持不变。
2. 格式不完整或字段非法的结构化片段必须产生明确中文诊断，说明“未进入结构化扫描补充，只作为自然语言补充保留”。
3. 非法 `command=` 不能生成 `CommandDefinition`，不能进入 command catalog；非法 `module=` / `risk=` 不能进入对应结构化列表。
4. 没有 `=` 的自然语言补充仍按原行为进入 notes，不被误报为结构化错误。
5. CLI 的“扫描补充理解 / 影响”阶段能展示这些诊断，让用户在进入团队规则和写入前 preview 前看到生效边界。
6. 不修改 `.ai` schema、LLM prompt、scan reconciler、writer、benchmark 或 Runtime 分工。
7. 更新 evolution log，记录本轮 Gap Analysis、取舍、验证和 Self-Harness Gate。
8. 提交前运行 `scripts/test-fast.sh`；push 仍等待 full regression 外部依赖补齐。

## 关键决策 / 取舍

- 本轮不把非法结构化片段直接丢弃，而是作为自然语言补充保留，并明确标注它未进入结构化补充。这样既保留用户意图，又避免 silent fallback。
- 本轮不新增 `GuidedScanOverrides` 字段，避免扩大到 interaction decision schema 或 writer 契约；诊断作为 notes 进入现有审计链路。
- 保留 invalid stack 的二次提示能力；如果用户二次输入仍非法，再按诊断保留为自然语言补充。

## Assumptions / Risks

- Assumption：用户把 `command=`、`module=`、`risk=` 写错时，宁可看到明确诊断，也不应被静默当成结构化补充成功。
- Risk：诊断作为 notes 进入后续 `.ai` 语义资产，可能增加少量噪声；但它表达的是真实人工补充边界，符合审计需要。
- Risk：`interactive_init.py` 仍偏大；本轮只抽出解析器，scan presentation renderer 拆分留作下一轮候选。
