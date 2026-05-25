# Scanner Skill 重构计划 v2：LLM 主导 + 脚本精确提取

> **For implementer:** Use TDD throughout. Write failing test first. Watch it fail. Then implement.
> **API:** DeepSeek V4 Flash（OpenAI 兼容格式，key 已存 .env）
> **Baseline:** 113 tests passing, 16 source files, 13 test files
> **Predecessor:** `docs/plans/2026-05-25-scanner-refactor-plan.md`（v1，已废弃）

---

## 0. 设计决策（v2 核心修订）

### 0.1 扫描顺序反转

| 步骤 | v1（已废弃） | v2（本计划） |
|------|-------------|-------------|
| 第一步 | 确定性脚本穷举扫描 | **确定性脚本收集文件树**（最小工作，不做判断） |
| 第二步 | LLM 补充分析 | **LLM 两轮扫描建立框架**（技术栈、架构、模块、命令） |
| 第三步 | 合并输出 | **确定性脚本精确提取**（按 LLM 结论读具体文件） |
| 第四步 | — | **确定性脚本校验 LLM**（事实 vs 推断矛盾标记为校准点） |
| 第五步 | — | **合并输出** |

### 0.2 防止 LLM 浅尝辄止

1. **Prompt 结构化约束**：明确要求分析每个顶层模块、覆盖 build/test 命令
2. **二次自检**：第一轮分析后让 LLM 自查"漏了什么"
3. **确定性脚本校验**：LLM 说有 Maven → 脚本确认 pom.xml 存在

### 0.3 API 配置

- Base URL: `https://api.deepseek.com`（OpenAI 兼容格式）
- Model: `deepseek-v4-flash`
- API Key: 环境变量 `DEEPSEEK_API_KEY`（`.env` 文件已配，`.gitignore` 已排除）

### 0.4 不动的文件

7 个 detector + models.py 不动。68 个 detector/model 测试不动。4 个现有集成测试不动。

---

## Task 1：新建 file_tree_collector.py — 最小文件树收集

**目标：** 递归遍历文件树，输出结构化清单。纯收集，零判断。LLM 的唯一输入。

**Files:**
- Create: `harness_builder/scanner/detectors/file_tree_collector.py`
- Create: `tests/scanner/test_file_tree_collector.py`

**新增测试（8 个）：** basic / key_files / file_metadata / excludes_ignored / empty_repo / directory_child_count / posix_paths / max_depth

**实现要点：**
- 遍历所有文件和目录，忽略 `.git/node_modules/target` 等
- 每个文件记录：path, name, extension, sizeBytes
- 每个目录记录：path, name, fileCount, subdirectoryCount
- 支持 max_depth 参数（默认 6 层）
- 所有路径用 POSIX 格式

**验证：** 121 PASS (113 + 8)

---

## Task 2：新建 deepseek_client.py — LLM 调用封装

**目标：** 封装 DeepSeek API，独立可测试。

**Files:**
- Create: `harness_builder/scanner/deepseek_client.py`
- Create: `tests/scanner/test_deepseek_client.py`

**新增测试（5 个）：** config_defaults / config_from_env / builds_correct_request / with_system_prompt / timeout_returns_none / no_api_key_returns_none

**实现要点：**
- `DeepSeekConfig` dataclass：api_key, base_url, model, max_tokens, temperature, timeout
- 环境变量 fallback：`DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`
- `call_deepseek(user_message, system_prompt, config)` → response string or None
- 用 `urllib.request` 调用 OpenAI 兼容的 `/chat/completions` 端点
- 异常时返回 None（不抛出）

**验证：** 126 PASS

---

## Task 3：新建 llm_scanner.py — LLM 扫描引擎（含自检）

**目标：** LLM 基于文件树做两轮扫描：第一轮分析，第二轮自检。

**Files:**
- Create: `harness_builder/scanner/detectors/llm_scanner.py`
- Create: `tests/scanner/test_llm_scanner.py`

**新增测试（13 个）：**

| 函数 | 测试 | 验证内容 |
|------|------|---------|
| `build_scan_prompt` | 2 | 包含文件树信息、要求最低覆盖 |
| `build_self_check_prompt` | 1 | 引用第一轮结论、列出未分析目录 |
| `parse_scan_response` | 3 | 有效JSON、code block、无效降级 |
| `merge_rounds` | 2 | 第二轮优先、第二轮失败回退第一轮 |
| `scan_with_llm` | 4 | 两轮调用、第二轮失败降级、无caller降级、首轮失败 |

**实现要点：**
- `build_scan_prompt(file_tree)`：从文件树构建详细 prompt，明确要求分析每个顶层模块和覆盖 build/test 命令
- `build_self_check_prompt(round1_json, file_tree)`：自检 prompt，列出所有顶层目录让 LLM 检查是否有遗漏
- `parse_scan_response(raw)`：JSON 解析 + code block 提取 + 降级
- `merge_rounds(round1, round2)`：第二轮优先，但保留第一轮独有的模块分析
- `scan_with_llm(file_tree, caller)`：两轮调用入口。caller 签名为 `(user_message, system_prompt) -> str|None`
- LLM 输出结构：`{stackAnalysis, moduleAnalysis, commandCandidates, architecturePattern, anomalies, calibrationPoints}`

**验证：** ~139 PASS

---

后续 Task 4-8 见 `docs/plans/2026-05-25-scanner-refactor-v2-part2.md`
