# Harness Builder Scanner Skill 实施计划

> **给实现者：** 全程采用 TDD。每个任务先写失败测试，确认失败，再写最小实现，确认通过后提交。

**目标：** 实现一个自包含的 Harness Builder Scanner Skill，能够在当前工程根目录扫描工程资产，并生成 `.harness/project-inventory.json`、`.harness/command-catalog.yaml`、`.harness/scanner-report.md`。

**架构：** Scanner Skill 采用“确定性 detector + 通用兜底扫描 + LLM 假设层 + 输出契约 + 人类报告模板”的结构。确定性脚本负责生成 JSON/YAML 事实源；通用兜底扫描保证未知或非标准技术栈也能输出基础 inventory；LLM 只生成 hints 和人工校准建议。首轮支持 RuoYi-Vue 与 eShopOnWeb 两类技术栈，同时保证未知技术栈不会扫描失败。

**技术栈：** Python 3.11+、pytest、PyYAML、标准库 pathlib/json/xml/regex；暂不引入复杂静态分析框架。

---

## 0. 上下文与硬边界

### 0.1 参考文档

实现前必须阅读：

- `docs/superpowers/plans/2026-05-25-scanner-skill-requirements.md`
- `docs/superpowers/specs/POC-scanner-skill-design.md`
- 本地私密上下文：`private/context/Harness Builder — 产品整体规划 v1.0（内部上下文）.md`

注意：`private/` 已被 `.gitignore` 忽略，禁止提交其中任何内容。

### 0.2 当前阶段只做 Scanner Skill

本实施计划不包含：

- Task Mapping
- Risk Zones
- Restricted Paths
- Human Escalation
- Experience / Self-Improve
- Maturity Model
- AI Coding 执行
- Web UI

当前只实现：

```text
当前工程根目录 → Scanner Skill → .harness/ 三个文件
```

### 0.3 目标输出

```text
.harness/
  project-inventory.json
  command-catalog.yaml
  scanner-report.md
```

---

## 1. 目标目录结构

最终代码结构：

```text
harness_builder/
  __init__.py
  scanner/
    __init__.py
    cli.py
    core.py
    models.py
    report.py
    detectors/
      __init__.py
      filesystem.py
      java_maven.py
      node_frontend.py
      dotnet.py
      ci_docker.py
      shallow_code.py
      generic_fallback.py
      llm_hints.py
schemas/
  project-inventory.schema.json
  command-catalog.schema.json
tests/
  fixtures/
    minimal-java-maven/
    minimal-dotnet/
  scanner/
    test_cli.py
    test_filesystem.py
    test_java_maven.py
    test_node_frontend.py
    test_dotnet.py
    test_ci_docker.py
    test_shallow_code.py
    test_command_catalog.py
    test_report.py
    test_end_to_end.py
pyproject.toml
```

---

## 2. 任务列表

## Task 1：建立 Python 项目骨架与测试入口

**目标：** 建立最小 Python 包、pytest 配置和 CLI 帮助命令。

**文件：**

- 创建：`pyproject.toml`
- 创建：`harness_builder/__init__.py`
- 创建：`harness_builder/scanner/__init__.py`
- 创建：`harness_builder/scanner/cli.py`
- 创建：`tests/scanner/test_cli.py`

**Step 1：写失败测试**

`tests/scanner/test_cli.py`：

```python
import subprocess
import sys


def test_scanner_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli", "--help"],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "Harness Builder Scanner" in result.stdout
    assert "--repo" in result.stdout
    assert "--out" in result.stdout
```

**Step 2：运行测试，确认失败**

命令：

```bash
python -m pytest tests/scanner/test_cli.py -v
```

预期：失败，原因是 `harness_builder.scanner.cli` 不存在或没有 CLI。

**Step 3：最小实现**

`pyproject.toml`：

```toml
[project]
name = "harness-builder"
version = "0.1.0"
description = "Harness Builder Scanner Skill POC"
requires-python = ">=3.11"
dependencies = ["PyYAML>=6.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

`harness_builder/__init__.py`：

```python
__version__ = "0.1.0"
```

`harness_builder/scanner/__init__.py`：

```python
"""Harness Builder Scanner Skill."""
```

`harness_builder/scanner/cli.py`：

```python
import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness Builder Scanner")
    parser.add_argument("--repo", default=".", help="Repository root path. Defaults to current directory.")
    parser.add_argument("--out", default=None, help="Output directory. Defaults to <repo>/.harness.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    out = Path(args.out).resolve() if args.out else repo / ".harness"
    if not repo.exists():
        parser.error(f"repo path does not exist: {repo}")
    out.mkdir(parents=True, exist_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_cli.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add pyproject.toml harness_builder tests/scanner/test_cli.py && git commit -m "feat: 初始化 Scanner Skill Python 骨架"
```

---

## Task 2：文件系统扫描器

**目标：** 扫描工程顶层目录、关键文件、文件数量和扩展名统计。

**文件：**

- 创建：`harness_builder/scanner/models.py`
- 创建：`harness_builder/scanner/detectors/filesystem.py`
- 创建：`tests/fixtures/minimal-java-maven/README.md`
- 创建：`tests/fixtures/minimal-java-maven/pom.xml`
- 创建：`tests/fixtures/minimal-java-maven/src/main/java/com/example/App.java`
- 创建：`tests/scanner/test_filesystem.py`

**Step 1：写失败测试**

`tests/scanner/test_filesystem.py`：

```python
from pathlib import Path

from harness_builder.scanner.detectors.filesystem import scan_filesystem


def test_scan_filesystem_detects_top_level_and_counts():
    repo = Path("tests/fixtures/minimal-java-maven")

    result = scan_filesystem(repo)

    assert result["topLevelDirectories"] == ["src"]
    assert "README.md" in result["keyFiles"]
    assert "pom.xml" in result["keyFiles"]
    assert result["fileCounts"]["total"] >= 3
    assert result["fileCounts"]["byExtension"][".java"] == 1
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_filesystem.py -v
```

预期：FAIL，`scan_filesystem` 不存在。

**Step 3：最小实现**

`harness_builder/scanner/models.py`：

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScanContext:
    repo_root: Path
    out_dir: Path
    inventory: dict[str, Any] = field(default_factory=dict)
    commands: dict[str, Any] = field(default_factory=dict)
```

`harness_builder/scanner/detectors/filesystem.py`：

```python
from __future__ import annotations

from collections import Counter
from pathlib import Path

IGNORED_DIRS = {".git", ".harness", "node_modules", "target", "bin", "obj", ".venv", "__pycache__"}
KEY_FILE_NAMES = {
    "README.md",
    "CONTRIBUTING.md",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "package.json",
    "global.json",
    "docker-compose.yml",
    "Dockerfile",
}


def scan_filesystem(repo_root: Path) -> dict:
    top_dirs = sorted(p.name for p in repo_root.iterdir() if p.is_dir() and p.name not in IGNORED_DIRS)
    key_files: list[str] = []
    ext_counter: Counter[str] = Counter()
    total = 0

    for path in repo_root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        rel = path.relative_to(repo_root).as_posix()
        if path.is_file():
            total += 1
            ext_counter[path.suffix or "<none>"] += 1
            if path.name in KEY_FILE_NAMES or path.name.endswith(".sln") or path.name.endswith(".csproj"):
                key_files.append(rel)

    return {
        "topLevelDirectories": top_dirs,
        "keyFiles": sorted(key_files),
        "fileCounts": {
            "total": total,
            "byExtension": dict(sorted(ext_counter.items())),
        },
    }
```

创建 fixture：

`tests/fixtures/minimal-java-maven/README.md`：

```markdown
# Minimal Java Maven Fixture
```

`tests/fixtures/minimal-java-maven/pom.xml`：

```xml
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>minimal-java-maven</artifactId>
  <version>1.0.0</version>
</project>
```

`tests/fixtures/minimal-java-maven/src/main/java/com/example/App.java`：

```java
package com.example;

public class App {}
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_filesystem.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/models.py harness_builder/scanner/detectors/filesystem.py tests && git commit -m "feat: 添加文件系统扫描器"
```

---

## Task 3：Java / Maven 检测器

**目标：** 识别 Maven 项目、父 POM modules、Spring 配置和 SQL 资产。

**文件：**

- 创建：`harness_builder/scanner/detectors/java_maven.py`
- 修改：`tests/fixtures/minimal-java-maven/pom.xml`
- 创建：`tests/fixtures/minimal-java-maven/app/pom.xml`
- 创建：`tests/fixtures/minimal-java-maven/app/src/main/resources/application.yml`
- 创建：`tests/fixtures/minimal-java-maven/sql/schema.sql`
- 创建：`tests/scanner/test_java_maven.py`

**Step 1：写失败测试**

`tests/scanner/test_java_maven.py`：

```python
from pathlib import Path

from harness_builder.scanner.detectors.java_maven import detect_java_maven


def test_detect_java_maven_modules_and_assets():
    repo = Path("tests/fixtures/minimal-java-maven")

    result = detect_java_maven(repo)

    assert result["detected"] is True
    assert result["buildFiles"] == ["pom.xml", "app/pom.xml"]
    assert result["mavenModules"] == [{"name": "app", "path": "app"}]
    assert "app/src/main/resources/application.yml" in result["springConfigFiles"]
    assert "sql/schema.sql" in result["sqlAssets"]
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_java_maven.py -v
```

预期：FAIL。

**Step 3：最小实现**

`harness_builder/scanner/detectors/java_maven.py`：

```python
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def _strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _find_child_text(root: ET.Element, name: str) -> list[str]:
    values: list[str] = []
    for child in root.iter():
        if _strip_namespace(child.tag) == name and child.text:
            values.append(child.text.strip())
    return values


def _read_modules(pom_path: Path) -> list[str]:
    try:
        root = ET.parse(pom_path).getroot()
    except ET.ParseError:
        return []
    return _find_child_text(root, "module")


def detect_java_maven(repo_root: Path) -> dict:
    pom_files = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.rglob("pom.xml"))
    root_pom = repo_root / "pom.xml"
    modules = _read_modules(root_pom) if root_pom.exists() else []
    spring_configs = sorted(
        p.relative_to(repo_root).as_posix()
        for pattern in ("application.yml", "application.yaml", "application.properties")
        for p in repo_root.rglob(pattern)
    )
    sql_assets = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.rglob("*.sql"))

    return {
        "detected": bool(pom_files),
        "buildFiles": pom_files,
        "mavenModules": [{"name": m, "path": m} for m in modules],
        "springConfigFiles": spring_configs,
        "sqlAssets": sql_assets,
    }
```

更新 fixture：

`tests/fixtures/minimal-java-maven/pom.xml`：

```xml
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>minimal-java-maven</artifactId>
  <version>1.0.0</version>
  <packaging>pom</packaging>
  <modules>
    <module>app</module>
  </modules>
</project>
```

`tests/fixtures/minimal-java-maven/app/pom.xml`：

```xml
<project>
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>com.example</groupId>
    <artifactId>minimal-java-maven</artifactId>
    <version>1.0.0</version>
  </parent>
  <artifactId>app</artifactId>
</project>
```

`tests/fixtures/minimal-java-maven/app/src/main/resources/application.yml`：

```yaml
server:
  port: 8080
```

`tests/fixtures/minimal-java-maven/sql/schema.sql`：

```sql
create table demo_user (id bigint primary key);
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_java_maven.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/detectors/java_maven.py tests && git commit -m "feat: 添加 Java Maven 检测器"
```

---

## Task 4：Node / Vue 前端检测器

**目标：** 识别 package.json、scripts 和 Vue 文件。

**文件：**

- 创建：`harness_builder/scanner/detectors/node_frontend.py`
- 创建：`tests/fixtures/minimal-java-maven/frontend/package.json`
- 创建：`tests/fixtures/minimal-java-maven/frontend/src/App.vue`
- 创建：`tests/scanner/test_node_frontend.py`

**Step 1：写失败测试**

`tests/scanner/test_node_frontend.py`：

```python
from pathlib import Path

from harness_builder.scanner.detectors.node_frontend import detect_node_frontend


def test_detect_node_frontend_scripts_and_vue_files():
    repo = Path("tests/fixtures/minimal-java-maven")

    result = detect_node_frontend(repo)

    assert result["detected"] is True
    assert result["projects"][0]["path"] == "frontend"
    assert result["projects"][0]["scripts"]["build"] == "vite build"
    assert result["projects"][0]["vueFileCount"] == 1
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_node_frontend.py -v
```

预期：FAIL。

**Step 3：最小实现**

`harness_builder/scanner/detectors/node_frontend.py`：

```python
from __future__ import annotations

import json
from pathlib import Path

IGNORED_PARTS = {"node_modules", ".git", ".harness"}


def detect_node_frontend(repo_root: Path) -> dict:
    projects: list[dict] = []
    for package_json in sorted(repo_root.rglob("package.json")):
        if any(part in IGNORED_PARTS for part in package_json.parts):
            continue
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        project_dir = package_json.parent
        vue_count = sum(1 for _ in project_dir.rglob("*.vue"))
        projects.append(
            {
                "path": project_dir.relative_to(repo_root).as_posix() or ".",
                "packageFile": package_json.relative_to(repo_root).as_posix(),
                "scripts": data.get("scripts", {}),
                "dependencies": sorted((data.get("dependencies") or {}).keys()),
                "devDependencies": sorted((data.get("devDependencies") or {}).keys()),
                "vueFileCount": vue_count,
            }
        )
    return {"detected": bool(projects), "projects": projects}
```

创建 fixture：

`tests/fixtures/minimal-java-maven/frontend/package.json`：

```json
{
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "vite build"
  },
  "dependencies": {
    "vue": "^3.0.0"
  }
}
```

`tests/fixtures/minimal-java-maven/frontend/src/App.vue`：

```vue
<template><div>Hello</div></template>
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_node_frontend.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/detectors/node_frontend.py tests && git commit -m "feat: 添加 Node Vue 前端检测器"
```

---

## Task 5：.NET 检测器

**目标：** 识别 `.sln`、`.csproj`、`global.json`、项目引用和测试项目。

**文件：**

- 创建：`harness_builder/scanner/detectors/dotnet.py`
- 创建：`tests/fixtures/minimal-dotnet/Demo.sln`
- 创建：`tests/fixtures/minimal-dotnet/global.json`
- 创建：`tests/fixtures/minimal-dotnet/src/Web/Web.csproj`
- 创建：`tests/fixtures/minimal-dotnet/src/ApplicationCore/ApplicationCore.csproj`
- 创建：`tests/fixtures/minimal-dotnet/tests/UnitTests/UnitTests.csproj`
- 创建：`tests/scanner/test_dotnet.py`

**Step 1：写失败测试**

`tests/scanner/test_dotnet.py`：

```python
from pathlib import Path

from harness_builder.scanner.detectors.dotnet import detect_dotnet


def test_detect_dotnet_solution_projects_and_tests():
    repo = Path("tests/fixtures/minimal-dotnet")

    result = detect_dotnet(repo)

    assert result["detected"] is True
    assert result["solutions"] == ["Demo.sln"]
    project_paths = [p["path"] for p in result["projects"]]
    assert "src/Web/Web.csproj" in project_paths
    assert "src/ApplicationCore/ApplicationCore.csproj" in project_paths
    assert result["testProjects"] == ["tests/UnitTests/UnitTests.csproj"]
    assert result["globalJson"] == "global.json"
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_dotnet.py -v
```

预期：FAIL。

**Step 3：最小实现**

`harness_builder/scanner/detectors/dotnet.py`：

```python
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def _strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _project_references(csproj: Path, repo_root: Path) -> list[str]:
    try:
        root = ET.parse(csproj).getroot()
    except ET.ParseError:
        return []
    refs: list[str] = []
    for node in root.iter():
        if _strip_namespace(node.tag) == "ProjectReference" and "Include" in node.attrib:
            ref = (csproj.parent / node.attrib["Include"]).resolve()
            try:
                refs.append(ref.relative_to(repo_root).as_posix())
            except ValueError:
                refs.append(node.attrib["Include"])
    return refs


def detect_dotnet(repo_root: Path) -> dict:
    solutions = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.rglob("*.sln"))
    csprojs = sorted(repo_root.rglob("*.csproj"))
    projects: list[dict] = []
    test_projects: list[str] = []
    for csproj in csprojs:
        rel = csproj.relative_to(repo_root).as_posix()
        is_test = "test" in rel.lower() or csproj.name.lower().endswith("tests.csproj")
        projects.append({"path": rel, "name": csproj.stem, "isTest": is_test, "projectReferences": _project_references(csproj, repo_root)})
        if is_test:
            test_projects.append(rel)
    global_json = repo_root / "global.json"
    return {
        "detected": bool(solutions or projects),
        "solutions": solutions,
        "projects": projects,
        "testProjects": sorted(test_projects),
        "globalJson": "global.json" if global_json.exists() else None,
    }
```

创建 fixture 文件：

`tests/fixtures/minimal-dotnet/Demo.sln`：

```text
Microsoft Visual Studio Solution File, Format Version 12.00
```

`tests/fixtures/minimal-dotnet/global.json`：

```json
{"sdk": {"version": "8.0.100"}}
```

`tests/fixtures/minimal-dotnet/src/Web/Web.csproj`：

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">
  <ItemGroup>
    <ProjectReference Include="../ApplicationCore/ApplicationCore.csproj" />
  </ItemGroup>
</Project>
```

`tests/fixtures/minimal-dotnet/src/ApplicationCore/ApplicationCore.csproj`：

```xml
<Project Sdk="Microsoft.NET.Sdk" />
```

`tests/fixtures/minimal-dotnet/tests/UnitTests/UnitTests.csproj`：

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <ProjectReference Include="../../src/ApplicationCore/ApplicationCore.csproj" />
  </ItemGroup>
</Project>
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_dotnet.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/detectors/dotnet.py tests && git commit -m "feat: 添加 dotnet 检测器"
```

---

## Task 6：CI / Docker 检测器

**目标：** 识别 GitHub Actions、Dockerfile、docker-compose 文件。

**文件：**

- 创建：`harness_builder/scanner/detectors/ci_docker.py`
- 创建：`tests/fixtures/minimal-dotnet/.github/workflows/dotnetcore.yml`
- 创建：`tests/fixtures/minimal-dotnet/docker-compose.yml`
- 创建：`tests/scanner/test_ci_docker.py`

**Step 1：写失败测试**

`tests/scanner/test_ci_docker.py`：

```python
from pathlib import Path

from harness_builder.scanner.detectors.ci_docker import detect_ci_docker


def test_detect_ci_and_docker_assets():
    repo = Path("tests/fixtures/minimal-dotnet")

    result = detect_ci_docker(repo)

    assert result["githubActions"] == [".github/workflows/dotnetcore.yml"]
    assert result["dockerComposeFiles"] == ["docker-compose.yml"]
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_ci_docker.py -v
```

预期：FAIL。

**Step 3：最小实现**

`harness_builder/scanner/detectors/ci_docker.py`：

```python
from __future__ import annotations

from pathlib import Path


def detect_ci_docker(repo_root: Path) -> dict:
    workflows = sorted(p.relative_to(repo_root).as_posix() for p in (repo_root / ".github" / "workflows").glob("*.yml")) if (repo_root / ".github" / "workflows").exists() else []
    workflows += sorted(p.relative_to(repo_root).as_posix() for p in (repo_root / ".github" / "workflows").glob("*.yaml")) if (repo_root / ".github" / "workflows").exists() else []
    compose = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.glob("docker-compose*.yml"))
    compose += sorted(p.relative_to(repo_root).as_posix() for p in repo_root.glob("docker-compose*.yaml"))
    dockerfiles = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.rglob("Dockerfile"))
    return {"githubActions": sorted(workflows), "dockerComposeFiles": sorted(compose), "dockerfiles": dockerfiles}
```

创建 fixture：

`tests/fixtures/minimal-dotnet/.github/workflows/dotnetcore.yml`：

```yaml
name: dotnetcore
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: dotnet build
```

`tests/fixtures/minimal-dotnet/docker-compose.yml`：

```yaml
services:
  web:
    build: .
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_ci_docker.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/detectors/ci_docker.py tests && git commit -m "feat: 添加 CI 和 Docker 检测器"
```

---

## Task 7：浅层代码结构检测器

**目标：** 用轻量规则识别 Controller/API、Service、Entity/Model、Test 文件。

**文件：**

- 创建：`harness_builder/scanner/detectors/shallow_code.py`
- 创建：`tests/fixtures/minimal-java-maven/app/src/main/java/com/example/UserController.java`
- 创建：`tests/fixtures/minimal-java-maven/app/src/main/java/com/example/UserService.java`
- 创建：`tests/fixtures/minimal-dotnet/src/Web/Controllers/CatalogController.cs`
- 创建：`tests/scanner/test_shallow_code.py`

**Step 1：写失败测试**

`tests/scanner/test_shallow_code.py`：

```python
from pathlib import Path

from harness_builder.scanner.detectors.shallow_code import detect_shallow_code_structure


def test_detect_shallow_java_and_dotnet_code_roles():
    java_repo = Path("tests/fixtures/minimal-java-maven")
    dotnet_repo = Path("tests/fixtures/minimal-dotnet")

    java_result = detect_shallow_code_structure(java_repo)
    dotnet_result = detect_shallow_code_structure(dotnet_repo)

    assert "app/src/main/java/com/example/UserController.java" in java_result["controllers"]
    assert "app/src/main/java/com/example/UserService.java" in java_result["services"]
    assert "src/Web/Controllers/CatalogController.cs" in dotnet_result["controllers"]
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_shallow_code.py -v
```

预期：FAIL。

**Step 3：最小实现**

`harness_builder/scanner/detectors/shallow_code.py`：

```python
from __future__ import annotations

from pathlib import Path

IGNORED_PARTS = {".git", ".harness", "node_modules", "target", "bin", "obj"}


def detect_shallow_code_structure(repo_root: Path) -> dict:
    result = {"controllers": [], "services": [], "entitiesOrModels": [], "tests": [], "frontendComponents": []}
    for path in repo_root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        rel = path.relative_to(repo_root).as_posix()
        name = path.name.lower()
        if name.endswith(("controller.java", "controller.cs")) or "/controllers/" in rel.lower():
            result["controllers"].append(rel)
        if name.endswith(("service.java", "service.cs")) or "/services/" in rel.lower():
            result["services"].append(rel)
        if name.endswith(("entity.java", "model.java", "model.cs")) or "/models/" in rel.lower():
            result["entitiesOrModels"].append(rel)
        if "test" in rel.lower() and path.suffix in {".java", ".cs", ".js", ".ts"}:
            result["tests"].append(rel)
        if path.suffix in {".vue", ".tsx", ".jsx"}:
            result["frontendComponents"].append(rel)
    return {key: sorted(value) for key, value in result.items()}
```

创建 fixture：

`tests/fixtures/minimal-java-maven/app/src/main/java/com/example/UserController.java`：

```java
package com.example;

public class UserController {}
```

`tests/fixtures/minimal-java-maven/app/src/main/java/com/example/UserService.java`：

```java
package com.example;

public class UserService {}
```

`tests/fixtures/minimal-dotnet/src/Web/Controllers/CatalogController.cs`：

```csharp
namespace Demo.Web.Controllers;

public class CatalogController {}
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_shallow_code.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/detectors/shallow_code.py tests && git commit -m "feat: 添加浅层代码结构检测器"
```

---

## Task 8：命令目录生成器

**目标：** 从检测结果生成 `command-catalog.yaml`。

**文件：**

- 创建：`harness_builder/scanner/core.py`
- 创建：`tests/scanner/test_command_catalog.py`

**Step 1：写失败测试**

`tests/scanner/test_command_catalog.py`：

```python
from pathlib import Path

from harness_builder.scanner.core import scan_repository


def test_command_catalog_contains_maven_and_frontend_commands(tmp_path):
    repo = Path("tests/fixtures/minimal-java-maven")
    out = tmp_path / ".harness"

    result = scan_repository(repo, out)

    commands = result.commands
    build_commands = [cmd["command"] for cmd in commands["commands"]["build"]]
    frontend_commands = [cmd["command"] for cmd in commands["commands"]["frontend"]]

    assert "mvn clean package -DskipTests" in build_commands
    assert "npm run build" in frontend_commands
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_command_catalog.py -v
```

预期：FAIL。

**Step 3：最小实现**

`harness_builder/scanner/core.py`：

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness_builder.scanner.detectors.filesystem import scan_filesystem
from harness_builder.scanner.detectors.java_maven import detect_java_maven
from harness_builder.scanner.detectors.node_frontend import detect_node_frontend


@dataclass
class ScanResult:
    inventory: dict[str, Any]
    commands: dict[str, Any]


def _command(name: str, command: str, source: str, working_directory: str = ".", confidence: str = "medium") -> dict:
    return {
        "name": name,
        "command": command,
        "workingDirectory": working_directory,
        "source": source,
        "confidence": confidence,
        "verified": False,
    }


def _build_command_catalog(repo_name: str, java: dict, node: dict) -> dict:
    catalog = {"repo": repo_name, "commands": {"build": [], "test": [], "run": [], "frontend": [], "docker": []}}
    if java.get("detected"):
        catalog["commands"]["build"].append(_command("maven-package", "mvn clean package -DskipTests", "pom.xml", confidence="high"))
        catalog["commands"]["test"].append(_command("maven-test", "mvn test", "pom.xml", confidence="medium"))
    for project in node.get("projects", []):
        scripts = project.get("scripts", {})
        if "build" in scripts:
            catalog["commands"]["frontend"].append(_command("frontend-build", "npm run build", project["packageFile"], project["path"], "high"))
        if "dev" in scripts:
            catalog["commands"]["run"].append(_command("frontend-dev", "npm run dev", project["packageFile"], project["path"], "medium"))
    return catalog


def scan_repository(repo_root: Path, out_dir: Path) -> ScanResult:
    repo_root = repo_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    fs = scan_filesystem(repo_root)
    java = detect_java_maven(repo_root)
    node = detect_node_frontend(repo_root)
    inventory = {"repo": {"name": repo_root.name, "path": str(repo_root)}, "structure": fs, "stackExtensions": {"java": java, "node": node}}
    commands = _build_command_catalog(repo_root.name, java, node)
    return ScanResult(inventory=inventory, commands=commands)
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_command_catalog.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/core.py tests/scanner/test_command_catalog.py && git commit -m "feat: 生成基础命令目录"
```

---

## Task 9：端到端写出 `.harness/` 文件

**目标：** CLI 调用后写出 JSON/YAML/Markdown 三个文件。

**文件：**

- 修改：`harness_builder/scanner/cli.py`
- 修改：`harness_builder/scanner/core.py`
- 创建：`harness_builder/scanner/report.py`
- 创建：`tests/scanner/test_end_to_end.py`

**Step 1：写失败测试**

`tests/scanner/test_end_to_end.py`：

```python
import json
import subprocess
import sys
from pathlib import Path

import yaml


def test_cli_generates_harness_files(tmp_path):
    repo = Path("tests/fixtures/minimal-java-maven").resolve()
    out = tmp_path / ".harness"

    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(repo), "--out", str(out)],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    inventory = json.loads((out / "project-inventory.json").read_text())
    commands = yaml.safe_load((out / "command-catalog.yaml").read_text())
    report = (out / "scanner-report.md").read_text()

    assert inventory["repo"]["name"] == "minimal-java-maven"
    assert commands["repo"] == "minimal-java-maven"
    assert "# Scanner Report" in report
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_end_to_end.py -v
```

预期：FAIL，尚未写文件。

**Step 3：最小实现**

`harness_builder/scanner/report.py`：

```python
from __future__ import annotations

from typing import Any


def render_scanner_report(inventory: dict[str, Any], commands: dict[str, Any]) -> str:
    repo_name = inventory["repo"]["name"]
    build_count = len(commands["commands"].get("build", []))
    test_count = len(commands["commands"].get("test", []))
    frontend_count = len(commands["commands"].get("frontend", []))
    return f"""# Scanner Report — {repo_name}

## 1. 项目概览

- 项目名称：{repo_name}
- 项目路径：{inventory['repo']['path']}

## 2. 命令候选

- build 命令数：{build_count}
- test 命令数：{test_count}
- frontend 命令数：{frontend_count}

## 3. 人工校准点

- 请确认命令候选是否符合当前本地环境。
- 请确认 Scanner 识别的模块是否符合项目真实边界。
"""
```

修改 `harness_builder/scanner/core.py`：

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from harness_builder.scanner.detectors.filesystem import scan_filesystem
from harness_builder.scanner.detectors.java_maven import detect_java_maven
from harness_builder.scanner.detectors.node_frontend import detect_node_frontend
from harness_builder.scanner.report import render_scanner_report


@dataclass
class ScanResult:
    inventory: dict[str, Any]
    commands: dict[str, Any]


def _command(name: str, command: str, source: str, working_directory: str = ".", confidence: str = "medium") -> dict:
    return {
        "name": name,
        "command": command,
        "workingDirectory": working_directory,
        "source": source,
        "confidence": confidence,
        "verified": False,
    }


def _build_command_catalog(repo_name: str, java: dict, node: dict) -> dict:
    catalog = {"repo": repo_name, "commands": {"build": [], "test": [], "run": [], "frontend": [], "docker": []}}
    if java.get("detected"):
        catalog["commands"]["build"].append(_command("maven-package", "mvn clean package -DskipTests", "pom.xml", confidence="high"))
        catalog["commands"]["test"].append(_command("maven-test", "mvn test", "pom.xml", confidence="medium"))
    for project in node.get("projects", []):
        scripts = project.get("scripts", {})
        if "build" in scripts:
            catalog["commands"]["frontend"].append(_command("frontend-build", "npm run build", project["packageFile"], project["path"], "high"))
        if "dev" in scripts:
            catalog["commands"]["run"].append(_command("frontend-dev", "npm run dev", project["packageFile"], project["path"], "medium"))
    return catalog


def scan_repository(repo_root: Path, out_dir: Path) -> ScanResult:
    repo_root = repo_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    fs = scan_filesystem(repo_root)
    java = detect_java_maven(repo_root)
    node = detect_node_frontend(repo_root)
    inventory = {"repo": {"name": repo_root.name, "path": str(repo_root)}, "structure": fs, "stackExtensions": {"java": java, "node": node}}
    commands = _build_command_catalog(repo_root.name, java, node)
    return ScanResult(inventory=inventory, commands=commands)


def write_scan_outputs(result: ScanResult, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "project-inventory.json").write_text(json.dumps(result.inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "command-catalog.yaml").write_text(yaml.safe_dump(result.commands, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (out_dir / "scanner-report.md").write_text(render_scanner_report(result.inventory, result.commands), encoding="utf-8")
```

修改 `harness_builder/scanner/cli.py`：

```python
import argparse
from pathlib import Path

from harness_builder.scanner.core import scan_repository, write_scan_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness Builder Scanner")
    parser.add_argument("--repo", default=".", help="Repository root path. Defaults to current directory.")
    parser.add_argument("--out", default=None, help="Output directory. Defaults to <repo>/.harness.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    out = Path(args.out).resolve() if args.out else repo / ".harness"
    if not repo.exists():
        parser.error(f"repo path does not exist: {repo}")
    result = scan_repository(repo, out)
    write_scan_outputs(result, out)
    print(f"Generated Harness scanner outputs at {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_end_to_end.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner tests && git commit -m "feat: 写出 scanner 输出文件"
```

---

## Task 10：补齐 .NET 命令目录集成

**目标：** `scan_repository` 集成 dotnet detector，并生成 dotnet build/test 命令。

**文件：**

- 修改：`harness_builder/scanner/core.py`
- 创建：`tests/scanner/test_dotnet_command_catalog.py`

**Step 1：写失败测试**

`tests/scanner/test_dotnet_command_catalog.py`：

```python
from pathlib import Path

from harness_builder.scanner.core import scan_repository


def test_command_catalog_contains_dotnet_build_and_test(tmp_path):
    repo = Path("tests/fixtures/minimal-dotnet")
    out = tmp_path / ".harness"

    result = scan_repository(repo, out)

    build_commands = [cmd["command"] for cmd in result.commands["commands"]["build"]]
    test_commands = [cmd["command"] for cmd in result.commands["commands"]["test"]]

    assert "dotnet build" in build_commands
    assert "dotnet test" in test_commands
    assert result.inventory["stackExtensions"]["dotnet"]["detected"] is True
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_dotnet_command_catalog.py -v
```

预期：FAIL。

**Step 3：最小实现**

在 `core.py` 中：

- import `detect_dotnet`
- `dotnet = detect_dotnet(repo_root)`
- inventory 写入 `stackExtensions.dotnet`
- 如果 dotnet detected，command catalog 添加：

```python
catalog["commands"]["build"].append(_command("dotnet-build", "dotnet build", "*.sln", confidence="high"))
catalog["commands"]["test"].append(_command("dotnet-test", "dotnet test", "*.sln", confidence="high"))
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_dotnet_command_catalog.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/core.py tests/scanner/test_dotnet_command_catalog.py && git commit -m "feat: 集成 dotnet 命令目录"
```

---

## Task 11：通用兜底扫描器

**目标：** 当没有明确 detector 命中时，仍然生成基础 inventory，并标记 unknown/mixed 技术栈和人工校准点。

**文件：**

- 创建：`harness_builder/scanner/detectors/generic_fallback.py`
- 创建：`tests/fixtures/unknown-stack/README.md`
- 创建：`tests/fixtures/unknown-stack/scripts/build.custom`
- 创建：`tests/fixtures/unknown-stack/config/app.conf`
- 创建：`tests/scanner/test_generic_fallback.py`

**Step 1：写失败测试**

`tests/scanner/test_generic_fallback.py`：

```python
from pathlib import Path

from harness_builder.scanner.detectors.generic_fallback import detect_generic_fallback


def test_generic_fallback_handles_unknown_stack():
    repo = Path("tests/fixtures/unknown-stack")

    result = detect_generic_fallback(repo)

    assert result["stackClassification"] in {"unknown", "mixed"}
    assert "README.md" in result["documentation"]
    assert "scripts/build.custom" in result["scriptCandidates"]
    assert "config/app.conf" in result["configCandidates"]
    assert result["manualCalibrationPoints"]
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_generic_fallback.py -v
```

预期：FAIL。

**Step 3：最小实现**

`harness_builder/scanner/detectors/generic_fallback.py`：

```python
from __future__ import annotations

from pathlib import Path

SCRIPT_DIR_NAMES = {"scripts", "bin", "tools"}
CONFIG_DIR_NAMES = {"config", "conf", "settings"}
DOC_NAMES = {"README.md", "CONTRIBUTING.md"}


def detect_generic_fallback(repo_root: Path) -> dict:
    documentation = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.rglob("*") if p.is_file() and p.name in DOC_NAMES)
    script_candidates = sorted(
        p.relative_to(repo_root).as_posix()
        for p in repo_root.rglob("*")
        if p.is_file() and any(part in SCRIPT_DIR_NAMES for part in p.relative_to(repo_root).parts)
    )
    config_candidates = sorted(
        p.relative_to(repo_root).as_posix()
        for p in repo_root.rglob("*")
        if p.is_file() and any(part in CONFIG_DIR_NAMES for part in p.relative_to(repo_root).parts)
    )
    return {
        "stackClassification": "unknown",
        "documentation": documentation,
        "scriptCandidates": script_candidates,
        "configCandidates": config_candidates,
        "manualCalibrationPoints": [
            "未识别到受支持的主技术栈 detector，请人工确认构建系统和测试命令。"
        ],
    }
```

创建 fixture 文件：

`tests/fixtures/unknown-stack/README.md`：

```markdown
# Unknown Stack Fixture
```

`tests/fixtures/unknown-stack/scripts/build.custom`：

```text
custom build
```

`tests/fixtures/unknown-stack/config/app.conf`：

```text
port=8080
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_generic_fallback.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/detectors/generic_fallback.py tests && git commit -m "feat: 添加通用兜底扫描器"
```

---

## Task 12：LLM hints 数据结构与占位输出

**目标：** 定义 LLM 兜底输出的位置和结构，但首轮不实际调用模型。先生成空 hints 或基于规则的提示，保证后续可扩展。

**文件：**

- 创建：`harness_builder/scanner/detectors/llm_hints.py`
- 创建：`tests/scanner/test_llm_hints.py`

**Step 1：写失败测试**

`tests/scanner/test_llm_hints.py`：

```python
from harness_builder.scanner.detectors.llm_hints import build_llm_hint_placeholder


def test_llm_hint_placeholder_is_separate_from_facts():
    hints = build_llm_hint_placeholder(["未识别到主技术栈"])

    assert hints["enabled"] is False
    assert hints["hints"][0]["type"] == "manual-calibration"
    assert hints["hints"][0]["confidence"] == "low"
    assert "evidence" in hints["hints"][0]
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_llm_hints.py -v
```

预期：FAIL。

**Step 3：最小实现**

`harness_builder/scanner/detectors/llm_hints.py`：

```python
from __future__ import annotations


def build_llm_hint_placeholder(manual_points: list[str]) -> dict:
    return {
        "enabled": False,
        "policy": "LLM 只能生成 hints 和人工校准建议，不得覆盖确定性事实源。",
        "hints": [
            {
                "type": "manual-calibration",
                "message": point,
                "confidence": "low",
                "evidence": [],
            }
            for point in manual_points
        ],
    }
```

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_llm_hints.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/detectors/llm_hints.py tests/scanner/test_llm_hints.py && git commit -m "feat: 定义 LLM 兜底提示结构"
```

---

## Task 13：集成兜底输出到 inventory

**目标：** `scan_repository` 集成 generic fallback 和 llm hints。未知项目也能输出三份文件。

**文件：**

- 修改：`harness_builder/scanner/core.py`
- 创建：`tests/scanner/test_unknown_stack_end_to_end.py`

**Step 1：写失败测试**

`tests/scanner/test_unknown_stack_end_to_end.py`：

```python
import json
import subprocess
import sys
from pathlib import Path


def test_unknown_stack_still_generates_outputs(tmp_path):
    repo = Path("tests/fixtures/unknown-stack").resolve()
    out = tmp_path / ".harness"

    result = subprocess.run(
        [sys.executable, "-m", "harness_builder.scanner.cli", "--repo", str(repo), "--out", str(out)],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    inventory = json.loads((out / "project-inventory.json").read_text())
    assert inventory["stackExtensions"]["genericFallback"]["stackClassification"] == "unknown"
    assert inventory["llmHints"]["enabled"] is False
    assert (out / "command-catalog.yaml").exists()
    assert (out / "scanner-report.md").exists()
```

**Step 2：运行测试，确认失败**

```bash
python -m pytest tests/scanner/test_unknown_stack_end_to_end.py -v
```

预期：FAIL。

**Step 3：最小实现**

在 `core.py` 中：

- import `detect_generic_fallback`
- import `build_llm_hint_placeholder`
- 运行 generic fallback。
- 将结果写入 `stackExtensions.genericFallback`。
- 将 manual calibration points 汇总到 `manualCalibrationPoints`。
- 将 LLM hints 写入 `llmHints`。
- 即使没有任何 build/test 命令，也输出空 command catalog。

**Step 4：运行测试，确认通过**

```bash
python -m pytest tests/scanner/test_unknown_stack_end_to_end.py -v
```

预期：PASS。

**Step 5：提交**

```bash
git add harness_builder/scanner/core.py tests/scanner/test_unknown_stack_end_to_end.py && git commit -m "feat: 集成未知技术栈兜底输出"
```

---

## Task 14：真实目标仓库冒烟验证

**目标：** 在 RuoYi-Vue 与 eShopOnWeb 上运行 Scanner，验证生成三份输出。

**文件：**

- 创建：`docs/research/scanner-smoke-test-results.md`

**Step 1：准备目标仓库**

命令：

```bash
mkdir -p /tmp/openclaw/harness-poc-targets
cd /tmp/openclaw/harness-poc-targets
[ -d RuoYi-Vue ] || git clone --depth 1 https://github.com/yangzongzhuan/RuoYi-Vue.git RuoYi-Vue
[ -d eShopOnWeb ] || git clone --depth 1 https://github.com/dotnet-architecture/eShopOnWeb.git eShopOnWeb
```

**Step 2：运行 Scanner**

```bash
python -m harness_builder.scanner.cli --repo /tmp/openclaw/harness-poc-targets/RuoYi-Vue
python -m harness_builder.scanner.cli --repo /tmp/openclaw/harness-poc-targets/eShopOnWeb
```

预期：两个仓库都生成：

```text
.harness/project-inventory.json
.harness/command-catalog.yaml
.harness/scanner-report.md
```

**Step 3：记录结果**

`docs/research/scanner-smoke-test-results.md`：

```markdown
# Scanner Skill 冒烟验证结果

## RuoYi-Vue

- project-inventory.json：已生成 / 未生成
- command-catalog.yaml：已生成 / 未生成
- scanner-report.md：已生成 / 未生成
- 识别到的技术栈：
- 识别到的 build/test/frontend 命令：
- 人工校准点：

## eShopOnWeb

- project-inventory.json：已生成 / 未生成
- command-catalog.yaml：已生成 / 未生成
- scanner-report.md：已生成 / 未生成
- 识别到的技术栈：
- 识别到的 build/test/frontend 命令：
- 人工校准点：

## 结论

- Core schema 是否稳定：
- 技术栈扩展字段是否有用：
- 下一阶段 Task Mapping Skill 需要哪些字段：
```

**Step 4：提交**

```bash
git add docs/research/scanner-smoke-test-results.md && git commit -m "test: 记录 Scanner 真实仓库冒烟结果"
```

---

## Task 15：最终验证

**目标：** 确认 Scanner 第一阶段满足需求文档。

**验证命令：**

```bash
python -m pytest -v
python -m harness_builder.scanner.cli --repo /tmp/openclaw/harness-poc-targets/RuoYi-Vue
python -m harness_builder.scanner.cli --repo /tmp/openclaw/harness-poc-targets/eShopOnWeb
```

**检查点：**

- RuoYi-Vue 输出 `.harness/project-inventory.json`
- RuoYi-Vue 输出 `.harness/command-catalog.yaml`
- RuoYi-Vue 输出 `.harness/scanner-report.md`
- eShopOnWeb 输出 `.harness/project-inventory.json`
- eShopOnWeb 输出 `.harness/command-catalog.yaml`
- eShopOnWeb 输出 `.harness/scanner-report.md`
- JSON/YAML 中存在统一 core schema
- Java / .NET 差异进入 stack extensions
- Markdown 报告不包含事实源之外的关键判断

**提交：**

```bash
git status
git log --oneline -5
```

最终无需额外代码提交；如果文档有更新，再提交：

```bash
git add docs && git commit -m "docs: 完成 Scanner Skill 第一阶段验证"
```

---

## 3. 执行模式建议

建议采用 **subagent-driven** 执行模式，但每个 sub-agent 一次只做一个任务，并在每个任务完成后做 review。

推荐顺序：

1. Task 1–2：一个实现子代理。
2. Task 3–4：一个实现子代理。
3. Task 5–6：一个实现子代理。
4. Task 7–8：一个实现子代理。
5. Task 9–10：一个实现子代理。
6. Task 11–13：一个实现子代理，专门处理未知技术栈和 LLM hints 兜底。
7. Task 14–15：主会话执行真实仓库验证和最终判断。

每个任务必须满足：

```text
测试先失败 → 最小实现 → 测试通过 → 提交
```

---

## 4. 下一步

本实施计划经确认后，进入 Superpowers subagent-driven development 阶段。

首个执行任务：Task 1，建立 Python 项目骨架与测试入口。
