from __future__ import annotations

from pathlib import Path

from harness_builder_agent.tools.evidence_collector import collect_evidence

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_collect_evidence_captures_key_files_without_stack_decision():
    bundle = collect_evidence(FIXTURES / "minimal-java-maven")

    assert bundle.repo_name == "minimal-java-maven"
    assert bundle.detected_file_count > 0
    assert any(item.path == "pom.xml" for item in bundle.key_files)
    assert any(item.path == "frontend/package.json" for item in bundle.key_files)
    assert any(item.path == "app/src/main/resources/application.yml" for item in bundle.config_files)
    assert any(item.path == "README.md" for item in bundle.documents)
    assert "primary_stack" not in bundle.model_dump()


def test_collect_evidence_ignores_generated_and_dependency_dirs(tmp_path: Path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai" / "project-inventory.json").write_text("{}", encoding="utf-8")
    (tmp_path / "pom.xml").write_text("<project />", encoding="utf-8")

    bundle = collect_evidence(tmp_path)

    paths = {item.path for item in bundle.files}
    assert "pom.xml" in paths
    assert "node_modules/package.json" not in paths
    assert ".ai/project-inventory.json" not in paths


def test_collect_evidence_records_truncated_large_files(tmp_path: Path):
    (tmp_path / "README.md").write_text("x" * 5000, encoding="utf-8")

    bundle = collect_evidence(tmp_path, max_summary_chars=120)

    readme = next(item for item in bundle.documents if item.path == "README.md")
    assert readme.truncated is True
    assert len(readme.summary or "") == 120
    assert any(item["path"] == "README.md" for item in bundle.truncations)
