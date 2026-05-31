from pathlib import Path

import yaml

from harness_builder_agent.tools.asset_writers.skills import write_skill_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace


def test_write_skill_assets_copies_workflow_templates_and_records_artifacts(tmp_path: Path):
    ai = tmp_path / ".ai"
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    write_skill_assets(ai, trace=trace)
    trace.finish("completed", {})

    lightweight = ai / "skills" / "lightweight" / "SKILL.md"
    bugfix = ai / "skills" / "bugfix" / "SKILL.md"
    standard = ai / "skills" / "standard" / "SKILL.md"
    assert lightweight.exists()
    assert bugfix.exists()
    assert standard.exists()
    lightweight_text = lightweight.read_text(encoding="utf-8")
    bugfix_text = bugfix.read_text(encoding="utf-8")
    standard_text = standard.read_text(encoding="utf-8")
    assert "轻量级开发工作流" in lightweight_text
    assert "缺陷修复工作流" in bugfix_text
    assert "标准开发工作流" in standard_text
    assert "宿主 AI Coding Runtime" in lightweight_text
    assert "runtime artifact contract" in lightweight_text
    assert ".ai/task-runs/<task-id>/harness-map.yaml" in lightweight_text
    assert "Harness Builder 不负责生成这些任务运行产物" in lightweight_text
    assert "宿主 AI Coding Runtime" in bugfix_text
    assert "runtime artifact contract" in bugfix_text
    assert ".ai/task-runs/<task-id>/sensor-report.yaml" in bugfix_text
    assert "Harness Builder 不负责生成这些任务运行产物" in bugfix_text
    assert "Requirement Alignment" in standard_text
    assert "Solution Design" in standard_text
    assert "Implementation Plan" in standard_text
    assert "宿主 AI Coding Runtime" in standard_text
    assert "runtime artifact contract" in standard_text
    assert ".ai/task-runs/<task-id>/harness-map.yaml" in standard_text
    assert "Harness Builder 不负责生成这些任务运行产物" in standard_text

    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert {"path": ".ai/skills/lightweight/SKILL.md", "kind": "skill"} in artifacts["artifacts"]
    assert {"path": ".ai/skills/bugfix/SKILL.md", "kind": "skill"} in artifacts["artifacts"]
    assert {"path": ".ai/skills/standard/SKILL.md", "kind": "skill"} in artifacts["artifacts"]
