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
