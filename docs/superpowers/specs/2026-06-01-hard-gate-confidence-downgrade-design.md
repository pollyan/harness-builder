# Hard Gate 置信度降级设计

## 用户故事

作为 Harness Maintainer，当我对一个仓库运行 `harness-builder-agent init --non-interactive` 后，我可以得到不会自相矛盾的初始 Harness：低置信度或证据不足的验证命令不会被写成 hard gate，从而避免刚生成的 Harness 立刻因为 Builder 自己的 hard gate 契约在 `benchmark` 中失败。

## 当前问题

`benchmark` 已经正确要求 hard gate command 必须有真实 source 且 confidence 不能是 `low`。但 `scan_reconciler` 目前只在 hard gate 缺少 evidence 时降级；如果 LLM 返回 `gate=hard`、`source=pom.xml`、`confidence=low`，该命令会保留为 hard gate。随后 `benchmark` 会报告 `content:hard-gate-command-evidence` 失败。

## 目标行为

- LLM 或人工补充给出的 `gate=hard` 命令，只有在 source 有 evidence 且 confidence 至少为 `medium` 时才能保留为 hard gate。
- `confidence=low` 的 hard gate 必须在调和阶段降级为 `soft`，并保留 `confidence=low`。
- 降级必须写入 scan warning，驱动 CLI、human-input 和后续审计提示 Maintainer 补充证据或确认命令稳定性。
- `benchmark` 继续保持严格：如果已有 Harness 或手工修改后的 command catalog 仍包含 low-confidence hard gate，仍应失败。

## 非目标

- 不放宽 `benchmark` hard gate 检查。
- 不把低置信度命令静默提升成 medium/high。
- 不运行真实验证命令来推断稳定性。
- 不修改 Runtime task-run 产物契约。

## 验收标准

- 新增单元测试证明 low-confidence hard gate 会在 `reconcile_scan()` 中降级为 `soft`。
- 现有 benchmark 对 low-confidence hard gate 的失败测试继续通过。
- README 和工程规则说明生成阶段会把低置信度 hard gate 降级为 soft，benchmark 仍拒绝遗留或手工引入的 low-confidence hard gate。
