from pathlib import Path

from harness_builder.scanner.detectors.ci_docker import detect_ci_docker


def test_detect_ci_and_docker_assets():
    repo = Path("tests/fixtures/minimal-dotnet")

    result = detect_ci_docker(repo)

    assert result["githubActions"] == [".github/workflows/dotnetcore.yml"]
    assert result["dockerComposeFiles"] == ["docker-compose.yml"]


def test_detect_ci_docker_empty_repo(tmp_path):
    """Empty repo → all empty lists."""
    result = detect_ci_docker(tmp_path)

    assert result["githubActions"] == []
    assert result["dockerComposeFiles"] == []
    assert result["dockerfiles"] == []


def test_detect_ci_docker_yaml_workflows(tmp_path):
    """.yaml workflow files should also be detected."""
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "ci.yaml").write_text("name: ci")

    result = detect_ci_docker(tmp_path)

    assert ".github/workflows/ci.yaml" in result["githubActions"]


def test_detect_ci_docker_dockerfiles_in_subdirs(tmp_path):
    """Dockerfiles in subdirectories should be found via rglob."""
    sub = tmp_path / "src" / "api"
    sub.mkdir(parents=True)
    (sub / "Dockerfile").write_text("FROM python:3.11")

    result = detect_ci_docker(tmp_path)

    assert "src/api/Dockerfile" in result["dockerfiles"]


def test_detect_ci_docker_compose_yaml_extension(tmp_path):
    """docker-compose with .yaml extension should also be found."""
    (tmp_path / "docker-compose.override.yaml").write_text("services: {}")

    result = detect_ci_docker(tmp_path)

    assert any("docker-compose" in f and f.endswith(".yaml") for f in result["dockerComposeFiles"])


def test_detect_ci_docker_no_workflows_dir(tmp_path):
    """Missing .github/workflows directory → empty list, not crash."""
    result = detect_ci_docker(tmp_path)
    assert result["githubActions"] == []
