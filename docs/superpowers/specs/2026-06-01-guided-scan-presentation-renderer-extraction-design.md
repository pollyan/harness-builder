# Guided Scan Presentation Renderer 抽取设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、上一轮 scan supplement diagnostics spec / plan、`docs/evolution-log.md`。
- 当前代码 / 测试检查：`interactive_init.py` 当前约 1175 行；已有 Harness action runner / summaries / signals、prewrite preview、scan supplement parser 已拆出。但首次 guided init 的 scan progress、scan findings、LLM evidence expansion、深度追问、self-check、风险 / 不确定性 / 验证缺口、扫描后成熟度初评和 stack label helper 仍集中在 `interactive_init.py`。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo；迁移 todo 已 implemented。
- 按需未展开：`docs/engineering/llm-contracts.md` 与 `sensor-and-gate-rules.md`；本轮不修改 LLM prompt、scan schema、benchmark、Sensor 或 Runtime 分工。
- Sub agent：按 playbook 尝试启动只读 sub agent 审查本轮抽取边界，但当前会话返回 `agent thread limit reached`；本轮由主线程完成分析、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Guided scan presentation renderer 抽取 | 上一轮 Gate / 架构规则 / init North Star | 首次 guided init 的扫描呈现、成熟度 snapshot 和关注点文案有独立模块与 direct unit tests，主向导只编排状态 | 相关行为已有 integration 覆盖，但 helper 都在 `interactive_init.py` | 主向导文件仍混合扫描呈现与状态机，后续继续打磨扫描理解和成熟度初评时容易误碰用户输入流程 | 降低后续 init 主体验迭代风险，保护“扫描发现 -> 成熟度初评 -> 用户补充”的 North Star 主链路 | 中：搬迁 helper 多，但行为应保持不变；通过导入别名保留 `interactive_init._*` 兼容 | 新 renderer unit + existing guided integration + fast regression | 无外部凭证；不依赖真实 DeepSeek | 新模块可直接渲染 evidence expansion / risk / uncertainty / maturity snapshot；`interactive_init.py` 私有 helper 名称仍可用；transcript integration 不漂移 | 本轮 |
| B. Scan supplement parser 继续增强友好示例 | 上轮 Gate / 当前代码 | 结构化片段格式错误时不仅说明未生效，还给出最小可复制修正示例 | 已能诊断非法片段未进入 command catalog / project inventory / risk hints | 诊断还偏“说明边界”，尚未提供自动修正示例 | 进一步降低用户输入成本 | 低，但更偏 UX 文案，价值小于先拆出 scan presentation 边界 | unit + integration transcript | 无 | 可后续作为小 UX 切片 | 下一轮候选 |
| C. Push 前 full regression / 远端同步 | Git 状态 / Gate | 本地完整工作包通过 full regression 后同步 GitHub | 当前 main 线性领先 origin/main 49 | full regression 缺少 `DEEPSEEK_API_KEY` 和 `.benchmarks/*` 真实仓库导致 acceptance 失败 | 降低远端分叉风险 | 高，受外部依赖阻塞 | `scripts/test-full.sh` + push | 需要本地凭证和真实仓库 | 当前不 push | 后续 |

排序结论：

1. 选择 A，因为它保护 init North Star 的核心体验段：扫描发现、成熟度初评、低置信度追问和用户补充前的判断呈现。它不改变 schema / 产物 / LLM，却能降低后续继续增强扫描深度和 CLI 体验的维护风险。
2. B 暂不选，因为上一轮刚完成解析诊断，继续堆文案会让切片过小；先把 presentation renderer 拆出来，后续文案增强成本更低。
3. C 暂不选，因为 push gate 仍受外部 acceptance 依赖阻塞，不能作为本轮可独立完成 milestone。

## 本轮 Milestone

作为 Harness Builder 维护者，当我继续打磨首次 guided `init` 的扫描理解、深度追问和成熟度初评体验时，我可以在独立 `guided_scan_presentation` 模块中修改和单测扫描呈现逻辑，而不触碰主向导状态机，从而降低后续改进用户扫描对齐体验时误伤补充收集、候选审查、确认写入或已有 Harness 维护入口的风险。

## 验收标准

1. 新增 `src/harness_builder_agent/tools/guided_scan_presentation.py`，承接首次 guided init 的 scan progress、scan findings、attention summary、LLM evidence expansion、followup questions、self-check、maturity snapshot 和 stack label helper。
2. `interactive_init.py` 保留原私有 helper 名称作为导入别名，现有和隐藏测试调用 `interactive_init._risk_attention_lines` / `_show_scan_findings` 等不应失效。
3. 新增 direct unit tests 覆盖 renderer 的 evidence expansion、risk / uncertainty / verification gap lines、maturity snapshot transcript 和 progress callback 文案。
4. 现有 guided init integration transcript 行为不变，至少运行相关扫描展示 / evidence expansion / followup / scan supplement 切片。
5. 不修改 `.ai` schema、writer、benchmark、LLM prompt、scan reconciler、Runtime 分工或已有 Harness action runner。
6. 更新 evolution log；如长期文档事实源不变，不额外扩大 README / engineering 文档。
7. 提交前运行 `scripts/test-fast.sh`；不 push，直到 full regression acceptance 依赖补齐。

## 关键决策 / 取舍

- 抽取边界选择“首次 guided init 的扫描呈现层”，不迁移 scan execution、trace、用户补充解析、候选审查或写入确认状态机。
- 为兼容现有测试和隐藏调用，`interactive_init.py` 用 import alias 暴露原 `_show_*` / `_risk_*` / `_stack_*` 名称。
- 本轮是行为保持型重构，所有用户可见 transcript 变化都应由测试捕获；若测试失败，优先修迁移边界，不放宽断言。

## Assumptions / Risks

- Assumption：拆出 renderer 能降低后续 init North Star 持续迭代成本，独立价值体现在工程信任和测试定位。
- Risk：搬迁函数较多，容易漏掉 import 或 helper；通过 direct unit、targeted integration 和 fast regression 控制。
- Risk：`interactive_init.py` 仍然包含团队规则、候选审查、Workflow 补充和最终确认；这些可作为后续拆分候选，而不是本轮顺手处理。
