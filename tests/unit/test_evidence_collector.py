from __future__ import annotations

from pathlib import Path

from harness_builder_agent.tools.evidence_collector import collect_evidence, expand_evidence_with_requested_paths

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _write(path: Path, content: str = "content") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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


def test_collect_evidence_ignores_ai_tool_workspaces_and_keeps_root_project_manifests(tmp_path: Path):
    _write(tmp_path / "package.json", '{"scripts":{"test":"npm test"}}')
    _write(tmp_path / "pyproject.toml", "[project]\nname='demo'\n")
    _write(tmp_path / "requirements.txt", "flask\n")
    _write(tmp_path / ".claude" / "worktrees" / "feature" / "package.json", '{"private":true}')
    _write(tmp_path / ".opencode" / "package.json", '{"private":true}')
    _write(tmp_path / "deploy-package" / ".opencode" / "package.json", '{"private":true}')

    bundle = collect_evidence(tmp_path)

    indexed_paths = {item.path for item in bundle.files}
    key_paths = {item.path for item in bundle.key_files}
    priority_paths = {item.path for item in bundle.priority_files}

    assert "package.json" in indexed_paths
    assert "pyproject.toml" in indexed_paths
    assert "requirements.txt" in indexed_paths
    assert ".claude/worktrees/feature/package.json" not in indexed_paths
    assert ".opencode/package.json" not in indexed_paths
    assert "deploy-package/.opencode/package.json" not in indexed_paths

    assert {"package.json", "pyproject.toml", "requirements.txt"}.issubset(key_paths)
    assert {"package.json", "pyproject.toml", "requirements.txt"}.issubset(priority_paths)
    assert all(not path.startswith(".claude/") for path in key_paths)
    assert all("/.opencode/" not in f"/{path}" for path in key_paths)


def test_collect_evidence_records_truncated_large_files(tmp_path: Path):
    (tmp_path / "README.md").write_text("x" * 5000, encoding="utf-8")

    bundle = collect_evidence(tmp_path, max_summary_chars=120)

    readme = next(item for item in bundle.documents if item.path == "README.md")
    assert readme.truncated is True
    assert len(readme.summary or "") == 120
    assert any(item["path"] == "README.md" for item in bundle.truncations)


def test_collect_evidence_uses_stratified_sampling_for_large_messy_repo(tmp_path: Path):
    _write(tmp_path / "pom.xml", "<project><artifactId>root</artifactId></project>")
    _write(tmp_path / "src/api/UserController.java", "@RestController class UserController {}")
    _write(tmp_path / "src/security/AuthConfig.java", "class AuthConfig {}")
    _write(tmp_path / "quality/checks/UserFlowSpec.cs", "public class UserFlowSpec {}")
    _write(tmp_path / ".github/workflows/build.yml", "jobs: {}")
    _write(tmp_path / "appsettings.Production.json", "{}")
    for index in range(40):
        _write(tmp_path / "aaa" / f"Generated{index:02d}.java", f"class Generated{index:02d} {{}}")

    bundle = collect_evidence(tmp_path, max_source_samples=5)

    assert any(item.path == "pom.xml" for item in bundle.priority_files)
    assert any(item.path == "src/api/UserController.java" for item in bundle.api_entrypoints)
    assert any(item.path == "quality/checks/UserFlowSpec.cs" for item in bundle.test_files)
    assert any(item.path == "src/security/AuthConfig.java" for item in bundle.risk_files)
    assert any(item.path == ".github/workflows/build.yml" for item in bundle.ci_files)
    assert any(item.path == "appsettings.Production.json" for item in bundle.config_files)
    assert bundle.coverage is not None
    java_bucket = next(item for item in bundle.coverage.bucket_coverage if item.bucket == "source:.java")
    assert java_bucket.total_count >= 40
    assert java_bucket.skipped_count > 0
    source_warning = next(item for item in bundle.coverage.warnings if item["code"] == "source_sampling_truncated")
    assert source_warning["bucket"] == "source:.java"
    assert source_warning["total_count"] == java_bucket.total_count
    assert source_warning["selected_count"] == java_bucket.selected_count
    assert source_warning["skipped_count"] == java_bucket.skipped_count


def test_collect_evidence_marks_priority_reason_and_bucket(tmp_path: Path):
    _write(tmp_path / "src" / "Program.cs", "var builder = WebApplication.CreateBuilder(args);")
    _write(tmp_path / "tests-weird" / "CheckoutSpec.cs", "public class CheckoutSpec {}")

    bundle = collect_evidence(tmp_path)

    program = next(item for item in bundle.api_entrypoints if item.path == "src/Program.cs")
    spec = next(item for item in bundle.test_files if item.path == "tests-weird/CheckoutSpec.cs")
    assert program.priority == "critical"
    assert program.bucket == "api_entrypoint"
    assert program.reason
    assert spec.priority == "high"
    assert spec.bucket == "test"


def test_collect_evidence_keeps_full_file_index_lightweight(tmp_path: Path):
    _write(tmp_path / "pom.xml", "<project />")
    for index in range(10):
        _write(tmp_path / "src" / f"Ordinary{index}.java", "class Ordinary {}")

    bundle = collect_evidence(tmp_path, max_source_samples=2)

    ordinary_index = next(item for item in bundle.files if item.path == "src/Ordinary9.java")
    assert ordinary_index.summary is None
    assert ordinary_index.truncated is False
    selected_source = next(item for item in bundle.source_samples if item.path == "src/Ordinary0.java")
    assert selected_source.summary == "class Ordinary {}"


def test_expand_evidence_adds_llm_requested_file_skipped_by_source_sampling(tmp_path: Path):
    for index in range(8):
        _write(tmp_path / "src" / f"Ordinary{index:02d}.java", f"class Ordinary{index:02d} {{}}")
    _write(tmp_path / "src" / "zz" / "RefundRiskService.java", "class RefundRiskService { void refund() {} }")

    bundle = collect_evidence(tmp_path, max_source_samples=2)

    assert all(item.path != "src/zz/RefundRiskService.java" for item in bundle.source_samples)

    expanded = expand_evidence_with_requested_paths(
        tmp_path,
        bundle,
        ["src/zz/RefundRiskService.java"],
        max_summary_chars=80,
    )

    requested = next(item for item in expanded.llm_requested_files if item.path == "src/zz/RefundRiskService.java")
    assert requested.kind == "llm_requested"
    assert requested.bucket == "llm_requested"
    assert requested.priority == "high"
    assert requested.summary == "class RefundRiskService { void refund() {} }"
