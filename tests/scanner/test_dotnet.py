from pathlib import Path

from harness_builder.scanner.detectors.dotnet import detect_dotnet


def test_detect_dotnet_solution_projects_and_tests():
    repo = Path("tests/fixtures/minimal-dotnet")

    result = detect_dotnet(repo)

    assert result["detected"] is True
    assert result["solutions"] == ["Demo.sln"]
    project_paths = [p["path"] for p in result["projects"]]
    assert "src/Web/Web.csproj" in project_paths
    assert "src/ApplicationCore/ApplicationCore.csproj" in project_paths
    assert result["testProjects"] == ["tests/UnitTests/UnitTests.csproj"]
    assert result["globalJson"] == "global.json"
