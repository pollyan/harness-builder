# Human Input 处理方式 Benchmark 深度校验实施计划

## 目标

让 `benchmark` 的 `content:human-confirmation` 从标题级检查升级为处理方式契约检查，保护 `.ai/human-input-needed.md#处理方式` 的 scan follow-up 示例、人工治理入口和 Runtime 边界。

## 步骤

1. RED 测试
   - 在 `tests/integration/test_benchmark_command.py` 增加正向测试：包含 scan follow-up 的 generated human-input 通过 `_human_confirmation_checks()`。
   - 增加负向测试：删除 `module=...` / `review-human-input --interaction-id ... --decision resolved` / `## 处理方式` 等关键内容后，`content:human-confirmation` 失败并保留 `missing` detail。
   - 增加完整 `run_benchmark()` 负向测试，证明 persisted artifact 漂移会让 report `status=failed`。

2. 实现 helper
   - 在 `scan_followup_guidance.py` 增加 `scan_followup_required_guidance_snippets(question)`，返回 benchmark 可稳定校验的关键片段。
   - 保持现有 CLI / Markdown 文案 helper 不变，避免用户可见输出漂移。

3. 实现 benchmark 检查
   - 在 `benchmark.py` 复用 required snippet helper。
   - `_human_confirmation_checks()` 构建 `missing` 列表，校验稳定章节、runtime boundary、基础问题 id、scan follow-up per-id 内容、显式 `review-human-input` resolved 命令和 required snippets。
   - 对 resolved follow-up 只要求 resolved / reopened 边界，不要求重新补充示例。

4. 文档与记录
   - 更新 `README.md` 和 `docs/engineering/sensor-and-gate-rules.md` 的 benchmark 说明。
   - 如 `docs/engineering/init-workflow.md` 已足够，只做必要补充。
   - 更新 `docs/evolution-log.md`。

5. 验证
   - 先运行新增 targeted 测试，确认 RED 后实现为 GREEN。
   - 运行相关 human confirmation / benchmark tests。
   - 运行 `python -m compileall src tests`、`git diff --check`。
   - commit 前运行 `scripts/test-fast.sh`。
   - 本轮不 push；push 仍需 full regression。
