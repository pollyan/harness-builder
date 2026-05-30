# Scanner Skill 重构计划 v2：LLM 主导 + 脚本精确提取

> **For implementer:** Use TDD throughout. Write failing test first. Watch it fail. Then implement.
> **API:** DeepSeek V4 Flash（OpenAI 兼容格式，key 已存 .env）
> **Baseline:** 113 tests passing, 16 source files, 13 test files
> **Predecessor:** `docs/superpowers/plans/2026-05-25-scanner-refactor-plan.md`（v1，已废弃）

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

## Task 4：新建 evidence_extractor.py — 按需精确提取

**目标：** 接收 LLM 分析结果，用现有 detector 按需提取。不再盲跑全部 detector。

**Files:**
- Create: `harness_builder/scanner/detectors/evidence_extractor.py`
- Create: `tests/scanner/test_evidence_extractor.py`

**新增测试（5 个）：**

```python
# test_evidence_extractor.py

def test_extract_java_evidence():
    """LLM says Maven → extract pom.xml details."""
    repo = Path("tests/fixtures/minimal-java-maven")
    llm_analysis = {"stackAnalysis": {"primary": {"name": "Java / Maven"}}}
    result = extract_evidence(repo, llm_analysis)
    assert "java" in result
    assert result["java"]["detected"] is True

def test_extract_dotnet_evidence():
    repo = Path("tests/fixtures/minimal-dotnet")
    llm_analysis = {"stackAnalysis": {"primary": {"name": ".NET"}}}
    result = extract_evidence(repo, llm_analysis)
    assert "dotnet" in result

def test_extract_mixed_stacks():
    repo = Path("tests/fixtures/minimal-java-maven")
    llm_analysis = {"stackAnalysis": {"primary": {"name": "Java"}, "secondary": [{"name": "Vue.js"}]}}
    result = extract_evidence(repo, llm_analysis)
    assert result["java"]["detected"] is True
    assert result["node"]["detected"] is True

def test_extract_unknown_stack():
    repo = Path("tests/fixtures/unknown-stack")
    llm_analysis = {"stackAnalysis": {"primary": {"name": "Custom Stack"}}}
    result = extract_evidence(repo, llm_analysis)
    assert "genericFallback" in result

def test_extract_always_includes_filesystem():
    repo = Path("tests/fixtures/minimal-java-maven")
    llm_analysis = {"stackAnalysis": {"primary": {"name": "Java"}}}
    result = extract_evidence(repo, llm_analysis)
    assert "filesystem" in result
    assert "ci" in result
    assert "codeStructure" in result
```

**实现要点：**
- `_stack_mentions(analysis, keywords)` — 检查 LLM 结论是否提到某技术栈
- `extract_evidence(repo_root, llm_analysis)` — 按 LLM 结论选择性运行 detector
  - 提到 Java/Maven/Spring → 运行 `detect_java_maven`
  - 提到 Node/npm/Vue/React → 运行 `detect_node_frontend`
  - 提到 .NET → 运行 `detect_dotnet`
  - 始终运行：`scan_filesystem`、`detect_ci_docker`、`detect_shallow_code_structure`
  - 始终运行 `detect_generic_fallback`（兜底）

**验证：** ~144 PASS

---

## Task 5：重构 core.py — 五阶段流水线

**目标：** 把 `scan_repository()` 重构为：文件树收集 → LLM 两轮扫描 → 精确提取 → 事实校验 → 合并输出。

**Files:**
- Modify: `harness_builder/scanner/core.py`
- Modify: `tests/scanner/test_core.py`

**新增测试（5 个）：**

```python
def test_scan_no_llm_has_file_tree_and_analysis():
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=None)
    assert "fileTree" in result.inventory
    assert "analysis" in result.inventory
    assert result.inventory["analysis"]["enabled"] is False

def test_scan_with_mock_llm():
    round1 = json.dumps({"stackAnalysis": {"primary": {"name": "Java", "confidence": "high", "evidence": []}, "secondary": []}, "moduleAnalysis": [], "commandCandidates": [{"category": "build", "command": "mvn package", "confidence": "high", "evidence": []}], "architecturePattern": None, "anomalies": [], "calibrationPoints": []})
    round2 = json.dumps({"stackAnalysis": {"primary": {"name": "Java / Spring Boot", "confidence": "high", "evidence": ["pom.xml"]}, "secondary": []}, "moduleAnalysis": [{"module": "app", "guessedRole": "App", "confidence": "medium", "evidence": []}], "commandCandidates": [{"category": "build", "command": "mvn clean package", "confidence": "high", "evidence": []}], "architecturePattern": None, "anomalies": [], "calibrationPoints": []})
    caller = MagicMock(side_effect=[round1, round2])
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=caller)
    assert result.inventory["analysis"]["enabled"] is True
    assert "evidence" in result.inventory

def test_scan_evidence_matches_llm_stack():
    """LLM says Java → evidence should contain java detector results."""
    round1 = json.dumps({"stackAnalysis": {"primary": {"name": "Java"}, "secondary": []}, "moduleAnalysis": [], "commandCandidates": [], "architecturePattern": None, "anomalies": [], "calibrationPoints": []})
    round2 = round1
    caller = MagicMock(side_effect=[round1, round2])
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=caller)
    assert "java" in result.inventory["evidence"]
    assert result.inventory["evidence"]["java"]["detected"] is True

def test_scan_commands_come_from_analysis():
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=None)
    assert "build" in result.commands["commands"]

def test_scan_includes_validation_points():
    """Should include validation results where LLM and script disagree."""
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=None)
    assert "validation" in result.inventory
```

**实现要点：**
- 删除 `_build_command_catalog()` 和 `_command()`
- 删除对 `llm_hints` 的 import
- `scan_repository(repo_root, out_dir, llm_caller=None)` 五阶段：
  1. `collect_file_tree(repo_root)` → fileTree
  2. `scan_with_llm(fileTree, llm_caller)` → analysis
  3. `extract_evidence(repo_root, analysis)` → evidence
  4. `_validate(analysis, evidence)` → validation（LLM 说有 vs 脚本确认）
  5. 合并为 inventory + commands
- `_validate(analysis, evidence)` — 校验 LLM 结论：
  - LLM 说 Maven → evidence.java.detected == True？
  - LLM 说有 N 个模块 → 实际顶层目录数匹配？
  - 不匹配的标记为 `validationPoints`
- `_commands_from_analysis(analysis, repo_name)` — 转换为 command-catalog 格式

**回归处理：**
- 现有 test_core.py 中检查 `stackExtensions`、`llmHints` 的测试需要适配新字段名
- test_command_catalog.py、test_dotnet_command_catalog.py 需要确认命令结构兼容

**验证：** 全量通过

---

## Task 6：重构 cli.py + 删除旧文件

**Files:**
- Modify: `harness_builder/scanner/cli.py`
- Modify: `tests/scanner/test_cli.py`
- Delete: `harness_builder/scanner/detectors/llm_hints.py`
- Delete: `tests/scanner/test_llm_hints.py`

**CLI 变更：**
- `--no-llm` 离线模式（纯规则推断）
- 默认调用 DeepSeek
- 加载 `.env` 文件（用 `python-dotenv` 或手动 `os.environ`）

**新增测试（2 个）：**
```python
def test_cli_no_llm_flag(tmp_path):
    repo = Path("tests/fixtures/minimal-java-maven").resolve()
    out = tmp_path / ".harness"
    result = subprocess.run([sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(repo), "--out", str(out), "--no-llm"], text=True, capture_output=True)
    assert result.returncode == 0
    inv = json.loads((out / "project-inventory.json").read_text())
    assert inv["analysis"]["enabled"] is False

def test_cli_help_shows_no_llm():
    result = subprocess.run([sys.executable, "-m", "harness_builder.scanner.cli", "--help"], text=True, capture_output=True)
    assert "--no-llm" in result.stdout
```

**验证：** 全量通过

---

## Task 7：增强 report.py + 真实冒烟

**Files:**
- Modify: `harness_builder/scanner/report.py`
- Modify: `tests/scanner/test_report.py`

**报告增强：**
- 展示 LLM 分析结果（技术栈、模块职责、架构模式、异常）
- 区分"确定性事实"和"LLM 推断"
- 展示校验结果（LLM vs 脚本）

**真实冒烟：**
- 用 DeepSeek API 扫描 RuoYi-Vue（`python3 -m harness_builder.scanner.cli --repo /tmp/openclaw/harness-poc-targets/RuoYi-Vue`）
- 用 DeepSeek API 扫描 eShopOnWeb
- 验证输出包含 analysis + evidence + validation
- 记录结果到 `docs/research/scanner-v2-smoke-test.md`

---

## Task 8：最终验证 + 清理

- 全量测试通过（目标 ~140+）
- Git clean
- 更新 README.md
- 删除不再需要的旧测试文件（test_llm_hints.py 已在 Task 6 删除）
- 保留 v1 和 v2 计划文档作为版本历史

---

## 完成标准

1. ~140+ tests PASS
2. `--no-llm` 模式输出与重构前功能等价
3. 默认模式用 DeepSeek 做两轮 LLM 扫描
4. 真实仓库（RuoYi-Vue + eShopOnWeb）冒烟通过
5. 输出包含 fileTree + analysis + evidence + validation
6. API key 不提交代码库
