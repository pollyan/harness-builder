# Init Completion 用户补充紧凑摘要计划

目标：让首次 `init` completion message 的用户补充段从逐条明细改为“条数 + 示例 + source + 事实边界”，保持终端短交付摘要，同时保留审计入口。

## 实施步骤

1. 更新 completion summary 测试
   - 在 `tests/unit/test_init_summary.py` 增加多条 scan / team / workflow 补充场景。
   - 断言每类输出 `N 条；示例：第一条`。
   - 断言第二条 / 第三条明细不再出现在 completion message 中。
   - 先运行 targeted unit，确认 RED。

2. 调整 `_completion_user_supplement_lines()`
   - 新增小 helper 渲染单类补充摘要。
   - 有补充时每类只输出一行：类别、条数、首条示例。
   - 无补充、缺 interaction decisions、shown workflows、source 和事实边界保持现有语义。

3. 同步长期文档和演进记录
   - 更新 `README.md` 中 completion output 描述，从“列出补充明细”调整为“展示补充条数、示例、来源和事实边界”。
   - 更新 `docs/engineering/init-workflow.md` 的 completion message 契约。
   - 在 `docs/evolution-log.md` 顶部新增本轮中文记录。

4. 验证
   - 运行 targeted unit。
   - 运行 `tests/unit/test_init_summary.py`。
   - 运行相关 guided init integration。
   - 运行 `git diff --check`。
   - 创建 commit 前运行 `scripts/test-fast.sh`。

## 非目标

- 不改变 `init-summary.md` 的详细内容。
- 不删除用户补充审计入口。
- 不修改 `.ai` schema、LLM 扫描、benchmark 规则或 Runtime 边界。
- 不 push；本轮只是本地独立切片。
