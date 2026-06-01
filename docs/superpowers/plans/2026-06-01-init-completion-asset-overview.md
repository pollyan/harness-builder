# Init Completion 资产概览压缩计划

目标：把首次 `init` completion message 的 `本次已生成` 从逐项文件状态清单压缩为资产类型概览，保持行动优先和可审计边界。

## 实施步骤

1. 写 RED 测试
   - 更新 / 新增 `tests/unit/test_init_summary.py` 断言。
   - 覆盖完整 `.ai` 时 `本次已生成` 只展示紧凑资产类型概览、ready count 和完整清单入口。
   - 覆盖缺失核心文件时显示 missing detail。
   - 先运行 targeted unit，确认旧 8 行逐项清单导致测试失败。

2. 修改 `init_summary.py`
   - 将 `_generated_asset_summary()` 改为按固定资产组渲染：
     - 核心机器契约。
     - 语义控制资产。
     - 审查 / 经验资产。
     - 运行审计入口。
   - 每组输出 `ready=<n>/<total>`。
   - 有缺失时输出最多 3 个 missing path。
   - 始终指向 `.ai/init-summary.md` 和 `.ai/runs/*/artifacts.yaml`。

3. 更新长期文档
   - README 中首次 init completion 描述改为“生成资产类型概览和详细审计入口”。
   - `docs/engineering/init-workflow.md` 中 completion message 契约同步。

4. 记录演进
   - 更新 `docs/evolution-log.md`，保留 Gap Analysis 摘要、用户故事、验证结果和 Self-Harness Gate。

5. 验证
   - 运行 targeted `tests/unit/test_init_summary.py`。
   - 运行相关 guided init integration。
   - 运行 `git diff --check`。
   - 提交前运行 `scripts/test-fast.sh`。

## 非目标

- 不改变 `.ai` 实际生成文件。
- 不改变 `init-summary.md` 持久化章节。
- 不修改 schema、benchmark、LLM、scan 或 Runtime 分工。
- 不 push；本轮只是本地用户体验切片。
