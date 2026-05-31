# 测试覆盖深度与 Acceptance 策略增强

## 状态

- 状态：implemented
- 优先级：high
- 发现日期：2026-05-30
- 相关命令：默认 pytest、`tests/acceptance`、本地 Git hooks、CI
- 相关工程规则：`docs/engineering/testing-strategy.md`

## 背景

当前默认测试共有 38 个，额外 acceptance 测试 2 个。对于当前代码规模和功能复杂度来说，默认测试数量和边界覆盖都偏少。

默认测试能证明主 happy path 可运行，但不少关键模块的失败路径、边界条件、schema 反例和生成内容质量还没有足够覆盖。

## 当前现状

当前默认测试分布：

```text
unit: 28
integration: 9
e2e: 1
default total: 38
acceptance: 2 extra
```

当前本地 hooks：

- `pre-commit` 运行 `.venv/bin/python -m pytest -q`。
- `pre-push` 运行 `.venv/bin/python -m pytest -q`。
- `scripts/check-ci.sh` 用于查看 GitHub Actions。

当前默认 pytest 不包含 `tests/acceptance`。

## 主要缺口

### Unit 层缺口

- `write_assets.py` 没有直接单元测试，主要靠 integration 间接覆盖。
- `benchmark.py` 体量较大，但失败分支覆盖不足。
- `run_task.py` 缺少 sensor failed/skipped/no command/缺 guide/缺 skill 等边界场景。
- `weapon_library.py` 缺少独立单元测试。
- `assess_maturity.py`、`generate_improvements.py` 主要测成功路径。
- 多个 schema 缺少正反例测试，例如 `BenchmarkReport`、`HarnessMap`、`SensorReport`、`MaturityReport`、`WeaponLibrarySelection`。
- CLI 测试命名和真实命令数量存在漂移，说明测试需要治理。

### Integration 层缺口

- `init` 主要覆盖 Java/.NET happy path。
- 缺少 LLM 失败、schema 失败、context 缺失、context 深度参与生成等场景。
- 缺少生成产物损坏后 benchmark 如何失败的集成测试。
- 缺少 `init` 默认当前目录运行的测试。

### E2E 层缺口

- 当前只有一个 fixture e2e 测试函数，虽然覆盖 Java 和 .NET，但场景数量有限。
- 缺少 unknown stack、缺测试命令、monorepo、多模块、大仓库采样等场景。

### Acceptance 层缺口

- Acceptance 只有 2 个测试。
- 真实 DeepSeek 只覆盖 Java fixture。
- 真实仓库验收依赖 `.benchmarks` 本地存在，但没有更细的环境说明和失败诊断。
- Acceptance 不在默认 hooks 中运行，重要提交或发布前容易被忘记。

## 理想状态

未来测试策略应区分：

```text
快速回归
  -> unit + integration + e2e fixture
  -> pre-commit / CI 默认运行

完整本地验收
  -> 快速回归 + acceptance
  -> pre-push 或发布前运行

真实仓库验收
  -> DeepSeek + .benchmarks/RuoYi-Vue + .benchmarks/eShopOnWeb
  -> 目标模式完成前必须运行
```

可以考虑新增脚本：

```bash
scripts/test-fast.sh
scripts/test-full.sh
scripts/test-acceptance.sh
```

并明确 hooks 采用哪一层。

## 初步验收标准

未来实现该 todo 时，至少应满足：

- 为 `write_assets.py` 或拆分后的 writer 增加单元测试。
- 为 benchmark 增加缺文件、schema 损坏、章节缺失、trace 损坏、skill 引用错误、hard gate failed/skipped 测试。
- 为 run task 增加 failed/skipped/no command/缺 guide/缺 skill 场景。
- 为主要 schema 增加正反例。
- 为 weapon library 增加独立选择测试。
- 增加 `init` 默认当前目录运行测试。
- 明确 acceptance 何时运行，缺 key 或缺真实仓库时如何失败。
- README、`docs/engineering/testing-strategy.md` 和 hooks 策略保持一致。

## 非目标

第一版不要求：

- 追求固定百分比覆盖率。
- 把所有 acceptance 强制放进 GitHub Actions 默认流程。
- 为每个私有 helper 函数写脆弱测试。

重点是补齐关键业务边界和失败路径，让测试能真正保护后续重构和交互式改造。

## 实现结果

- 已补充 CLI、schema、weapon library、asset writer、benchmark、run task、assess/improve 的关键测试。
- 默认回归测试从 38 个增加到 61 个。
- 已新增 `scripts/test-fast.sh`、`scripts/test-acceptance.sh`、`scripts/test-full.sh` 三层本地验证脚本。
- 已新增 `scripts/test-unit.sh`、`scripts/test-integration.sh`、`scripts/test-guided-init.sh`、`scripts/test-llm-contracts.sh` 和常用 acceptance 切片脚本，用于开发过程中的 targeted feedback。
- `pre-commit` 使用 `scripts/test-fast.sh`，并可用 `.pytest_cache/harness-builder-test-fast.stamp` 跳过重复 fast regression；`pre-push` 使用 `scripts/test-full.sh`。
- Acceptance 仍然显式运行，不进入默认 CI；缺少 key、真实仓库、网络或 API 可用性时必须失败。
- 已验证 `scripts/test-fast.sh` 通过。
- 已验证 `scripts/test-acceptance.sh` 在提升权限环境下通过，覆盖真实 DeepSeek 和真实开源仓库链路。
