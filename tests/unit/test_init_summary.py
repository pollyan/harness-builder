from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.init_summary import build_init_summary_markdown, render_init_completion_message


def _score() -> MaturityReport:
    return MaturityReport(
        overall_level="L2",
        target_next_level="L3",
        dimension_scores={"Sensors": "L2"},
        blocking_reasons=["缺少真实 benchmark 质量验收。"],
        recommended_next_steps=["运行 benchmark 验证第一版 Harness。"],
    )


def test_init_summary_reports_existing_benchmark_status(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "maturity-score.yaml").write_text(yaml.safe_dump(_score().model_dump(mode="json")), encoding="utf-8")
    (ai / "benchmark-report.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "profile": "java-spring",
                "status": "failed",
                "quality_status": "degraded",
                "checks": [
                    {"id": "schema:project-inventory", "passed": True},
                    {"id": "content:guides-quality", "passed": False},
                ],
                "quality_scores": {},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    markdown = build_init_summary_markdown(_score(), ai=ai)
    message = render_init_completion_message(ai)

    assert "## Benchmark 健康度" in markdown
    assert "benchmark_status=failed" in markdown
    assert "quality_status=degraded" in markdown
    assert "failed_checks=1" in markdown
    assert ".ai/benchmark-report.yaml" in markdown
    assert "Benchmark 健康度" in message
    assert "benchmark_status=failed" in message
    assert "quality_status=degraded" in message
    assert "failed_checks=1" in message
