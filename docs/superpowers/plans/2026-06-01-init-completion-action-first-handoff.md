# Init Completion 行动优先交付摘要计划

目标：让首次 `init` 写入完成后的终端摘要先完成成熟度与下一步行动交接，再展示生成清单和审计细节。

## 实施步骤

1. 更新 completion summary 测试
   - 在 `tests/unit/test_init_summary.py` 中增加 section 顺序断言，要求 `当前成熟度`、`建议下一步`、`Benchmark 健康度` 和 `优先查看` 都在 `本次已生成` 前。
   - 更新 guided init integration transcript 断言，防止未来重新把行动信息压回生成清单之后。
   - 先运行 targeted unit，确认 RED。

2. 调整 `render_init_completion_message()`
   - 保留现有 helper 和 section 标题。
   - 将输出顺序调整为：标题 / 输出目录 / 边界、当前成熟度、建议下一步、Benchmark 健康度、优先查看、本次已生成、主要证据 / 缺口、本次吸收的用户补充、仍需人工确认。
   - 不修改 `build_init_summary_markdown()`、schema、benchmark 或 Runtime 契约。

3. 同步长期文档和演进记录
   - 更新 `README.md` 中 completion output 描述，说明终端摘要先展示成熟度、下一步、benchmark 和入口，再列生成清单与补充审计。
   - 更新 `docs/engineering/init-workflow.md` 的 completion message 契约，沉淀行动优先顺序。
   - 在 `docs/evolution-log.md` 顶部新增本轮中文记录。

4. 验证
   - 运行 `tests/unit/test_init_summary.py`。
   - 运行相关 guided init integration 测试。
   - 运行 `git diff --check`。
   - 创建 commit 前运行 `scripts/test-fast.sh`。

## 非目标

- 不压缩或删除用户补充摘要。
- 不改变 `init-summary.md` 的 Markdown 章节顺序。
- 不修改 `.ai` schema、LLM 扫描、benchmark 规则或 Runtime 边界。
- 不 push；本轮只是一个本地独立切片，尚未形成需要同步远端的完整工作包。
