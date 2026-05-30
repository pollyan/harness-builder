from pathlib import Path

import yaml

from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_json, write_text, write_yaml
from harness_builder_agent.tools.generation_trace import GenerationTrace


def test_shared_writers_create_parent_directories_and_preserve_unicode(tmp_path: Path):
    write_text(tmp_path / "nested" / "guide.md", "中文规则\n")
    write_json(tmp_path / "nested" / "payload.json", {"name": "中文"})
    write_yaml(tmp_path / "nested" / "payload.yaml", {"name": "中文"})

    assert (tmp_path / "nested" / "guide.md").read_text(encoding="utf-8") == "中文规则\n"
    assert '"中文"' in (tmp_path / "nested" / "payload.json").read_text(encoding="utf-8")
    assert yaml.safe_load((tmp_path / "nested" / "payload.yaml").read_text(encoding="utf-8")) == {"name": "中文"}


def test_record_artifact_is_noop_without_trace_and_records_relative_path(tmp_path: Path):
    record_artifact(None, tmp_path / ".ai" / "guide.md", "guide")
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    record_artifact(trace, tmp_path / ".ai" / "guide.md", "guide")
    trace.finish("completed", {})

    artifacts = yaml.safe_load(
        (tmp_path / ".ai" / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8")
    )
    assert artifacts["artifacts"] == [{"path": ".ai/guide.md", "kind": "guide"}]
