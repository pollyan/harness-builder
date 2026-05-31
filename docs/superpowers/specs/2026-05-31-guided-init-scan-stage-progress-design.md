# Guided Init 扫描内部阶段进度设计

## 背景

`docs/strategy/init-north-star.md` 要求扫描阶段不能长时间静默，并应按阶段输出当前阶段、已完成阶段和下一阶段。当前 guided `init` 已有扫描前说明和扫描完成提示，但 `scan_repository()` 内部的 evidence 收集、LLM evidence plan、补充 evidence 读取、最终 LLM scan 和 scan reconcile 仍是一个阻塞调用。真实仓库和真实 DeepSeek 场景下，用户仍无法知道耗时发生在哪个内部阶段。

本轮处于用户授权的全自动目标模式：过程文档记录 assumptions / decisions / risks，但不等待额外人工确认。

## Current State Gap Analysis

候选 gap 排序：

1. **扫描内部阶段 progress callback**  
   - 目标态：guided init 在 `collect evidence -> LLM evidence plan -> evidence expansion -> LLM scan -> reconcile` 每个关键阶段输出状态。  
   - 当前能力：只有扫描开始和扫描完成提示。  
   - 价值：直接服务真实仓库和真实 LLM 等待体验，让用户知道程序在工作和耗时来自哪里。  
   - 风险/复杂度：中低；可通过 keyword-only optional callback 保持兼容。  
   - 可测试性：高；unit 可断言事件序列，guided integration 可断言中文阶段文案。
2. **生成资产 Markdown 中保留推荐项成熟度来源**  
   - 价值高，但涉及 asset writer 和内容契约，范围更大。
3. **更深的智能 evidence expansion UI**  
   - 需要更大设计和可能新增中间结果展示，先不做。

本轮选择第 1 项。

## 用户故事

作为 Harness Maintainer，当我首次 guided `init` 一个真实遗留仓库且扫描和 LLM 调用需要等待时，我可以在 CLI 中看到正在收集 evidence、请求 LLM 规划补充 evidence、读取补充 evidence、请求最终 LLM scan 和调和扫描结果的阶段状态，从而判断程序仍在工作，并能在失败时定位失败发生在哪个阶段。

## 范围

包含：

- 给 `scan_repository()` 增加可选 keyword-only `progress` callback，默认 `None`。
- 进度事件覆盖：
  - `collect-evidence`
  - `plan-evidence-expansion`
  - `expand-evidence`
  - `llm-scan`
  - `reconcile-scan`
- guided `init` 传入 renderer，把事件翻译成中文 CLI 行。
- `--non-interactive` 不传 progress，自动化输出不变。
- unit 测试事件序列；guided integration 测试用户可见 transcript。

不包含：

- 不改变 `scan_repository()` 返回值。
- 不改变 LLM prompt、schema、reconciler 或 evidence collector 逻辑。
- 不吞异常、不重试、不 fallback。
- 不落盘新的机器消费产物。

## 设计

新增轻量数据结构：

```python
@dataclass(frozen=True)
class ScanProgressEvent:
    phase: str
    status: Literal["started", "completed"]
    message: str
    details: dict[str, object] = field(default_factory=dict)
```

`scan_repository(..., progress: ScanProgressCallback | None = None)` 在每个阶段前后调用 `_emit_progress()`。`progress` 只用于用户体验和测试观察，不参与业务决策。

guided `init` 新增 `_guided_scan_progress(event)`：

- `started` 输出 `- 当前阶段：...`
- `completed` 输出 `  已完成：...`
- 输出阶段名使用中文，不包含 prompt、原始 LLM 响应、API key、base URL 或大段 evidence。

为了兼容现有测试中大量 `monkeypatch interactive_init.scan_repository = lambda repo_path: ...`，guided init 通过 helper `_scan_repository_for_guided_init()` 检查当前 `scan_repository` callable 是否支持 `progress` 参数：

- 支持则传 `progress=_guided_scan_progress`。
- 不支持则按旧签名调用，并保留扫描前/后提示。

这避免破坏旧测试和外部直接 monkeypatch，同时真实 `scan_repo.scan_repository` 会启用内部阶段进度。

## Assumptions / Risks

- progress callback 是非机器契约；不需要 Pydantic schema。
- 事件 id 会进入单元测试契约，后续改名需同步测试和文档。
- 兼容旧 monkeypatch 是必要的，因为 integration tests 当前大量使用单参数 fake scan。
- 如果某个阶段失败，最后一个 started 事件就是定位线索；异常仍由原逻辑显式抛出。

## 验收标准

1. `scan_repository()` unit test 能观察到完整事件序列：`collect-evidence started/completed`、`plan-evidence-expansion started/completed`、`expand-evidence started/completed`、`llm-scan started/completed`、`reconcile-scan started/completed`。
2. guided init happy path 在 `扫描仓库` 与 `扫描完成` 之间输出中文内部阶段：收集仓库 evidence、请求 LLM 规划补充 evidence、读取 LLM 请求的补充 evidence、请求 LLM 做最终结构化扫描、调和扫描结果。
3. 使用旧单参数 fake `scan_repository` 的 guided integration tests 继续通过。
4. 非交互 `--non-interactive` 输出不新增 guided 阶段文案。
5. LLM 失败、schema 失败和 scan conflict 仍显式失败，没有 fallback。
6. 相关 unit / integration、`scripts/test-fast.sh` 和 push 前 `scripts/test-full.sh` 通过。
