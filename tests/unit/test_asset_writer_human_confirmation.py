from pathlib import Path

import yaml

from harness_builder_agent.tools.asset_writers.human_confirmation import write_human_confirmation_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace


def test_write_human_confirmation_assets_writes_context_questionnaire_and_markdown(tmp_path: Path):
    ai = tmp_path / ".ai"
    context_inputs = {
        "schema_version": "1.0",
        "contexts": [
            {
                "path": "team-rules.md",
                "size_bytes": 36,
                "summary": "团队规则：必须分层。",
                "truncated": False,
            }
        ],
    }
    questionnaire = {
        "schema_version": "1.0",
        "questions": [
            {
                "interaction_type": "candidate_asset_confirmation",
                "interaction_id": "confirm:architecture",
                "question": "架构是否分层？",
                "options": ["保持 candidate", "人工确认后提升为 confirmed"],
                "confidence": "medium",
                "reason": "扫描需要确认。",
            }
        ],
    }
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    write_human_confirmation_assets(ai, context_inputs, questionnaire, trace)
    trace.finish("completed", {})

    assert yaml.safe_load((ai / "context-inputs.yaml").read_text(encoding="utf-8")) == context_inputs
    assert yaml.safe_load((ai / "questionnaire.yaml").read_text(encoding="utf-8")) == questionnaire
    markdown = (ai / "human-input-needed.md").read_text(encoding="utf-8")
    assert "团队规则" in markdown
    assert "架构是否分层" in markdown
    artifacts = yaml.safe_load(
        (ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8")
    )
    assert {"path": ".ai/context-inputs.yaml", "kind": "context_inputs"} in artifacts["artifacts"]
    assert {"path": ".ai/questionnaire.yaml", "kind": "questionnaire"} in artifacts["artifacts"]
    assert {"path": ".ai/human-input-needed.md", "kind": "human_confirmation"} in artifacts["artifacts"]
