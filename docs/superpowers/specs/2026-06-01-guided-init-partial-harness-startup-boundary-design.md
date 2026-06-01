# Guided Init 不完整 Harness 启动边界设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、`docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、最近 init / existing Harness 相关 spec / plan 列表、`interactive_init.py`、`guided_scan_presentation.py`、`prewrite_preview.py` 和 guided init integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/architecture.md`；本轮不修改 LLM、benchmark、Sensor gate、writer 架构或目录边界。
- open todo：`docs/todos/README.md` 显示当前没有 open todo。
- sub agent：按目标模式尝试启动 explorer 审查 partial `.ai` 状态，当前环境返回 `agent thread limit reached`；主线程继续调研并记录。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 不完整 `.ai` core 状态应在启动确认前说明 | 新发现 / init North Star 启动边界 / partial Harness 规则 | Maintainer 在第一次 `继续生成 Harness?` 前就知道仓库已有部分 `.ai` core 文件、为什么没有进入已有 Harness 维护入口、继续后会按首次 init 重新扫描且最终确认前不覆盖正式资产 | `show_scan_maturity_snapshot()` 和 prewrite preview 已用 `has_existing_partial_harness()` 把 partial core 解释为 L1 起步 | 启动说明阶段没有 partial core 提示；用户需要先同意扫描，之后才看到 partial L1 叙事；如果用户只是想确认是否已有 Harness，首次确认前信息不够 | 提升首次 guided init 的边界透明度，避免把 partial `.ai` 状态误认为全新 L0 或完整已有 Harness | 低；只改启动说明和测试，不改 schema、writer、LLM 或 existing Harness 正常入口 | integration 构造只有 `harness-config.yaml` 或只有 `project-inventory.json`，输入 `n` 取消，断言启动说明包含 present / missing、未扫描、未覆盖 | 无外部依赖 | CLI transcript、scan mock 未调用、formal core 文件未被覆盖 | 本轮 |
| B. 非交互 init LLM 网络失败时 CLI traceback 过长 | 上轮 full regression 观察 / 错误体验 | 自动化 `init --non-interactive` 失败时有明确错误和 trace，减少 Rich traceback 噪音 | acceptance 失败会暴露 DeepSeek DNS / URLError，并写失败 trace | 当前 CLI 会输出完整 Python traceback；但 non-interactive 自动化路径不承担 guided CLI 进度展示契约，且 acceptance 需要保留失败细节 | 改善自动化可读性 | 中；涉及 Typer exception 行为、acceptance stderr、测试契约和真实失败诊断 | CLI integration 可 mock scan 异常；acceptance 仍依赖网络 | 需要更明确产品取舍，避免隐藏调试信息 | 下一轮候选 |
| C. push 前 full regression / 远端同步 | Git 状态 / 提交规则 | 本地 ahead commit 通过 full 后 push GitHub | 当前本地 `.env` 已有 key，`.benchmarks` 存在，fast 通过 | sandbox 下 acceptance 仍无法解析 `api.deepseek.com`；非 sandbox 会向 DeepSeek 发送 fixture / benchmark evidence，需要明确外部数据发送授权 | 同步远端，降低本地分叉 | 外部网络和数据外发权限阻塞 | `scripts/test-full.sh` + push | 外部服务 / 授权 | 继续作为 push gate，不作为本轮功能 milestone |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 的启动与目标说明：用户在等待扫描前就应知道流程边界和现有资产状态。改动小、可本地测试、不会触碰 LLM / schema / Runtime。
2. B 暂不选。它来自真实 full regression 观察，但属于非交互自动化错误呈现，和短期 guided init 主体验相比优先级略低，也需要更谨慎确认是否改变 traceback 调试语义。
3. C 仍是 push gate；本轮完成后按规则再次运行 full 并评估。

本轮 milestone：

作为 Harness Maintainer，当我对一个已有不完整 `.ai` core 文件的仓库运行默认 guided `init` 时，我可以在第一次确认继续前看到哪些核心 Harness 文件已存在、哪些缺失、为什么不会进入已有 Harness 维护入口，以及继续后仍不会在最终确认前覆盖正式资产，从而能决定是继续扫描还是先取消备份。

## 设计

- 将 `_show_guided_init_startup_boundary()` 改为接收 `repo`。
- 如果 `.ai/project-inventory.json` 与 `.ai/harness-config.yaml` 不是同时存在，但至少一个存在：
  - 在启动说明中追加“不完整 Harness 状态”提示。
  - 展示 present core files 和 missing core files。
  - 说明因 core files 不完整，本次不会进入已有 Harness 维护菜单。
  - 说明继续后会按首次 init 重新扫描，最终 `confirm` / `确认` 前仍不会覆盖正式 Harness 资产；如需保留现有 `.ai`，应取消并备份。
- 保持后续扫描成熟度初评和 prewrite preview 里的 L1 partial Harness 叙事不变。

## 非目标

- 不改变完整已有 Harness 的维护入口触发条件。
- 不自动修复 partial `.ai`。
- 不新增 `--force` / `--repair` 参数。
- 不改变 writer 覆盖语义、schema、LLM、benchmark 或 Runtime 分工。

## 验收标准

- RED：新增 integration 先证明只有 `.ai/harness-config.yaml` 时，启动说明不会在第一次确认前展示 partial core present / missing。
- 实现后：
  - partial core 状态在 `继续生成 Harness?` 前展示。
  - 输出列出已存在 `.ai/harness-config.yaml` 和缺失 `.ai/project-inventory.json`。
  - 输出说明不会进入已有 Harness 维护入口、继续后按首次 init 重新扫描、最终确认前不覆盖正式 Harness 资产。
  - 用户输入 `n` 取消时不调用 `scan_repository`。
  - 已存在的 partial core 文件不被覆盖，缺失 core 文件仍不存在。
  - 没有 partial core 的 happy path 启动说明保持原有语义。
  - `tests/integration/test_init_on_fixture_projects.py` targeted、guided init integration、`compileall`、`git diff --check`、`scripts/test-fast.sh` 通过。

## Assumptions / Risks

- Assumption：partial core 文件是用户需要在首次确认前知道的风险边界；`.ai/runs` trace 目录不应被当作 partial Harness core。
- Assumption：同时存在 inventory 和 config 才是完整已有 Harness 维护入口；只有一个 core 文件时继续走首次 init，但必须透明告知。
- Risk：启动说明稍微变长；只在 partial core 存在时展示，避免污染普通 happy path。
