# Test Loop Slices Design

## 工程信任故事

作为 Harness Builder 维护者或目标模式 Codex，当我在一轮小功能中只修改某类能力时，我可以运行命名清晰的测试切片，并让 pre-commit 复用刚刚通过的 fast regression，从而缩短反馈循环，同时不削弱 push 前 full / acceptance 验收边界。

## Current State Gap Analysis

- North Star 要求 Harness Builder 持续演进，并用 Sensors / Benchmark / 验证机制支撑工程信任；目标模式的迭代速度直接影响持续演进能力。
- 当前 `scripts/test-fast.sh` 是唯一默认快速入口，会一次跑完 unit / integration / e2e；本轮实际验证显示它约 6 秒，但 commit hook 可能重复运行，目标模式连续小步提交会放大成本。
- `scripts/test-acceptance.sh` 支持透传 pytest target，但 README 没有提供常用 LLM smoke、真实仓库、self-improve acceptance 的命名入口。
- 当前工作树已有部分脚本切片草稿，但缺少测试保护、README / engineering docs 更新和演进记录。
- 草稿中的 fast stamp 写入 `.git/harness-builder-test-fast.stamp`，在 Codex sandbox 下会因 `.git` 写入受限导致 `scripts/test-fast.sh` 测试已通过但命令失败；stamp 应写入 ignored workspace cache。
- `.githooks/pre-commit` 直接执行在当前 Codex sandbox 会被 signal 9 杀掉；该问题与本轮脚本内容无关，手动 `bash .githooks/pre-commit` 正常。本轮不重构 hooksPath，但必须避免脚本自身依赖 `.git` 写入。

## 目标

- 新增并文档化常用测试切片脚本：
  - `scripts/test-unit.sh`
  - `scripts/test-integration.sh`
  - `scripts/test-guided-init.sh`
  - `scripts/test-llm-contracts.sh`
  - `scripts/test-acceptance-llm-smoke.sh`
  - `scripts/test-acceptance-real-repo.sh`
  - `scripts/test-acceptance-self-improve.sh`
- 抽取共享 shell helper，统一 Python 选择和 pytest 调用。
- `scripts/test-fast.sh` 在无 pytest target 时写入 fast stamp；带 target 时只运行目标测试，不刷新 whole-tree stamp。
- pre-commit 先比较 fast stamp，匹配时跳过重复 fast regression；不匹配时运行 `scripts/test-fast.sh`。
- fast stamp 写入 `.pytest_cache/harness-builder-test-fast.stamp`，避免 `.git` 写权限问题，并保持不提交缓存。
- 用 unit 测试覆盖脚本语法、关键契约、stamp 行为和 README 文档入口。

## 非目标

- 不改变 `scripts/test-full.sh` 的语义；push 前仍必须运行 full。
- 不让 acceptance 进入默认 CI 或 pre-commit。
- 不跳过、mock 或弱化真实 DeepSeek acceptance；缺 key / 缺仓库仍应失败。
- 不解决当前 Codex sandbox 直接执行 `.githooks/pre-commit` 被 signal 9 的平台限制；Codex 仍按 AGENTS.md 主动运行验证。

## 设计

### 脚本分层

`scripts/lib-test-env.sh` 提供：

- `hb_select_python`
- `hb_run_pytest`
- `hb_fast_fingerprint`
- `hb_fast_stamp_path`
- `hb_write_fast_stamp`
- `hb_fast_stamp_matches`

脚本切片只负责选择默认 pytest target，额外参数原样透传。

### Stamp 契约

`hb_fast_fingerprint` 基于 HEAD、tracked staged 文件、untracked 非 ignored 文件和工作树内容计算 hash。`scripts/test-fast.sh` 完整运行后写入 `.pytest_cache/harness-builder-test-fast.stamp`。pre-commit 只在 stamp 指纹匹配当前工作树时跳过重复 fast regression。

### 文档

README 和 `docs/engineering/testing-strategy.md` 补充“开发循环切片”和“full / acceptance 边界不变”。`docs/todos/testing-coverage-and-acceptance-strategy.md` 的 implemented 结果更新为包含切片脚本。

## 验收标准

- unit 测试覆盖新增脚本 `bash -n` 语法。
- unit 测试覆盖 README 列出所有新增切片脚本。
- unit 测试覆盖 `hb_fast_stamp_path` 不指向 `.git`，且 stamp 写入后能匹配，工作树内容变化后失配。
- targeted shell 测试覆盖 `scripts/test-unit.sh --version`、`scripts/test-integration.sh --version`、`scripts/test-guided-init.sh --collect-only`、`scripts/test-llm-contracts.sh --collect-only` 可运行。
- `scripts/test-fast.sh` 通过，并能写入 `.pytest_cache` stamp。
- 本轮不运行真实 acceptance；未修改 LLM/真实仓库验收语义，push 前仍由 `scripts/test-full.sh` 覆盖。

## Decisions / Responses

- 价值切分：这是工程信任故事，不是单纯加脚本；它降低目标模式每轮验证成本，保护持续演进效率。
- 边界回应：切片脚本只加速开发反馈，不替代 commit 前 fast、push 前 full 和真实 acceptance。
- 风险回应：fast stamp 必须基于当前工作树指纹，不能按时间戳盲跳过。
- 环境回应：stamp 放 `.pytest_cache`，避免 `.git` 写入权限导致测试通过但脚本失败。

## Assumptions / Risks

- 假设 `.pytest_cache/` 已被 `.gitignore` 忽略，适合作为本地验证缓存。
- 风险是脚本数量增加导致入口分散；README 使用“常用开发切片”集中说明。
- 风险是用户误把 targeted acceptance 当 full acceptance；文档必须明确 targeted 只用于开发反馈。
