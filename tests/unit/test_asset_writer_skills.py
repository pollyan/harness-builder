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
    assert lightweight.exists()
    assert bugfix.exists()
    assert "轻量级开发工作流" in lightweight.read_text(encoding="utf-8")
    assert "缺陷修复工作流" in bugfix.read_text(encoding="utf-8")

    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert {"path": ".ai/skills/lightweight/SKILL.md", "kind": "skill"} in artifacts["artifacts"]
    assert {"path": ".ai/skills/bugfix/SKILL.md", "kind": "skill"} in artifacts["artifacts"]
