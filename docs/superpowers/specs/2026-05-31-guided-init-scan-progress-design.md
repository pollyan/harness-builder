# Guided Init 扫描进度反馈设计

## 背景

`docs/strategy/init-north-star.md` 明确要求 `init` 的扫描阶段不能长时间静默。当前首次 guided `init` 在用户确认继续后直接调用 `scan_repository(repo)`，直到扫描完成才展示“扫描发现”。在真实仓库和真实 LLM 场景下，这个阶段可能持续较久；如果 LLM、网络或 schema 校验失败，用户只能看到异常，缺少“失败发生在扫描阶段、尚未写入正式 Harness 资产”的边界说明。

本轮处于用户授权的目标模式：过程文档记录需求和决策，但不等待额外人工确认。

## 用户故事

作为 Harness Maintainer，当我首次运行 guided `harness-builder-agent init --repo <repo>` 并确认继续后，我希望在耗时扫描开始前看到阶段化进度说明，并在扫描失败时知道失败发生在扫描阶段且未写入正式 `.ai` Harness 资产，从而判断程序仍在工作、失败边界清晰，并能继续排查 LLM 配置、网络或仓库扫描问题。

## 范围

本轮只改首次 guided `init` 的扫描阶段体验。

包含：

- 在调用 `scan_repository(repo)` 前输出扫描阶段标题和将要执行的阶段说明。
- 扫描成功后输出完成提示，说明已经完成 evidence 收集、LLM 结构化分析和调和。
- 扫描失败时输出稳定的中文失败边界提示，并继续显式抛出原异常。
- 保持非交互 `--non-interactive` 语义不变。
- 增加 integration 测试覆盖成功路径和失败路径。

不包含：

- 不拆分 `scan_repository()` 内部 pipeline。
- 不增加精确百分比或真实 callback。
- 不改变 DeepSeek / LLM 失败策略。
- 不写入 `.ai/task-runs`，不恢复任何 `run` 能力。
- 不改变扫描结果、成熟度评分、Guide / Sensor 生成逻辑。

## 设计

在 `src/harness_builder_agent/tools/interactive_init.py` 中新增小型渲染函数：

- `_show_scan_progress_start(repo: Path) -> None`
- `_show_scan_progress_completed(inventory: ProjectInventory, commands: CommandCatalog) -> None`
- `_show_scan_progress_failed() -> None`

`run_guided_init()` 在用户确认继续后、`trace.event("scan", "started", ...)` 之前调用 start 渲染；扫描成功并记录 completed trace 后调用 completed 渲染；扫描异常时记录 scan failed trace、输出 failed 渲染并重新抛出异常。

失败处理只增加可解释性，不吞异常，不把失败改成成功，也不制造 fallback。

## CLI 文案契约

成功路径至少包含：

- `扫描仓库`
- `正在收集仓库文件、构建配置、CI、测试和文档证据`
- `正在请求 LLM 做结构化扫描`
- `正在调和 LLM 判断与 evidence`
- `扫描完成`

失败路径至少包含：

- `扫描阶段失败`
- `未写入正式 Harness 资产`
- `请检查 LLM 配置、网络或扫描错误后重试`

这些文案用于 integration 测试，后续如需大幅改写需同步测试和 `docs/engineering/init-workflow.md`。

## 验收标准

1. guided init happy path 中，`扫描仓库` 出现在 `扫描发现` 之前，`扫描完成` 也出现在 `扫描发现` 之前。
2. 当 `scan_repository()` 在 guided init 中抛错时，CLI 输出先出现 `扫描仓库`，再出现 `扫描阶段失败`，并包含原始异常信息。
3. 扫描失败时不写入正式 `.ai/project-inventory.json`、`.ai/harness-config.yaml`、Guides、Sensors 或 Workflow Skills。
4. `--non-interactive` 路径不新增 guided CLI 进度文案断言，不改变自动化兼容语义。
5. 相关 guided init integration、fast regression 和 full regression 通过。
