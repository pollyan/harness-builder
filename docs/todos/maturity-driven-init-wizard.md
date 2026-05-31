# 成熟度驱动的 init 主向导与命令信息架构重构

## 状态

- 状态：open
- 优先级：high
- 发现日期：2026-05-31
- 已完成切片：首次 `init` 生成 `.ai/init-summary.md`，并在 CLI 完成输出中展示当前成熟度、主要阻断项、建议下一步和推荐入口文件。
- 已完成切片：默认 guided `init` 检测已有 `.ai` Harness 时先展示状态摘要，并支持 `exit` 只读退出，不覆盖正式资产。
- 已完成切片：默认 guided `init` 检测已有 `.ai` Harness 时支持 `assess` 复评成熟度，刷新 maturity 产物和 `init-summary.md`，不重新扫描或覆盖正式 Harness 资产。
- 已完成切片：默认 guided `init` 检测已有 `.ai` Harness 时支持 `improve` 生成 maturity-driven review-only 改进候选，并在生成前刷新 Experience index 与 maturity evidence。
- 已完成切片：默认 guided `init` 检测已有 `.ai` Harness 时支持 `benchmark` 运行质量门禁，刷新 benchmark / maturity / improvement 派生产物，输出失败项摘要，不重新扫描或覆盖正式 Harness 资产。
- 已完成切片：默认 guided `init` 检测已有 `.ai` Harness 时支持 `recommend-workflow` 收集任务说明，生成 review-only Workflow 推荐，并刷新 Experience / Maturity 派生证据，不执行 Runtime 或修改正式 routing policy。
- 已完成切片：默认 guided `init` 检测已有 `.ai` Harness 时支持 `review-candidate` 记录候选 `accepted` / `deferred` / `rejected` 治理决策；对单个 Guide / Sensor 候选支持显式 `applied`，并刷新 Candidate Governance 与 Experience index。
- 已完成切片：默认 guided `init` 检测已有 `.ai` Harness 时支持 `self-improve` 显式生成 review-only 自改进审查包，串联 maturity review 和 asset candidates，不执行 Runtime 或应用正式资产。
- 已完成切片：默认 guided `init` 检测已有 `.ai` Harness 时展示分项 Experience / review signals，包括 pending improvements、asset candidates、candidate governance、maturity reviews、workflow recommendations、runtime task runs、self-improve package、human-input-needed 和 schema/content failed checks。
- 已完成切片：默认 guided `init` 检测已有 workflow recommendation history 时展示最新 recommendation 的 task、workflow、risk、review status 和 source；旧 Harness 无 history index 时兼容 latest recommendation 文件。
- 相关命令：`harness-builder-agent init`、`assess`、`improve`、`benchmark`、`recommend-workflow`、`self-improve`
- 相关工程规则：`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/architecture.md`
- 相关产品方向：`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`

## 背景

当前 Harness Builder 已经具备扫描、初始化 `.ai` 资产、成熟度评估、改进候选、benchmark、workflow 推荐和 self-improve review package 等底层能力。但真实用户第一次使用时，仍然需要理解多个 CLI 命令、执行顺序、参数和生成文件含义。

这导致用户感受到的是“CLI 命令集合 + 生成文件 + 人工审查”的工程工具，而不是“成熟度驱动的向导式 Harness Builder 产品”。

未来产品体验应让用户优先从 `init` 进入。`init` 不只是初始化命令，而是 Harness Builder 的主入口：首次执行建立 Harness 基线；再次执行识别已有 `.ai`，进入状态感知维护入口。

## 当前现状

当前已有能力：

- `init` 能扫描仓库并生成 `.ai` Harness 资产。
- `init` 完成后能生成 `.ai/init-summary.md`，用成熟度框架给出当前等级、阻断项、下一步建议和入口文件。
- 默认 guided `init` 发现已有 `.ai` Harness 时能展示当前状态，并允许退出不覆盖正式资产。
- `assess` 能生成成熟度评分和成熟度报告。
- `improve` 能基于成熟度缺口生成改进候选。
- `benchmark` 能验证 Harness 资产 schema、引用、内容和质量分。
- `recommend-workflow` 能为单个任务生成 review-only workflow recommendation。
- `self-improve` 能串联 maturity assessment、improvement candidates、LLM maturity review 和 asset candidates，生成 review-only package。

当前剩余问题：

- 用户仍需要理解哪些动作只是 review-only，哪些专家命令可能应用正式资产。
- 首次 `init` 已有完成摘要，但还没有在写入前后形成完整的 benchmark 健康度解释和下一步治理节奏。
- 再次执行 `init` 已具备主要维护动作、单个 Guide / Sensor 候选 applied 闭环和 latest workflow recommendation history signal，但还缺少更完整的候选列表浏览、guided apply 前 diff / summary、完整 recommendation 历史浏览和更明确的 schema / contract 修复引导。
- 底层专家命令的能力和普通用户向导旅程之间仍需要进一步压缩认知负担。

## 产品判断

命令体系应分为两层：

| 层级 | 命令 | 定位 |
|---|---|---|
| 主入口命令 | `init` | 面向所有用户的成熟度驱动向导入口 |
| 专家 / 自动化命令 | `assess`、`improve`、`benchmark`、`recommend-workflow`、`summarize-experience`、`review-maturity`、`generate-asset-candidates`、`self-improve` | 给专家用户、CI、脚本、acceptance 和未来 IDE / Runtime 集成直接调用，也可被 `init` 向导内部编排 |

普通用户不应被要求记住命令顺序。底层命令不隐藏，但产品文档和默认体验应主推 `init`。

这里的关键不是“用向导把已有命令串起来”，而是“向导本身就是目标产品体验”。如果现有 `assess`、`improve`、`benchmark`、候选治理、schema、报告或产物结构无法支撑向导式旅程，应根据向导目标反向补齐、调整或重组底层能力，而不是让向导迁就现有命令形状。

## 设计原则

1. `init` 是主入口。
   用户第一次进入和后续维护都应优先从 `init` 开始。首次 `init` 建立 Harness 基线；再次 `init` 应识别已有 `.ai`，进入状态感知维护入口，而不是无脑覆盖。

2. 成熟度是解释主线。
   扫描结果、生成资产、候选建议和下一步行动，都应围绕 L0-L4 成熟度框架解释。用户应知道当前处在哪个等级、为什么、证据是什么、下一阶段该补什么。

3. 向导组织底层能力。
   `assess`、`improve`、`benchmark`、`recommend-workflow`、`self-improve` 等命令是专家和自动化能力，也可以被向导内部编排。普通用户不应被要求记住命令顺序。

4. 向导是目标体验。
   向导不是现有命令的薄包装。底层能力如果缺少向导需要的状态摘要、成熟度解释、候选治理、下一步建议、schema 或 benchmark 契约，应围绕向导目标补齐。

5. 用户确认工程判断。
   交互中让用户确认的是技术栈、模块边界、团队规范、风险区域、Sensor 严格度、Workflow 建议和候选变更，而不是内部字段名。

6. 先解释，再选择。
   每个关键步骤都应说明发现了什么、依据是什么、影响是什么、用户可以怎么调整，再让用户确认、补充或跳过。

7. 默认建立基线，不默认自改进。
   首次 `init` 默认生成初版 Harness、成熟度评估、benchmark 和下一步建议；不默认执行 `self-improve` 或深度 LLM asset candidate generation，只在末尾提示后续可进入自演进。

8. 再次执行 `init` 是维护入口。
   如果已有 Harness，`init` 应先展示当前状态：成熟度、benchmark、待处理候选、pending improvements、human-input-needed 和 schema / contract 问题，再引导用户选择复评、更新、处理候选或退出。

9. 高风险内容保持候选态。
   高风险、低置信度、影响正式规则或 hard gate 的内容，不自动写入正式 Harness；应进入 candidate / review-only，并在写入前展示摘要。

10. 输出下一步，而不是甩文件列表。
   向导结束时应明确告诉用户下一步最该看什么、处理什么、为什么，而不是只列出 `.ai` 目录下的所有文件。

## 首次 init 目标流程

```text
harness-builder-agent init [--repo .]

1. 识别仓库
   - 默认 repo 为当前目录 `.`
   - 显式 `--repo` 仍作为高级用法保留

2. 扫描与初始成熟度评估
   - 扫描技术栈、模块、命令、文档、CI、风险线索
   - 给出初始成熟度等级和维度评分
   - 用中文解释证据和不确定项

3. 用户确认与补充
   - 确认或修正扫描结论
   - 收集团队规范、组织规范、架构边界、测试策略、安全合规要求
   - 把用户补充作为后续生成上下文

4. Harness 候选生成
   - 生成 Guides / Sensors / Workflow / risk zones / maturity evidence
   - 区分 confirmed、candidate、review-only

5. 成熟度缺口与下一阶段建议
   - 解释当前 Harness 能到哪个等级
   - 说明哪些阻断项让它不能升到下一等级
   - 推荐最值得补齐的能力

6. 用户审查和选择
   - 哪些 Guide / Sensor 接受
   - 哪些保持候选
   - 哪些风险或 hard gate 需要暂缓

7. 最终摘要与写入
   - 展示即将写入的内容
   - 展示待人工处理项
   - 写入 `.ai`
   - 运行 benchmark 或明确提示是否立即运行

8. 下一步入口
   - 告诉用户现在最应该打开哪个文件
   - 告诉用户下一步最应该处理什么
   - 轻提示后续可以在积累任务执行记录或评审反馈后使用自演进能力
```

首次 `init` 不默认进入：

- `self-improve`
- LLM maturity review
- 深度 asset candidate generation
- 正式 Harness 自动改写
- Runtime 任务执行
- `.ai/task-runs` 生成

## 再次执行 init 的目标流程

如果检测到目标仓库已有 `.ai`，`init` 应作为状态感知维护入口。

```text
1. 读取现有 Harness 状态
   - 当前成熟度等级和维度评分
   - 上次生成 / 更新时间
   - benchmark 状态
   - pending improvements
   - review-only candidates
   - human-input-needed
   - schema / contract 问题

2. 展示状态摘要
   - 当前 Harness 是否健康
   - 哪些地方已经做得不错
   - 哪些地方阻碍进入下一成熟度等级
   - 哪些候选或人工输入还没处理

3. 引导用户选择下一步
   - 重新扫描并更新 Harness
   - 重新评估成熟度
   - 查看下一步改进建议
   - 处理待确认候选
   - 运行 benchmark / 查看质量报告
   - 退出，不做修改

4. 默认不直接覆盖正式资产
   - 重新扫描产生的高风险变化进入 candidate / review-only
   - 用户确认后才写入正式 Harness
   - 写入前必须展示 diff / summary
```

## 体验样例

首次初始化完成时，向导应输出类似：

```text
第一版 Harness 已经生成完成。

当前成熟度：L2 - Executable Sensors

做得好的地方：
- 已发现可执行的测试命令。
- 已生成项目级 Guides 和 Sensors。
- 已生成 lightweight / bugfix / standard Workflow Skill。

主要阻断项：
- 风险区域还需要进一步确认。
- 部分 Sensor 还没有绑定到任务工作流。
- 任务执行后的经验沉淀还没有开始。

建议下一步：
1. 先查看 .ai/maturity-report.md，确认成熟度评分和缺口。
2. 查看 .ai/human-input-needed.md，补充团队规则和风险边界。
3. 查看 .ai/sensors/verification.md，确认哪些命令可以作为 hard gate。
4. 后续当你积累任务执行记录或评审反馈后，可以使用自演进能力生成 review-only 改进包，帮助 Harness 持续演进。
```

再次执行 `init` 时，向导应输出类似：

```text
我发现这个仓库已经存在 Harness。

当前成熟度：L2
最近 benchmark：passed，quality degraded，score 80
待处理候选：3 个
待补充人工信息：2 项

你接下来想做什么？
1. 重新扫描仓库并生成更新建议
2. 重新评估成熟度
3. 查看下一步改进建议
4. 处理待确认候选
5. 运行 benchmark
6. 退出
```

## 初步验收标准

未来实现该 todo 时，至少应满足：

- `init` 默认 repo 为当前目录，`--repo` 仍可显式覆盖。
- 首次 `init` 完成后，用户能看到成熟度等级、维度摘要、阻断项和下一步建议。
- 首次 `init` 不默认执行 `self-improve`、LLM maturity review、deep asset candidate generation 或 Runtime 任务执行。
- 首次 `init` 写入前有最终 summary，说明即将写入的正式资产、候选资产和待人工处理项。
- 如果已有 `.ai`，再次执行 `init` 不直接覆盖正式资产，而是先展示状态摘要和可选动作。
- 再次执行 `init` 至少能引导用户进入复评、重新扫描、查看建议、处理候选、运行 benchmark 或退出。
- 用户交互文案以中文解释性语言为主，不把内部字段名作为主要确认内容。
- `assess`、`improve`、`benchmark`、`recommend-workflow`、`self-improve` 等底层命令保留专家/自动化入口。
- 新增或变更的机器消费输出必须有 Pydantic schema 和测试。
- 集成或 e2e 测试覆盖首次 `init` 和已有 `.ai` 再次 `init` 的主路径。
- benchmark 或测试覆盖向导生成的关键产物，不只断言文件存在。

## 非目标

第一版不要求：

- 实现 GUI / Dashboard。
- 实现 IDE 插件。
- 实现宿主 AI Coding Runtime。
- 在 `init` 中默认执行 `self-improve`。
- 自动应用高风险候选或正式 Harness 变更。
- 为不同用户角色提供不同界面。

## 后续设计要求

进入 spec / plan 前，需要进一步明确：

- `init` 向导内部如何编排现有 `assess`、`improve`、`benchmark` 能力。
- 已有 `.ai` 状态摘要读取哪些文件，schema 损坏时如何显式失败或引导修复。
- “处理待确认候选”第一版是否只展示和指引，还是提供 apply/reject 交互。
- benchmark 在首次 `init` 末尾是默认执行，还是提示用户确认后执行。
- 非 TTY / `--non-interactive` 模式如何保留自动化兼容性。
