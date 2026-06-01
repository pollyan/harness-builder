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
                "maturity_dimensions": ["guides"],
                "maturity_impact_summary": "补齐 Guides 上下文。",
                "next_stage_contribution": "把 LLM 发现的上下文候选留给 Maintainer 审查，后续可补齐项目 Guide 基线。",
                "review_boundary": "review_only_no_formal_asset_change",
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
                "maturity_dimensions": ["sensors", "verification_sophistication"],
                "maturity_impact_summary": "补齐 Sensors 验证、Verification 验证成熟度。",
                "next_stage_contribution": "把待确认验证命令或验证活动留在人工审查队列，避免直接提升 hard gate。",
                "review_boundary": "review_only_no_formal_asset_change",
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
    for name in [
        "project-experience.md",
        "repair-patterns.md",
        "sensor-feedback.md",
        "team-preferences.md",
        "deprecated-experience.md",
        "experience-index.yaml",
    ]:
        assert (ai / "experience" / name).exists()
    assert weapon_candidates.exists()
    assert llm_review.exists()
    assert (ai / "review" / "candidate-guides.md").exists()
    assert (ai / "review" / "candidate-sensors.md").exists()

    report = yaml.safe_load(weapon_candidates.read_text(encoding="utf-8"))
    assert all(item["human_confirmation_required"] is True for item in report["candidates"])
    by_id = {item["id"]: item for item in report["candidates"]}
    assert by_id["llm-guide-architecture-001"]["maturity_dimensions"] == ["guides"]
    assert by_id["llm-guide-architecture-001"]["maturity_impact_summary"] == "补齐 Guides 上下文。"
    assert by_id["llm-sensor-command-001"]["maturity_dimensions"] == ["sensors", "verification_sophistication"]
    assert by_id["llm-sensor-command-001"]["review_boundary"] == "review_only_no_formal_asset_change"
    review_markdown = llm_review.read_text(encoding="utf-8")
    assert "LLM Enhancement Candidates" in review_markdown
    assert "maturity=`补齐 Guides 上下文。`" in review_markdown
    assert "next=`把 LLM 发现的上下文候选留给 Maintainer 审查，后续可补齐项目 Guide 基线。`" in review_markdown
    assert "boundary=`review_only_no_formal_asset_change`" in review_markdown
    index = yaml.safe_load((ai / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert index["schema_version"] == "1.0"
    assert index["pending_improvement_count"] == 0

    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert {"path": ".ai/experience/weapon-library-candidates.yaml", "kind": "weapon_library_candidates"} in artifacts["artifacts"]
    assert {"path": ".ai/experience/experience-index.yaml", "kind": "experience_index"} in artifacts["artifacts"]
    assert {"path": ".ai/review/candidate-sensors.md", "kind": "review"} in artifacts["artifacts"]


def test_write_candidate_assets_preserves_existing_experience_markdown(tmp_path: Path):
    ai = tmp_path / ".ai"
    experience = ai / "experience"
    experience.mkdir(parents=True)
    edited_project_experience = "# Project Experience\n\n## Recorded Experience\n\nTeam-edited notes.\n"
    edited_pending = "# Pending Improvements\n\n- keep this customer edit\n"
    (experience / "project-experience.md").write_text(edited_project_experience, encoding="utf-8")
    (experience / "pending-improvements.md").write_text(edited_pending, encoding="utf-8")

    write_candidate_assets(ai, _enhancement_candidates())

    assert (experience / "project-experience.md").read_text(encoding="utf-8") == edited_project_experience
    assert (experience / "pending-improvements.md").read_text(encoding="utf-8") == edited_pending
    index = yaml.safe_load((experience / "experience-index.yaml").read_text(encoding="utf-8"))
    assert index["experience_files"]["project-experience.md"] is True
    assert index["pending_improvement_count"] == 1
