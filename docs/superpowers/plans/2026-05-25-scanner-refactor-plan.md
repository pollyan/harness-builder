# Scanner 重构实施计划：脚本收集 + LLM 理解流水线

> **For implementer:** Use TDD throughout. Write failing test first. Watch it fail. Then implement.

**Goal:** 重构 Scanner 架构，把"确定性脚本为主、LLM 兜底"改为"确定性脚本收集证据、LLM 理解证据、规则做快速推断"的三阶段流水线。

**Architecture:** 七个 detector 不动（它们已经是优秀的证据收集器）。新增 evidence_builder 把收集结果标准化；新增 llm_analyzer 基于 evidence 做深度分析；重构 core.py 为三阶段流水线（收集 → 分析 → 合并）。命令候选由规则（高置信度快速通道）和 LLM（全面补充）共同生成，标注来源。

**Tech Stack:** Python 3.9+、pytest、PyYAML、标准库 urllib（LLM 调用）、unittest.mock（LLM 测试）

**Baseline:** 113 tests passing, 16 source files, 13 test files

---

## 0. 上下文与硬边界

### 0.1 设计决策（已确认）

1. **确定性脚本 = 证据收集器**。回答"有没有""是什么""有多少"。
2. **LLM = 理解引擎**。基于证据回答"意味着什么""应该怎样""有什么异常"。
3. **规则快速推断保留**。有 pom.xml → Maven 构建文件存在。确定性 99.9%，不值得调 LLM。
4. **不是兜底关系，是流水线关系**。脚本产出是 LLM 的输入，LLM 产出是最终输出的一部分。
5. **向后兼容**。`--no-llm` 模式下行为与重构前一致。project-inventory.json 只新增不删除。

### 0.2 不动的文件

以下文件和测试完全不动（证据收集层 + 纯数据结构）：

| 源文件 | 测试文件 | 测试数 |
|--------|---------|--------|
| `detectors/filesystem.py` | `test_filesystem.py` | 7 |
| `detectors/java_maven.py` | `test_java_maven.py` | 13 |
| `detectors/node_frontend.py` | `test_node_frontend.py` | 9 |
| `detectors/dotnet.py` | `test_dotnet.py` | 9 |
| `detectors/ci_docker.py` | `test_ci_docker.py` | 6 |
| `detectors/shallow_code.py` | `test_shallow_code.py` | 10 |
| `detectors/generic_fallback.py` | `test_generic_fallback.py` | 8 |
| `models.py` | `test_models.py` | 3 |
| `report.py` | `test_report.py` | 3 |

共 68 个测试不动。

### 0.3 不动的测试文件（保留，不修改）

以下测试文件验证的是重构后仍需保持的行为，保留不动：

| 测试文件 | 测试数 | 验证内容 |
|---------|--------|---------|
| `test_command_catalog.py` | 1 | Maven + frontend 命令候选（`--no-llm` 模式仍需通过） |
| `test_dotnet_command_catalog.py` | 1 | dotnet 命令候选 |
| `test_end_to_end.py` | 1 | CLI 生成三个文件 |
| `test_unknown_stack_end_to_end.py` | 1 | 未知技术栈仍能生成输出 |

共 4 个测试不动。

### 0.4 将被替换/删除的文件

| 文件 | 处理 |
|------|------|
| `detectors/llm_hints.py` | 被 `detectors/llm_analyzer.py` 替代，重构完成后删除 |
| `tests/scanner/test_llm_hints.py` | 被 `tests/scanner/test_llm_analyzer.py` 替代，重构完成后删除 |
| `tests/scanner/test_core.py` | 重构后适配新接口（28 → ~35 tests） |
| `tests/scanner/test_cli.py` | 重构后适配新接口（4 → ~6 tests） |

---

## Task 1：新建 evidence_builder.py — 证据汇总模块

**目标：** 把 core.py 里调用各 detector 的逻辑抽成独立模块，输出标准化的 evidence dict。

**Files:**
- Create: `harness_builder/scanner/detectors/evidence_builder.py`
- Create: `tests/scanner/test_evidence_builder.py`

**Step 1: Write the failing test**

`tests/scanner/test_evidence_builder.py`:

```python
from pathlib import Path

from harness_builder.scanner.detectors.evidence_builder import collect_evidence


def test_collect_evidence_returns_all_detector_keys():
    repo = Path("tests/fixtures/minimal-java-maven")

    evidence = collect_evidence(repo)

    assert "repo" in evidence
    assert "filesystem" in evidence
    assert "java" in evidence
    assert "node" in evidence
    assert "dotnet" in evidence
    assert "ci" in evidence
    assert "codeStructure" in evidence
    assert "genericFallback" in evidence


def test_collect_evidence_repo_metadata():
    repo = Path("tests/fixtures/minimal-java-maven")

    evidence = collect_evidence(repo)

    assert evidence["repo"]["name"] == "minimal-java-maven"
    assert isinstance(evidence["repo"]["path"], str)


def test_collect_evidence_java_detected():
    repo = Path("tests/fixtures/minimal-java-maven")

    evidence = collect_evidence(repo)

    assert evidence["java"]["detected"] is True
    assert len(evidence["java"]["buildFiles"]) > 0


def test_collect_evidence_dotnet_not_detected():
    repo = Path("tests/fixtures/minimal-java-maven")

    evidence = collect_evidence(repo)

    assert evidence["dotnet"]["detected"] is False


def test_collect_evidence_node_detected():
    repo = Path("tests/fixtures/minimal-java-maven")

    evidence = collect_evidence(repo)

    assert evidence["node"]["detected"] is True


def test_collect_evidence_empty_repo(tmp_path):
    evidence = collect_evidence(tmp_path)

    assert evidence["repo"]["name"] == tmp_path.name
    assert evidence["filesystem"]["topLevelDirectories"] == []
    assert evidence["java"]["detected"] is False
    assert evidence["node"]["detected"] is False
    assert evidence["dotnet"]["detected"] is False


def test_collect_evidence_dotnet_repo():
    repo = Path("tests/fixtures/minimal-dotnet")

    evidence = collect_evidence(repo)

    assert evidence["dotnet"]["detected"] is True
    assert evidence["java"]["detected"] is False
    assert len(evidence["ci"]["githubActions"]) > 0
```

**Step 2: Run test — confirm it fails**

Command: `python3 -m pytest tests/scanner/test_evidence_builder.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness_builder.scanner.detectors.evidence_builder'`

**Step 3: Write minimal implementation**

`harness_builder/scanner/detectors/evidence_builder.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder.scanner.detectors.ci_docker import detect_ci_docker
from harness_builder.scanner.detectors.dotnet import detect_dotnet
from harness_builder.scanner.detectors.filesystem import scan_filesystem
from harness_builder.scanner.detectors.generic_fallback import detect_generic_fallback
from harness_builder.scanner.detectors.java_maven import detect_java_maven
from harness_builder.scanner.detectors.node_frontend import detect_node_frontend
from harness_builder.scanner.detectors.shallow_code import detect_shallow_code_structure


def collect_evidence(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    return {
        "repo": {"name": repo_root.name, "path": str(repo_root)},
        "filesystem": scan_filesystem(repo_root),
        "java": detect_java_maven(repo_root),
        "node": detect_node_frontend(repo_root),
        "dotnet": detect_dotnet(repo_root),
        "ci": detect_ci_docker(repo_root),
        "codeStructure": detect_shallow_code_structure(repo_root),
        "genericFallback": detect_generic_fallback(repo_root),
    }
```

**Step 4: Run test — confirm it passes**

Command: `python3 -m pytest tests/scanner/test_evidence_builder.py -v`
Expected: 7 PASS

**Step 5: Run all tests — confirm no regression**

Command: `python3 -m pytest -v`
Expected: 120 PASS (113 existing + 7 new)

**Step 6: Commit**

`git add harness_builder/scanner/detectors/evidence_builder.py tests/scanner/test_evidence_builder.py && git commit -m "feat: 新增证据汇总模块 evidence_builder"`

---

## Task 2：新建 llm_analyzer.py — LLM 分析引擎

**目标：** 从 llm_hints.py 演化，职责从"生成 hints"扩展为"完整分析"。接收 evidence dict，输出结构化分析结果（技术栈、模块职责、命令候选、架构模式、异常、校准点）。

**Files:**
- Create: `harness_builder/scanner/detectors/llm_analyzer.py`
- Create: `tests/scanner/test_llm_analyzer.py`

**Step 1: Write the failing test**

`tests/scanner/test_llm_analyzer.py`:

```python
import json
from unittest.mock import MagicMock

from harness_builder.scanner.detectors.llm_analyzer import (
    build_analysis_prompt,
    parse_llm_response,
    format_analysis,
    analyze_with_llm,
    generate_rule_based_analysis,
)


# ── build_analysis_prompt ──


def test_prompt_contains_evidence():
    evidence = {
        "repo": {"name": "test-project", "path": "/tmp/test"},
        "filesystem": {"topLevelDirectories": ["src"], "keyFiles": ["pom.xml"], "fileCounts": {"total": 10}},
        "java": {"detected": True, "buildFiles": ["pom.xml"]},
        "node": {"detected": False, "projects": []},
        "dotnet": {"detected": False, "solutions": [], "projects": []},
        "ci": {"githubActions": [], "dockerComposeFiles": [], "dockerfiles": []},
        "codeStructure": {"controllers": [], "services": [], "entitiesOrModels": [], "tests": [], "frontendComponents": []},
        "genericFallback": {"stackClassification": "unknown", "documentation": [], "scriptCandidates": [], "configCandidates": []},
    }
    prompt = build_analysis_prompt(evidence)

    assert "test-project" in prompt
    assert "pom.xml" in prompt
    assert "JSON" in prompt or "json" in prompt


def test_prompt_requests_structured_output():
    evidence = {"repo": {"name": "x"}, "filesystem": {}, "java": {}, "node": {}, "dotnet": {}, "ci": {}, "codeStructure": {}, "genericFallback": {}}
    prompt = build_analysis_prompt(evidence)

    assert "stackAnalysis" in prompt
    assert "moduleAnalysis" in prompt
    assert "commandCandidates" in prompt
    assert "anomalies" in prompt


# ── parse_llm_response ──


def test_parse_valid_json():
    raw = json.dumps({
        "stackAnalysis": {"primary": {"name": "Java", "confidence": "high", "evidence": ["pom.xml"]}, "secondary": []},
        "moduleAnalysis": [],
        "commandCandidates": [],
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    })
    parsed = parse_llm_response(raw)

    assert parsed["stackAnalysis"]["primary"]["name"] == "Java"


def test_parse_json_in_code_block():
    raw = '```json\n{"stackAnalysis": null, "moduleAnalysis": [], "commandCandidates": [], "architecturePattern": null, "anomalies": [], "calibrationPoints": []}\n```'
    parsed = parse_llm_response(raw)

    assert isinstance(parsed, dict)


def test_parse_invalid_json_returns_error_structure():
    parsed = parse_llm_response("not json at all")

    assert parsed.get("_parseError") is True
    assert "stackAnalysis" in parsed  # Still has expected keys for graceful degradation


# ── format_analysis ──


def test_format_stack_analysis():
    parsed = {
        "stackAnalysis": {"primary": {"name": "Java / Spring Boot", "confidence": "high", "evidence": ["pom.xml found"]}, "secondary": [{"name": "Vue.js", "confidence": "high", "evidence": [".vue files"]}]},
        "moduleAnalysis": [], "commandCandidates": [], "architecturePattern": None, "anomalies": [], "calibrationPoints": [],
    }
    result = format_analysis(parsed)

    assert result["stackAnalysis"]["primary"]["name"] == "Java / Spring Boot"
    assert len(result["stackAnalysis"]["secondary"]) == 1


def test_format_command_candidates():
    parsed = {
        "stackAnalysis": None, "moduleAnalysis": [],
        "commandCandidates": [
            {"category": "build", "command": "mvn clean package", "workingDirectory": ".", "confidence": "high", "evidence": ["pom.xml"]},
        ],
        "architecturePattern": None, "anomalies": [], "calibrationPoints": [],
    }
    result = format_analysis(parsed)

    assert len(result["commandCandidates"]) == 1
    assert result["commandCandidates"][0]["source"] == "llm"


def test_format_anomalies():
    parsed = {
        "stackAnalysis": None, "moduleAnalysis": [], "commandCandidates": [],
        "architecturePattern": None,
        "anomalies": [{"message": "No CI found", "confidence": "medium", "evidence": ["no .github/workflows"]}],
        "calibrationPoints": [],
    }
    result = format_analysis(parsed)

    assert len(result["anomalies"]) == 1


# ── analyze_with_llm (with mock caller) ──


def test_analyze_with_mock_llm():
    mock_response = json.dumps({
        "stackAnalysis": {"primary": {"name": "Java", "confidence": "high", "evidence": ["pom.xml"]}, "secondary": []},
        "moduleAnalysis": [{"module": "app", "guessedRole": "Application module", "confidence": "medium", "evidence": ["has pom.xml"]}],
        "commandCandidates": [{"category": "build", "command": "mvn clean package", "workingDirectory": ".", "confidence": "high", "evidence": ["pom.xml"]}],
        "architecturePattern": {"pattern": "Multi-module Maven", "confidence": "medium", "evidence": ["multiple pom.xml"]},
        "anomalies": [],
        "calibrationPoints": [{"message": "Verify Spring profiles", "confidence": "low", "evidence": []}],
    })
    caller = MagicMock(return_value=mock_response)

    evidence = {"repo": {"name": "test"}, "filesystem": {}, "java": {"detected": True}, "node": {}, "dotnet": {}, "ci": {}, "codeStructure": {}, "genericFallback": {}}
    result = analyze_with_llm(evidence, caller)

    assert result["enabled"] is True
    assert result["stackAnalysis"]["primary"]["name"] == "Java"
    assert len(result["commandCandidates"]) == 1
    assert result["commandCandidates"][0]["source"] == "llm"
    assert caller.called


def test_analyze_with_llm_exception():
    caller = MagicMock(side_effect=RuntimeError("API error"))

    evidence = {"repo": {"name": "test"}, "filesystem": {}, "java": {}, "node": {}, "dotnet": {}, "ci": {}, "codeStructure": {}, "genericFallback": {}}
    result = analyze_with_llm(evidence, caller)

    assert result["enabled"] is False
    assert result.get("_llmError") is True


def test_analyze_without_caller():
    evidence = {"repo": {"name": "test"}, "filesystem": {}, "java": {}, "node": {}, "dotnet": {}, "ci": {}, "codeStructure": {}, "genericFallback": {}}
    result = analyze_with_llm(evidence, None)

    assert result["enabled"] is False


# ── generate_rule_based_analysis ──


def test_rule_based_java():
    evidence = {
        "repo": {"name": "test"},
        "java": {"detected": True, "buildFiles": ["pom.xml"]},
        "node": {"detected": False, "projects": []},
        "dotnet": {"detected": False, "solutions": [], "projects": []},
    }
    result = generate_rule_based_analysis(evidence)

    assert result["stackAnalysis"]["primary"]["name"] == "Maven / Java"
    build_cmds = [c for c in result["commandCandidates"] if c["category"] == "build"]
    assert len(build_cmds) >= 1
    assert build_cmds[0]["source"] == "rule"


def test_rule_based_dotnet():
    evidence = {
        "repo": {"name": "test"},
        "java": {"detected": False},
        "node": {"detected": False, "projects": []},
        "dotnet": {"detected": True, "solutions": ["App.sln"], "projects": []},
    }
    result = generate_rule_based_analysis(evidence)

    assert result["stackAnalysis"]["primary"]["name"] == ".NET"
    build_cmds = [c for c in result["commandCandidates"] if c["category"] == "build"]
    assert any("dotnet build" in c["command"] for c in build_cmds)


def test_rule_based_node():
    evidence = {
        "repo": {"name": "test"},
        "java": {"detected": False},
        "node": {"detected": True, "projects": [{"path": "ui", "packageFile": "ui/package.json", "scripts": {"build": "vite build", "dev": "vite"}, "vueFileCount": 5}]},
        "dotnet": {"detected": False, "solutions": [], "projects": []},
    }
    result = generate_rule_based_analysis(evidence)

    assert "Vue.js" in result["stackAnalysis"]["primary"]["name"]
    frontend_cmds = [c for c in result["commandCandidates"] if c["category"] == "frontend"]
    assert len(frontend_cmds) >= 1


def test_rule_based_no_stack():
    evidence = {
        "repo": {"name": "test"},
        "java": {"detected": False},
        "node": {"detected": False, "projects": []},
        "dotnet": {"detected": False, "solutions": [], "projects": []},
    }
    result = generate_rule_based_analysis(evidence)

    assert result["stackAnalysis"]["primary"] is None
    assert result["commandCandidates"] == []


def test_rule_based_mixed_stack():
    evidence = {
        "repo": {"name": "test"},
        "java": {"detected": True, "buildFiles": ["pom.xml"]},
        "node": {"detected": True, "projects": [{"path": "ui", "packageFile": "ui/package.json", "scripts": {"build": "vite build"}, "vueFileCount": 10}]},
        "dotnet": {"detected": False, "solutions": [], "projects": []},
    }
    result = generate_rule_based_analysis(evidence)

    assert result["stackAnalysis"]["primary"]["name"] == "Maven / Java"
    assert len(result["stackAnalysis"]["secondary"]) >= 1
    # Should have both maven and node commands
    categories = set(c["category"] for c in result["commandCandidates"])
    assert "build" in categories
    assert "frontend" in categories
```

**Step 2: Run test — confirm it fails**

Command: `python3 -m pytest tests/scanner/test_llm_analyzer.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

`harness_builder/scanner/detectors/llm_analyzer.py`:

```python
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def build_analysis_prompt(evidence: dict[str, Any]) -> str:
    """Build a structured prompt from the collected evidence for LLM analysis."""
    repo_name = evidence.get("repo", {}).get("name", "unknown")
    fs = evidence.get("filesystem", {})
    java = evidence.get("java", {})
    node = evidence.get("node", {})
    dotnet = evidence.get("dotnet", {})
    ci = evidence.get("ci", {})
    code = evidence.get("codeStructure", {})
    generic = evidence.get("genericFallback", {})

    # Build a concise evidence summary
    detected = []
    if java.get("detected"):
        detected.append("Java/Maven")
    if node.get("detected"):
        detected.append("Node.js/Vue")
    if dotnet.get("detected"):
        detected.append(".NET")

    return f"""You are a project structure analyst. Analyze the following scan evidence and provide structured insights.

Rules:
- Every insight must include confidence (high/medium/low) and evidence (list of supporting facts).
- Do NOT invent facts not supported by the evidence.
- Do NOT override the deterministic scan results.

Repository: {repo_name}
Detected tech stacks: {json.dumps(detected) if detected else 'None detected by deterministic scanners'}

Filesystem:
- Top directories: {json.dumps(fs.get('topLevelDirectories', [])[:15])}
- Key files: {json.dumps(fs.get('keyFiles', [])[:20])}
- File counts by extension: {json.dumps(dict(list(fs.get('fileCounts', {}).get('byExtension', {}).items())[:10]))}
- Total files: {fs.get('fileCounts', {}).get('total', 0)}

Java/Maven: {json.dumps(java, ensure_ascii=False)}
Node/Frontend: {json.dumps(node, ensure_ascii=False)}
.NET: {json.dumps(dotnet, ensure_ascii=False)}
CI/Docker: {json.dumps(ci, ensure_ascii=False)}
Code structure: controllers={len(code.get('controllers', []))}, services={len(code.get('services', []))}, entities={len(code.get('entitiesOrModels', []))}, tests={len(code.get('tests', []))}, frontend={len(code.get('frontendComponents', []))}
Generic fallback: {json.dumps(generic, ensure_ascii=False)}

Respond in this exact JSON format:
{{
  "stackAnalysis": {{
    "primary": {{"name": "<primary stack or null>", "confidence": "<high|medium|low>", "evidence": ["<why>"]}},
    "secondary": [{{"name": "<secondary stack>", "confidence": "<high|medium|low>", "evidence": ["<why>"]}}]
  }},
  "moduleAnalysis": [
    {{"module": "<directory/module name>", "guessedRole": "<what it likely does>", "confidence": "<high|medium|low>", "evidence": ["<why>"]}}
  ],
  "commandCandidates": [
    {{"category": "<build|test|run|frontend|docker>", "command": "<actual command>", "workingDirectory": "<. or path>", "confidence": "<high|medium|low>", "evidence": ["<why>"]}}
  ],
  "architecturePattern": {{"pattern": "<pattern name or null>", "confidence": "<high|medium|low>", "evidence": ["<why>"]}} | null,
  "anomalies": [
    {{"message": "<unusual pattern>", "confidence": "<high|medium|low>", "evidence": ["<why>"]}}
  ],
  "calibrationPoints": [
    {{"message": "<what human should verify>", "confidence": "<high|medium|low>", "evidence": ["<why>"]}}
  ]
}}"""


def parse_llm_response(raw: str) -> dict[str, Any]:
    """Parse LLM response, extracting JSON from markdown code blocks if needed."""
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON")
        return {
            "stackAnalysis": None, "moduleAnalysis": [], "commandCandidates": [],
            "architecturePattern": None, "anomalies": [], "calibrationPoints": [],
            "_parseError": True, "_rawPreview": text[:500],
        }


def format_analysis(parsed: dict[str, Any]) -> dict[str, Any]:
    """Format parsed LLM response into the standard analysis structure."""
    # Add source="llm" to all command candidates
    commands = []
    for cmd in parsed.get("commandCandidates", []):
        cmd_copy = dict(cmd)
        cmd_copy["source"] = "llm"
        commands.append(cmd_copy)

    return {
        "stackAnalysis": parsed.get("stackAnalysis"),
        "moduleAnalysis": parsed.get("moduleAnalysis", []),
        "commandCandidates": commands,
        "architecturePattern": parsed.get("architecturePattern"),
        "anomalies": parsed.get("anomalies", []),
        "calibrationPoints": parsed.get("calibrationPoints", []),
    }


def analyze_with_llm(evidence: dict[str, Any], llm_caller: Optional[Callable[[str], str]]) -> dict[str, Any]:
    """Run LLM analysis on collected evidence. Returns analysis dict or graceful degradation."""
    if llm_caller is None:
        return {"enabled": False, **generate_rule_based_analysis(evidence)}

    prompt = build_analysis_prompt(evidence)
    try:
        raw = llm_caller(prompt)
        parsed = parse_llm_response(raw)
        formatted = format_analysis(parsed)
        return {"enabled": True, **formatted}
    except Exception:
        logger.exception("LLM analysis failed")
        return {"enabled": False, "_llmError": True, **generate_rule_based_analysis(evidence)}


def generate_rule_based_analysis(evidence: dict[str, Any]) -> dict[str, Any]:
    """Generate analysis using deterministic rules only (fallback or --no-llm mode)."""
    java = evidence.get("java", {})
    node = evidence.get("node", {})
    dotnet = evidence.get("dotnet", {})

    # Stack analysis
    primary = None
    secondary = []
    commands = []

    if java.get("detected"):
        primary = {"name": "Maven / Java", "confidence": "high", "evidence": [f"{len(java.get('buildFiles', []))} pom.xml files found"]}
        commands.append({"category": "build", "command": "mvn clean package -DskipTests", "workingDirectory": ".", "confidence": "high", "source": "rule", "evidence": ["pom.xml detected"]})
        commands.append({"category": "test", "command": "mvn test", "workingDirectory": ".", "confidence": "medium", "source": "rule", "evidence": ["Maven project"]})

    if dotnet.get("detected"):
        if primary is None:
            primary = {"name": ".NET", "confidence": "high", "evidence": [f"{len(dotnet.get('solutions', []))} solution files"]}
        else:
            secondary.append({"name": ".NET", "confidence": "high", "evidence": [f"{len(dotnet.get('solutions', []))} solution files"]})
        commands.append({"category": "build", "command": "dotnet build", "workingDirectory": ".", "confidence": "high", "source": "rule", "evidence": [".sln detected"]})
        commands.append({"category": "test", "command": "dotnet test", "workingDirectory": ".", "confidence": "high", "source": "rule", "evidence": [".sln detected"]})

    if node.get("detected"):
        for proj in node.get("projects", []):
            scripts = proj.get("scripts", {})
            proj_path = proj.get("path", ".")
            vue_count = proj.get("vueFileCount", 0)
            stack_name = "Vue.js" if vue_count > 0 else "Node.js"

            if primary is None:
                primary = {"name": stack_name, "confidence": "high", "evidence": [f"package.json at {proj_path}"]}
            else:
                secondary.append({"name": stack_name, "confidence": "high", "evidence": [f"package.json at {proj_path}"]})

            if "build" in scripts:
                commands.append({"category": "frontend", "command": "npm run build", "workingDirectory": proj_path, "confidence": "high", "source": "rule", "evidence": [f"package.json build script at {proj_path}"]})
            if "dev" in scripts:
                commands.append({"category": "run", "command": "npm run dev", "workingDirectory": proj_path, "confidence": "medium", "source": "rule", "evidence": [f"package.json dev script at {proj_path}"]})

    return {
        "stackAnalysis": {"primary": primary, "secondary": secondary},
        "moduleAnalysis": [],
        "commandCandidates": commands,
        "architecturePattern": None,
        "anomalies": [],
        "calibrationPoints": [],
    }
```

**Step 4: Run test — confirm it passes**

Command: `python3 -m pytest tests/scanner/test_llm_analyzer.py -v`
Expected: ~18 PASS

**Step 5: Run all tests — confirm no regression**

Command: `python3 -m pytest -v`
Expected: ~138 PASS (120 + 18 new)

**Step 6: Commit**

`git add harness_builder/scanner/detectors/llm_analyzer.py tests/scanner/test_llm_analyzer.py && git commit -m "feat: 新增 LLM 分析引擎 llm_analyzer"`

---

## Task 3：重构 core.py — 三阶段流水线

**目标：** 把 `scan_repository()` 从"收集 + 硬编码命令生成"改为"收集证据 → LLM/规则分析 → 合并输出"。`_build_command_catalog()` 删除，改用 `llm_analyzer`。

**Files:**
- Modify: `harness_builder/scanner/core.py`
- Modify: `tests/scanner/test_core.py`

**Step 1: Write the failing test**

在 `tests/scanner/test_core.py` **末尾**追加以下测试（保留所有现有测试）：

```python
from harness_builder.scanner.detectors.evidence_builder import collect_evidence
from harness_builder.scanner.detectors.llm_analyzer import generate_rule_based_analysis
from unittest.mock import MagicMock


def test_scan_repository_no_llm_has_evidence():
    """--no-llm mode: inventory should contain evidence field."""
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=None)

    assert "evidence" in result.inventory
    assert result.inventory["evidence"]["java"]["detected"] is True


def test_scan_repository_no_llm_has_analysis():
    """--no-llm mode: inventory should contain analysis with source='rule' commands."""
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=None)

    assert "analysis" in result.inventory
    assert result.inventory["analysis"]["enabled"] is False
    build_cmds = [c for c in result.inventory["analysis"]["commandCandidates"] if c["category"] == "build"]
    assert len(build_cmds) >= 1
    assert build_cmds[0]["source"] == "rule"


def test_scan_repository_with_mock_llm():
    """LLM mode: analysis should contain LLM-sourced commands."""
    mock_response = json.dumps({
        "stackAnalysis": {"primary": {"name": "Java", "confidence": "high", "evidence": ["pom.xml"]}, "secondary": []},
        "moduleAnalysis": [], "commandCandidates": [
            {"category": "build", "command": "mvn clean package", "workingDirectory": ".", "confidence": "high", "evidence": ["pom.xml"]}
        ],
        "architecturePattern": None, "anomalies": [], "calibrationPoints": [],
    })
    caller = MagicMock(return_value=mock_response)

    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=caller)

    assert result.inventory["analysis"]["enabled"] is True
    assert caller.called


def test_scan_repository_analysis_in_commands():
    """ScanResult.commands should be populated from analysis.commandCandidates."""
    repo = Path("tests/fixtures/minimal-java-maven")
    result = scan_repository(repo, Path("/tmp/unused"), llm_caller=None)

    # commands should come from analysis
    assert "commands" in result.commands
    assert "build" in result.commands["commands"]
```

**Step 2: Run test — confirm it fails**

Command: `python3 -m pytest tests/scanner/test_core.py::test_scan_repository_no_llm_has_evidence -v`
Expected: FAIL — `AssertionError: assert 'evidence' in result.inventory` (key not yet present)

**Step 3: Modify core.py**

Replace the entire `core.py` implementation with:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from harness_builder.scanner.detectors.evidence_builder import collect_evidence
from harness_builder.scanner.detectors.llm_analyzer import analyze_with_llm
from harness_builder.scanner.report import render_scanner_report


@dataclass
class ScanResult:
    inventory: dict[str, Any]
    commands: dict[str, Any]


def _commands_from_analysis(analysis: dict[str, Any], repo_name: str) -> dict[str, Any]:
    """Convert flat commandCandidates list into categorized command catalog."""
    categories = {"build": [], "test": [], "run": [], "frontend": [], "docker": []}
    for cmd in analysis.get("commandCandidates", []):
        cat = cmd.get("category", "build")
        if cat in categories:
            entry = {
                "name": cmd.get("command", "").split()[0] + "-" + cat,
                "command": cmd.get("command", ""),
                "workingDirectory": cmd.get("workingDirectory", "."),
                "source": cmd.get("source", "rule"),
                "confidence": cmd.get("confidence", "medium"),
                "evidence": cmd.get("evidence", []),
                "verified": False,
            }
            categories[cat].append(entry)
    return {"repo": repo_name, "commands": categories}


def scan_repository(repo_root: Path, out_dir: Path, llm_caller: Optional[Callable[[str], str]] = None) -> ScanResult:
    repo_root = repo_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: Collect evidence (deterministic)
    evidence = collect_evidence(repo_root)

    # Phase 2: Analyze evidence (LLM or rules)
    analysis = analyze_with_llm(evidence, llm_caller)

    # Phase 3: Merge into inventory
    inventory = {
        "repo": evidence["repo"],
        "structure": evidence["filesystem"],
        "stackExtensions": {
            "java": evidence["java"],
            "node": evidence["node"],
            "dotnet": evidence["dotnet"],
            "genericFallback": evidence["genericFallback"],
        },
        "ci": evidence["ci"],
        "codeStructure": evidence["codeStructure"],
        "evidence": evidence,
        "analysis": analysis,
    }
    commands = _commands_from_analysis(analysis, repo_root.name)
    return ScanResult(inventory=inventory, commands=commands)


def write_scan_outputs(result: ScanResult, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "project-inventory.json").write_text(json.dumps(result.inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "command-catalog.yaml").write_text(yaml.safe_dump(result.commands, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (out_dir / "scanner-report.md").write_text(render_scanner_report(result.inventory, result.commands), encoding="utf-8")
```

**Step 4: Run test — confirm new tests pass**

Command: `python3 -m pytest tests/scanner/test_core.py -v`
Expected: All existing + new tests PASS

**Step 5: Run all tests — check for regressions**

Command: `python3 -m pytest -v`

Expected: Some existing tests in `test_command_catalog.py` and `test_core.py` may fail due to interface changes. Fix any failures:

- `test_command_catalog.py`: This test calls `scan_repository()` and checks for commands. The new interface should produce the same commands via `_commands_from_analysis()`. If it fails, update assertions to match the new command structure (now includes `source` field).
- `test_core.py` existing tests that check for `stackExtensions`, `llmHints`, etc: Update to match new structure (`evidence` replaces direct detector results in `stackExtensions`, `analysis` replaces `llmHints`).

**Step 6: Fix failing tests, then commit**

`git add -A && git commit -m "feat: 重构 core.py 为三阶段流水线"`

---

## Task 4：重构 cli.py — 默认 LLM，`--no-llm` 离线

**目标：** CLI 默认尝试 LLM 调用，`--no-llm` 跳过。保持 `--llm` 作为显式启用标志。

**Files:**
- Modify: `harness_builder/scanner/cli.py`
- Modify: `tests/scanner/test_cli.py`

**Step 1: Write the failing test**

在 `tests/scanner/test_cli.py` **末尾**追加：

```python
def test_scanner_cli_no_llm_flag(tmp_path):
    """--no-llm should produce output without LLM."""
    repo = Path("tests/fixtures/minimal-java-maven").resolve()
    out = tmp_path / ".harness"

    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(repo), "--out", str(out), "--no-llm"],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert (out / "project-inventory.json").exists()
    import json
    inv = json.loads((out / "project-inventory.json").read_text())
    assert inv["analysis"]["enabled"] is False
```

**Step 2: Run test — confirm it fails**

Command: `python3 -m pytest tests/scanner/test_cli.py::test_scanner_cli_no_llm_flag -v`
Expected: FAIL — `error: unrecognized arguments: --no-llm`

**Step 3: Modify cli.py**

Update `build_parser()` to add `--no-llm`:

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness Builder Scanner")
    parser.add_argument("--repo", default=".", help="Repository root path. Defaults to current directory.")
    parser.add_argument("--out", default=None, help="Output directory. Defaults to <repo>/.harness.")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM analysis. Use deterministic rules only.")
    return parser
```

Update `main()` to pass `llm_caller=None` when `--no-llm`:

```python
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    out = Path(args.out).resolve() if args.out else repo / ".harness"
    if not repo.exists():
        parser.error(f"repo path does not exist: {repo}")

    llm_caller = None if args.no_llm else _make_llm_caller()
    result = scan_repository(repo, out, llm_caller=llm_caller)
    write_scan_outputs(result, out)
    print(f"Generated Harness scanner outputs at {out}")
    return 0
```

**Step 4: Run test — confirm it passes**

Command: `python3 -m pytest tests/scanner/test_cli.py -v`
Expected: All PASS

**Step 5: Run all tests**

Command: `python3 -m pytest -v`
Expected: All PASS

**Step 6: Commit**

`git add harness_builder/scanner/cli.py tests/scanner/test_cli.py && git commit -m "feat: CLI 支持 --no-llm 离线模式"`

---

## Task 5：增强 report.py — 区分事实和推断

**目标：** 报告展示 LLM 分析结果，明确标注"确定性事实"和"LLM 推断"。

**Files:**
- Modify: `harness_builder/scanner/report.py`
- Modify: `tests/scanner/test_report.py`

**Step 1: Write the failing test**

在 `tests/scanner/test_report.py` **末尾**追加：

```python
def test_render_report_with_analysis():
    inventory = {
        "repo": {"name": "test-project", "path": "/tmp/test"},
        "analysis": {
            "enabled": True,
            "stackAnalysis": {"primary": {"name": "Java", "confidence": "high", "evidence": ["pom.xml"]}, "secondary": []},
            "moduleAnalysis": [{"module": "app", "guessedRole": "Application", "confidence": "medium", "evidence": []}],
            "anomalies": [{"message": "No CI", "confidence": "medium", "evidence": []}],
            "calibrationPoints": [],
        },
    }
    commands = {"commands": {"build": [], "test": [], "run": [], "frontend": [], "docker": []}}
    report = render_scanner_report(inventory, commands)

    assert "Java" in report
    assert "LLM 分析" in report or "分析结果" in report
    assert "Application" in report
    assert "No CI" in report


def test_render_report_no_analysis():
    inventory = {
        "repo": {"name": "test", "path": "/tmp/test"},
        "analysis": {"enabled": False},
    }
    commands = {"commands": {}}
    report = render_scanner_report(inventory, commands)

    assert "# Scanner Report" in report
```

**Step 2: Run test — confirm it fails**

Command: `python3 -m pytest tests/scanner/test_report.py::test_render_report_with_analysis -v`
Expected: FAIL — `AssertionError: assert 'LLM 分析' in report`

**Step 3: Modify report.py**

Replace `render_scanner_report()` with:

```python
def render_scanner_report(inventory: dict[str, Any], commands: dict[str, Any]) -> str:
    repo_name = inventory["repo"]["name"]
    build_count = len(commands["commands"].get("build", []))
    test_count = len(commands["commands"].get("test", []))
    frontend_count = len(commands["commands"].get("frontend", []))

    sections = [
        f"# Scanner Report — {repo_name}",
        "",
        "## 1. 项目概览",
        "",
        f"- 项目名称：{repo_name}",
        f"- 项目路径：{inventory['repo']['path']}",
        "",
        "## 2. 命令候选",
        "",
        f"- build 命令数：{build_count}",
        f"- test 命令数：{test_count}",
        f"- frontend 命令数：{frontend_count}",
    ]

    analysis = inventory.get("analysis", {})
    if analysis.get("enabled"):
        sections.extend([
            "",
            "## 3. LLM 分析结果",
            "",
        ])
        sa = analysis.get("stackAnalysis", {})
        if sa and sa.get("primary"):
            sections.append(f"- 主技术栈：{sa['primary']['name']}（置信度：{sa['primary']['confidence']}）")
            for sec in sa.get("secondary", []):
                sections.append(f"- 辅助技术栈：{sec['name']}（置信度：{sec['confidence']}）")

        for mod in analysis.get("moduleAnalysis", []):
            sections.append(f"- 模块 [{mod['module']}]：{mod['guessedRole']}（置信度：{mod['confidence']}）")

        for anom in analysis.get("anomalies", []):
            sections.append(f"- ⚠️ 异常：{anom['message']}（置信度：{anom['confidence']}）")
    else:
        sections.extend(["", "## 3. 分析模式", "", "- 当前为确定性规则模式（未启用 LLM 分析）"])

    sections.extend([
        "",
        "## 4. 人工校准点",
        "",
        "- 请确认命令候选是否符合当前本地环境。",
        "- 请确认 Scanner 识别的模块是否符合项目真实边界。",
    ])

    return "\n".join(sections) + "\n"
```

**Step 4: Run all tests**

Command: `python3 -m pytest -v`
Expected: All PASS

**Step 5: Commit**

`git add harness_builder/scanner/report.py tests/scanner/test_report.py && git commit -m "feat: 增强报告，区分确定性事实和 LLM 推断"`

---

## Task 6：清理 — 删除旧文件，修复回归测试

**目标：** 删除 `llm_hints.py` 和 `test_llm_hints.py`，修复任何因接口变更导致的测试失败。

**Files:**
- Delete: `harness_builder/scanner/detectors/llm_hints.py`
- Delete: `tests/scanner/test_llm_hints.py`
- Fix: Any failing tests due to `llm_hints` import path changes

**Step 1: Check if llm_hints is imported anywhere**

Command: `grep -r "llm_hints" harness_builder/ tests/ --include="*.py"`
Expected: Only in `llm_hints.py` itself and its test file (should be safe to delete)

**Step 2: Delete the files**

```bash
git rm harness_builder/scanner/detectors/llm_hints.py tests/scanner/test_llm_hints.py
```

**Step 3: Run all tests**

Command: `python3 -m pytest -v`
Expected: All PASS (if any import errors, fix them)

**Step 4: Fix any regressions and commit**

`git commit -m "refactor: 删除旧 llm_hints，已完成迁移到 llm_analyzer"`

---

## Task 7：真实仓库冒烟验证

**目标：** 用 RuoYi-Vue 和 eShopOnWeb 做端到端验证（`--no-llm` 模式）。

**Step 1: Run on RuoYi-Vue**

Command: `python3 -m harness_builder.scanner.cli --repo /tmp/openclaw/harness-poc-targets/RuoYi-Vue --no-llm`

Expected: 生成 `.harness/` 三份文件，`project-inventory.json` 包含 `evidence` 和 `analysis` 字段。

**Step 2: Verify output**

```bash
cat /tmp/openclaw/harness-poc-targets/RuoYi-Vue/.harness/project-inventory.json | python3 -m json.tool | head -30
```

Expected: `analysis.enabled` 为 `false`，`analysis.commandCandidates` 包含 `mvn` 和 `npm` 命令。

**Step 3: Run on eShopOnWeb**

Command: `python3 -m harness_builder.scanner.cli --repo /tmp/openclaw/harness-poc-targets/eShopOnWeb --no-llm`

**Step 4: Record results**

Save smoke test results to `docs/research/scanner-refactor-smoke-test.md` and commit.

---

## Task 8：最终验证

**目标：** 确认所有测试通过、工作区干净、文档更新。

**Step 1: Full test suite**

Command: `python3 -m pytest -v`
Expected: ~125+ PASS, 0 FAIL

**Step 2: Git status clean**

Command: `git status`
Expected: `nothing to commit, working tree clean`

**Step 3: Update README.md**

Update `harness-builder/README.md` to reflect the new architecture:
- Three-phase pipeline description
- `--no-llm` flag documentation
- Updated "当前状态" section

**Step 4: Commit and done**

`git commit -m "docs: 更新 README 反映重构后架构"`
