from __future__ import annotations

from typing import Any


def render_scanner_report(inventory: dict[str, Any], commands: dict[str, Any]) -> str:
    repo_name = inventory.get("repo", {}).get("name", "unknown")
    repo_path = inventory.get("repo", {}).get("path", "unknown")

    analysis = inventory.get("analysis", {})
    evidence = inventory.get("evidence", {})
    validation = inventory.get("validation", {})
    file_tree = inventory.get("fileTree", {})

    analysis_enabled = analysis.get("enabled", False) if isinstance(analysis, dict) else False
    stack_analysis = analysis.get("stackAnalysis", {}) if analysis_enabled else {}
    module_analysis = analysis.get("moduleAnalysis", []) if analysis_enabled else []
    arch_pattern = analysis.get("architecturePattern") if analysis_enabled else None
    anomalies = analysis.get("anomalies", []) if analysis_enabled else []

    cmds = commands.get("commands", {})
    build_cmds = cmds.get("build", [])
    test_cmds = cmds.get("test", [])
    frontend_cmds = cmds.get("frontend", [])
    run_cmds = cmds.get("run", [])
    docker_cmds = cmds.get("docker", [])

    sections = []

    # Header
    sections.append("# Scanner Report — {}\n".format(repo_name))

    # 1. Overview
    sections.append("## 1. 项目概览\n")
    sections.append("- 项目名称：{}".format(repo_name))
    sections.append("- 项目路径：{}".format(repo_path))

    # File tree summary
    if file_tree:
        files = file_tree.get("files", [])
        dirs = file_tree.get("directories", [])
        total_files = len(files) if isinstance(files, list) else 0
        total_dirs = len(dirs) if isinstance(dirs, list) else 0
        sections.append("- 文件树：{} 个文件，{} 个目录".format(total_files, total_dirs))

    # 2. Tech Stack (LLM inference vs script evidence)
    sections.append("\n## 2. 技术栈分析\n")
    if analysis_enabled and stack_analysis:
        primary = stack_analysis.get("primary", {})
        if isinstance(primary, dict):
            p_name = primary.get("name", "unknown")
            p_conf = primary.get("confidence", "unknown")
            sections.append("- **主要技术栈（LLM 推断）**：{}（置信度：{}）".format(p_name, p_conf))
        secondary = stack_analysis.get("secondary", [])
        for sec in secondary:
            if isinstance(sec, dict):
                sec_name = sec.get("name", "unknown")
                sec_conf = sec.get("confidence", "unknown")
                sections.append("- 次要技术栈（LLM 推断）：{}（置信度：{}）".format(sec_name, sec_conf))
    else:
        sections.append("- LLM 分析未启用，技术栈由脚本检测推断")

    # Script evidence summary
    if evidence:
        sections.append("")
        sections.append("**脚本检测证据（确定性事实）**：")
        for key, val in evidence.items():
            if isinstance(val, dict) and val.get("detected"):
                summary_parts = []
                for k in ("buildTool", "framework", "packageManager"):
                    if k in val:
                        summary_parts.append("{}={}".format(k, val[k]))
                detail = "（{}）".format(", ".join(summary_parts)) if summary_parts else ""
                sections.append("  - ✅ {}{}".format(key, detail))

    # 3. Module responsibilities
    if module_analysis:
        sections.append("\n## 3. 模块职责（LLM 推断）\n")
        for mod in module_analysis:
            if isinstance(mod, dict):
                module_name = mod.get("module", "unknown")
                role = mod.get("guessedRole", "unknown")
                conf = mod.get("confidence", "unknown")
                sections.append("- **{}**：{}（置信度：{}）".format(module_name, role, conf))

    # 4. Architecture pattern
    if arch_pattern:
        sections.append("\n## 4. 架构模式（LLM 推断）\n")
        sections.append("- {}".format(arch_pattern))

    # 5. Command catalog
    sections.append("\n## 5. 命令候选\n")
    all_cmd_lists = [
        ("build", build_cmds),
        ("test", test_cmds),
        ("frontend", frontend_cmds),
        ("run", run_cmds),
        ("docker", docker_cmds),
    ]
    for label, cmd_list in all_cmd_lists:
        sections.append("- {} 命令数：{}".format(label, len(cmd_list)))

    # Detail commands with confidence
    has_cmds = any(c for _, c in all_cmd_lists)
    if has_cmds:
        sections.append("")
        sections.append("**命令详情**：")
        for label, cmd_list in all_cmd_lists:
            for cmd in cmd_list:
                if isinstance(cmd, dict):
                    cmd_str = cmd.get("command", cmd.get("name", "unknown"))
                    conf = cmd.get("confidence", "unknown")
                    wd = cmd.get("workingDirectory", ".")
                    sections.append("  - [{}] `{}`（置信度：{}，工作目录：{}）".format(
                        label, cmd_str, conf, wd))

    # 6. Anomalies
    if anomalies:
        sections.append("\n## 6. 异常与发现（LLM 推断）\n")
        for a in anomalies:
            sections.append("- ⚠️ {}".format(a))

    # 7. Validation results
    sections.append("\n## 7. LLM vs 脚本校验\n")
    validation_summary = validation.get("summary", "") if isinstance(validation, dict) else ""
    points = validation.get("points", []) if isinstance(validation, dict) else []
    if points:
        sections.append("校验摘要：{}".format(validation_summary))
        sections.append("")
        for pt in points:
            if isinstance(pt, dict):
                pt_type = pt.get("type", "unknown")
                pt_stack = pt.get("stack", "")
                pt_claim = pt.get("llmClaim", "")
                pt_evidence = pt.get("scriptEvidence", "")
                pt_resolution = pt.get("resolution", "")
                sections.append("- **{}**（{}）：LLM 声明「{}」，脚本结果「{}」→ {}".format(
                    pt_type, pt_stack, pt_claim, pt_evidence, pt_resolution))
    elif validation_summary:
        sections.append("校验摘要：{}".format(validation_summary))
    else:
        sections.append("- 无校验数据（LLM 分析未启用或无冲突）")

    # 8. Calibration notes
    sections.append("\n## 8. 人工校准点\n")
    sections.append("- 请确认命令候选是否符合当前本地环境。")
    sections.append("- 请确认 Scanner 识别的模块是否符合项目真实边界。")
    if analysis_enabled:
        sections.append("- LLM 推断内容标记为「LLM 推断」，请与确定性脚本证据交叉验证。")

    return "\n".join(sections) + "\n"
