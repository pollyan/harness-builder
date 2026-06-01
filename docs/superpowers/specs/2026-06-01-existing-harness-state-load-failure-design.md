# Existing Harness 状态读取失败保护设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、最近 existing Harness 相关 spec / plan、`src/harness_builder_agent/tools/interactive_init.py`、`src/harness_builder_agent/cli.py` 和 existing Harness integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`；本轮不修改 LLM prompt / schema、benchmark checks、Sensor gate 或模块边界。
- open todo：`docs/todos/README.md` 显示当前没有 open todo。
- sub agent：按目标模式尝试启动只读 explorer 审查 existing Harness 读取失败边界，当前环境返回 `agent thread limit reached`；主线程继续调研并在本 spec 记录。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 已有 Harness 核心状态损坏时友好失败 | 新发现 / no silent fallback / init North Star 已有 Harness 维护入口 | Maintainer 再次运行 guided `init` 时，如果 `.ai/project-inventory.json`、`.ai/harness-config.yaml` 或 `.ai/maturity-score.yaml` 损坏，CLI 明确说明读取失败、指出文件、说明未扫描且未覆盖正式资产，并以失败 trace 结束 | 已有 Harness 入口会先读 inventory/config/score，再展示维护摘要和菜单；正常路径已有大量 integration 覆盖 | 读取和 schema 校验直接内联执行；JSON/YAML/schema 错误会冒泡到外层 `init failed`，用户可能看到 Python 异常，trace 缺少 existing-harness 阶段定位 | 保护维护入口可信度；损坏状态是 Harness 生命周期中真实可见的维护场景，必须比 traceback 更可行动 | 低到中；只封装读取失败，不修复文件、不 fallback、不改 schema；需注意不要把缺少核心文件误判为已有 Harness | integration 先制造损坏 config / score，断言当前 RED：缺少友好提示；实现后断言输出、trace、无扫描、正式资产不被覆盖 | 无外部依赖 | CLI transcript、trace summary / event、scan mock 未调用、正式资产快照 | 本轮 |
| B. guided scan 失败输出去 traceback 化复核 | 上一轮 Gate / init-workflow 扫描失败边界 | 扫描阶段失败时 CLI 不展示 traceback，只展示阶段、原因、未写入边界和建议 | `run_guided_init()` 已对 scan 异常输出中文失败说明并 `typer.Exit(1)` | 需要系统性确认所有扫描子阶段错误都不会被外层重复记录；但当前已有明确实现和规则 | 能进一步增强首次 init 错误体验 | 中；可能涉及 LLM / network / schema 多类异常和 acceptance | targeted integration / unit 模拟 scan 异常 | 需要挑具体缺口，不能泛泛复核 | 下一轮候选，需重新找未覆盖错误类别 |
| C. push 前 full regression / 远端同步 | Git 状态 / 提交规则 | 本地 ahead commit 通过 full 后 push GitHub | 当前 `.env` 已有 DeepSeek key，`.benchmarks` 本地存在，fast 通常可通过 | sandbox 下 acceptance DNS 失败；非 sandbox full 会向 DeepSeek 发送 fixture / benchmark evidence，仍需要明确外部数据发送授权 | 远端同步本地工作 | 外部网络和数据外发权限阻塞 | `scripts/test-full.sh` + push | 需要用户明确授权外发 evidence | 继续作为 push gate，不作为本轮功能 milestone |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 的“再次进入已有 Harness”旅程，且与 no silent fallback、CLI 友好失败、正式资产不覆盖边界强相关；可以用本地 integration 清楚验收。
2. B 暂不选。扫描失败已有专门处理，缺口需要更具体证据；本轮优先修已经定位到的 existing Harness 读取入口。
3. C 仍是 push gate，不是功能 milestone；本轮完成后按规则再次运行 full 并评估是否可 push。

本轮 milestone：

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness，但核心 `.ai` 状态文件已经损坏或不符合 schema 时，我可以看到明确、中文、可行动的读取失败说明，并确认 Builder 没有重新扫描或覆盖正式资产，从而能先修复 Harness 状态再继续维护。

## 设计

- 新增局部读取辅助：
  - 检测已有 Harness 的核心文件仍保持原规则：只有 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml` 同时存在才进入维护入口。
  - 进入维护入口后，统一读取并 schema 校验 `project-inventory.json`、`harness-config.yaml` 和可选 `maturity-score.yaml`。
  - 任一读取、YAML/JSON 解析或 Pydantic 校验失败时抛出带 source path、error type 和短错误摘要的内部异常。
- `_handle_existing_harness_entry()` 捕获该内部异常：
  - 输出 `已有 Harness 读取失败`。
  - 指出损坏文件。
  - 说明未重新扫描、未覆盖正式 Harness 资产、未创建 Runtime 产物。
  - 建议修复该文件后重试，或备份 `.ai/` 后显式选择重新初始化。
  - trace 记录 `existing-harness` failed event，并以 `existing_harness_action=load-state`、`error=existing_harness_state_invalid` 结束。
  - `raise typer.Exit(1)`，避免外层泛化 `init failed` 和 Python traceback。

## 非目标

- 不自动修复损坏 JSON/YAML。
- 不把损坏状态 fallback 成重新扫描或 `reinit`。
- 不改变已有 Harness 正常菜单、编号、action、triage、benchmark 或 review 逻辑。
- 不改变 `.ai` 机器契约 schema。
- 不执行 Runtime，不创建 `.ai/task-runs`。

## 验收标准

- RED：新增 integration 先证明损坏 `.ai/harness-config.yaml` 时不会出现本轮要求的中文读取失败说明。
- 实现后：
  - 损坏 `.ai/harness-config.yaml` 时 guided `init` 以退出码 1 结束。
  - CLI 输出 `已有 Harness 读取失败`、损坏文件、未重新扫描 / 未覆盖正式 Harness 资产 / 未创建 Runtime 产物。
  - 输出不进入 `== 启动说明 ==`、不进入 `== 初始化完成 ==`，不展示维护动作菜单。
  - `scan_repository` mock 不被调用。
  - 既有正式资产快照除被测试故意损坏的文件外不变化。
  - trace status 为 `failed`，summary 包含 `existing_harness_action=load-state`、`error=existing_harness_state_invalid`、source path 和 error type。
  - 可选 `maturity-score.yaml` 损坏时也同样友好失败，避免把成熟度状态损坏静默当作“未发现 maturity-score”。
  - existing Harness 正常 exit / unknown action 回归通过。
  - `tests/integration/test_init_on_fixture_projects.py` targeted、guided init integration、`compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：核心 config / inventory 损坏时，继续维护动作不可信；显式失败比自动 reinit 更安全。
- Assumption：`maturity-score.yaml` 虽是可选文件，但一旦存在且损坏，就应显式失败；否则用户会误以为成熟度只是缺失。
- Risk：用户可能希望从损坏状态直接进入 `reinit`。本轮选择安全优先，要求先修复或备份 `.ai/`，避免自动覆盖正式资产。
- Risk：错误摘要过长会污染 CLI；实现会截断单行摘要，完整细节仍可通过 trace 查看。
