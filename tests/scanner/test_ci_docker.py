from pathlib import Path

from harness_builder.scanner.detectors.ci_docker import detect_ci_docker


def test_detect_ci_and_docker_assets():
    repo = Path("tests/fixtures/minimal-dotnet")

    result = detect_ci_docker(repo)

    assert result["githubActions"] == [".github/workflows/dotnetcore.yml"]
    assert result["dockerComposeFiles"] == ["docker-compose.yml"]
