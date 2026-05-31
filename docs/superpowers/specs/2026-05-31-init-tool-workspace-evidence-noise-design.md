# Init 工具工作区 Evidence 降噪设计

## 关联 Todo

- `docs/todos/guided-init-ai4se-real-repo-findings.md`
- 本轮只处理其中的第一类问题：`.claude/worktrees`、`.opencode`、`deploy-package/.opencode` 等 AI 工具工作区或历史工具产物中的 manifest 不应成为主项目判断依据。

## Current State Gap Analysis

目标态：

- `init` 扫描真实多栈仓库时，CLI 的“判断依据”和 LLM 的优先 evidence 应围绕根目录配置、主应用目录、README、CI、真实源码入口和测试入口。
- AI 工具工作区、临时 worktree、工具缓存和部署包里的工具目录可以作为轻量文件索引存在，但不能被当作主项目 build evidence。
- 对 Python / Flask + React / TypeScript 这类仓库，至少应把 `pyproject.toml`、`requirements.txt` 等 Python 项目文件纳入关键 evidence，避免只因工具目录里的 `package.json` 把项目理解牵引到 Node。

当前能力：

- `evidence_collector._walk_files()` 只忽略 `.git`、`.ai`、`.venv`、`node_modules`、`target`、`bin`、`obj`、`dist`、`build`、`__pycache__`。
- `evidence_collector._bucket_for()` 先判断 `_is_key_file()`，因此 `.claude/worktrees/x/package.json`、`.opencode/package.json`、`deploy-package/.opencode/package.json` 会和根目录 `package.json` 一样进入 `build` bucket。
- `_select_by_bucket()` 在 bucket 内按路径字典序排序，隐藏目录里的 manifest 可能排在根 manifest 前面。
- `scan_reconciler.reconcile_scan()` 把 `evidence.key_files` 原样写入 `ProjectInventory.evidence`，guided CLI 的“判断依据”又优先展示 `inventory.evidence[:6]`。

缺口：

- 工具工作区 evidence 既没有被忽略，也没有被降权或标记 secondary。
- Python 项目关键文件还没有进入 `KEY_FILE_NAMES`，真实多栈仓库容易被 Java/.NET/Node 之外的噪声 evidence 放大。
- 当前测试没有覆盖“工具目录 package.json 不进入 key evidence”这个信任边界。

## 用户故事

作为 Harness Maintainer，当我在包含 `.claude/worktrees`、`.opencode`、`deploy-package/.opencode` 等工具目录的真实仓库上运行 guided `init` 时，我可以看到主项目根目录和真实应用文件作为优先判断依据，而不是工具工作区里的 `package.json`，从而相信 Harness Builder 正在理解我的项目，而不是理解 AI 工具留下的临时产物。

## 设计决策

### 1. 明确忽略 AI 工具工作区目录

在 evidence 收集阶段把以下目录加入忽略集合：

- `.claude`
- `.opencode`

它们可以出现在任意层级，例如 `deploy-package/.opencode/package.json`。本轮不忽略整个 `deploy-package`，避免误伤真实部署配置；只忽略其中的工具工作区目录。

### 2. 增强 Python 项目关键 evidence

把以下 Python 项目文件纳入 `KEY_FILE_NAMES`：

- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `Pipfile`
- `poetry.lock`

这些文件只作为 evidence，不改变当前 `primary_stack` 枚举；Python 多栈建模仍保留为后续切片。

### 3. 不改变 LLM-first 和 no fallback 边界

本轮不增加确定性 stack 判断，不把 Python 自动提升为 primary stack，也不在 LLM 失败时 fallback。确定性逻辑只负责 evidence hygiene：收集更可信的输入，避免工具工作区污染 LLM 和 CLI。

## 非目标

本轮不实现：

- 完整多栈 schema 或 primary stack 枚举扩展。
- skipped / sampled 文件信息中文化。
- 疑似密钥高风险突出展示。
- LLM-planned deep scan 架构重写。
- `deploy-package` 整目录忽略。

这些仍保留在 `guided-init-ai4se-real-repo-findings.md` 中继续拆分。

## 验收标准

- `collect_evidence()` 不再把 `.claude/worktrees/**`、`.opencode/**`、`deploy-package/.opencode/**` 文件纳入 `EvidenceBundle.files`。
- `collect_evidence()` 在仓库根目录包含 `pyproject.toml`、`requirements.txt`、根 `package.json` 时，将它们作为 `key_files` / `priority_files`。
- 当同一个仓库同时存在根 `package.json` 和工具工作区里的 `package.json` 时，`key_files` 只包含根项目 manifest，不包含工具工作区 manifest。
- 通过 unit test 固定 evidence hygiene 行为；不要求真实 DeepSeek acceptance 覆盖本轮小切片。

## Assumptions / Risks

- `.claude` 和 `.opencode` 是 AI Coding 工具工作区或缓存目录，忽略它们符合当前产品边界。
- 如果客户把真实业务源码放在这些目录下，本轮会忽略它们；这是可接受的取舍，因为这些目录本身语义是工具状态，而不是主项目源码。
- Python 项目文件进入 key evidence 后，当前 LLM 仍可能输出 `unknown` primary stack，因为 schema 暂未支持 python/flask canonical primary stack；这属于后续多栈建模切片。

## Self-Harness Gate

本轮改善 `init` 用户旅程中的“扫描理解可信度”：在展示技术栈和判断依据之前，先确保 evidence 输入不被工具工作区污染。后续优先继续消化同一 todo 中的 skipped 信息中文化、高风险突出和多栈表达。
