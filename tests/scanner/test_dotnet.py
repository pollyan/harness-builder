from pathlib import Path

from harness_builder.scanner.detectors.dotnet import detect_dotnet, _project_references


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


def test_detect_dotnet_no_sln_no_csproj(tmp_path):
    """Empty directory → detected=False."""
    result = detect_dotnet(tmp_path)

    assert result["detected"] is False
    assert result["solutions"] == []
    assert result["projects"] == []
    assert result["testProjects"] == []
    assert result["globalJson"] is None


def test_detect_dotnet_csproj_only_no_sln(tmp_path):
    """A .csproj without .sln should still be detected."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.csproj").write_text("<Project />")

    result = detect_dotnet(tmp_path)

    assert result["detected"] is True
    assert len(result["projects"]) == 1


def test_detect_dotnet_test_detection_by_name(tmp_path):
    """Files ending with Tests.csproj should be classified as test projects."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "MyApp.Tests.csproj").write_text("<Project />")

    result = detect_dotnet(tmp_path)

    assert len(result["testProjects"]) == 1
    assert result["projects"][0]["isTest"] is True


def test_detect_dotnet_test_detection_by_path(tmp_path):
    """Files in a 'test' directory should be classified as test projects."""
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "Integration.csproj").write_text("<Project />")

    result = detect_dotnet(tmp_path)

    assert len(result["testProjects"]) == 1
    assert result["projects"][0]["isTest"] is True


def test_detect_dotnet_no_global_json(tmp_path):
    """Missing global.json should return None."""
    (tmp_path / "App.sln").write_text("")

    result = detect_dotnet(tmp_path)

    assert result["globalJson"] is None


def test_project_references_with_include(tmp_path):
    """Should resolve ProjectReference Include paths."""
    repo = tmp_path
    (repo / "src").mkdir()
    core_csproj = repo / "src" / "Core.csproj"
    core_csproj.write_text("<Project />")
    web_csproj = repo / "src" / "Web.csproj"
    web_csproj.write_text(
        '<Project><ItemGroup><ProjectReference Include="Core.csproj" /></ItemGroup></Project>'
    )

    refs = _project_references(web_csproj, repo)
    assert len(refs) == 1
    assert refs[0].endswith("Core.csproj")


def test_project_references_invalid_xml(tmp_path):
    """Malformed csproj should return empty list, not crash."""
    bad = tmp_path / "bad.csproj"
    bad.write_text("<not-closed")

    assert _project_references(bad, tmp_path) == []


def test_project_references_no_references(tmp_path):
    """A csproj with no ItemGroup should return empty list."""
    csproj = tmp_path / "plain.csproj"
    csproj.write_text("<Project><PropertyGroup><TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>")

    assert _project_references(csproj, tmp_path) == []
