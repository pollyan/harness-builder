from pathlib import Path

import yaml

from harness_builder_agent.tools.asset_writers.candidates import write_candidate_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace


def _enhancement_candidates() -> dict:
    return {
        "schema_version": "1.0",
        "source": "llm_scan_proposal",
        "candidates": [
            {
                "id": "llm-guide-architecture-001",
                "candidate_type": "guide",
                "status": "candidate",
                "title": "架构信号候选规则",
                "rationale": "Controller layer is present",
                "evidence": ["Controller layer is present"],
                "source": "llm_scan_proposal",
                "human_confirmation_required": True,
            },
            {
                "id": "llm-sensor-command-001",
                "candidate_type": "sensor",
                "status": "candidate",
                "title": "验证命令候选：unit_test",
                "rationale": "该命令已进入 CommandCatalog，建议人工确认是否保留或提升 gate。",
                "evidence": ["mvn test", "pom.xml"],
                "source": "llm_scan_proposal",
                "human_confirmation_required": True,
            },
        ],
    }


def test_write_candidate_assets_writes_experience_review_files_and_records_artifacts(tmp_path: Path):
    ai = tmp_path / ".ai"
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    write_candidate_assets(ai, _enhancement_candidates(), trace=trace)
    trace.finish("completed", {})

    weapon_candidates = ai / "experience" / "weapon-library-candidates.yaml"
    llm_review = ai / "review" / "llm-enhancement-candidates.md"
    assert (ai / "experience" / "pending-improvements.md").exists()
    assert weapon_candidates.exists()
    assert llm_review.exists()
    assert (ai / "review" / "candidate-guides.md").exists()
    assert (ai / "review" / "candidate-sensors.md").exists()

    report = yaml.safe_load(weapon_candidates.read_text(encoding="utf-8"))
    assert all(item["human_confirmation_required"] is True for item in report["candidates"])
    assert "LLM Enhancement Candidates" in llm_review.read_text(encoding="utf-8")

    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert {"path": ".ai/experience/weapon-library-candidates.yaml", "kind": "weapon_library_candidates"} in artifacts["artifacts"]
    assert {"path": ".ai/review/candidate-sensors.md", "kind": "review"} in artifacts["artifacts"]
