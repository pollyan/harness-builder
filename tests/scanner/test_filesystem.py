from pathlib import Path

from harness_builder.scanner.detectors.filesystem import scan_filesystem, IGNORED_DIRS, KEY_FILE_NAMES


def test_scan_filesystem_detects_top_level_and_counts():
    repo = Path("tests/fixtures/minimal-java-maven")

    result = scan_filesystem(repo)

    assert "app" in result["topLevelDirectories"]
    assert "frontend" in result["topLevelDirectories"]
    assert "src" in result["topLevelDirectories"]
    assert "README.md" in result["keyFiles"]
    assert "pom.xml" in result["keyFiles"]
    assert result["fileCounts"]["total"] >= 3
    assert result["fileCounts"]["byExtension"][".java"] >= 1


def test_scan_filesystem_excludes_ignored_dirs():
    repo = Path("tests/fixtures/minimal-java-maven")

    result = scan_filesystem(repo)

    for dirname in IGNORED_DIRS:
        assert dirname not in result["topLevelDirectories"]


def test_scan_filesystem_detects_sln_and_csproj_as_key_files():
    repo = Path("tests/fixtures/minimal-dotnet")

    result = scan_filesystem(repo)

    key_names = [Path(k).name for k in result["keyFiles"]]
    assert "Demo.sln" in key_names
    assert any(k.endswith(".csproj") for k in result["keyFiles"])


def test_scan_filesystem_empty_directory(tmp_path):
    """Completely empty repo should return zeroed counts."""
    result = scan_filesystem(tmp_path)

    assert result["topLevelDirectories"] == []
    assert result["keyFiles"] == []
    assert result["fileCounts"]["total"] == 0
    assert result["fileCounts"]["byExtension"] == {}


def test_scan_filesystem_only_ignored_dirs(tmp_path):
    """A repo with only .git and node_modules should report no top-level dirs."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / ".git").joinpath("HEAD").write_text("ref: refs/heads/main")

    result = scan_filesystem(tmp_path)

    assert result["topLevelDirectories"] == []
    assert result["fileCounts"]["total"] == 0


def test_scan_filesystem_no_extension(tmp_path):
    """Files without extensions should be counted under '<none>'."""
    (tmp_path / "Makefile").write_text("all:")

    result = scan_filesystem(tmp_path)

    assert "<none>" in result["fileCounts"]["byExtension"]
    assert result["fileCounts"]["byExtension"]["<none>"] == 1


def test_scan_filesystem_key_file_names_constant():
    """Verify KEY_FILE_NAMES contains expected entries."""
    assert "pom.xml" in KEY_FILE_NAMES
    assert "package.json" in KEY_FILE_NAMES
    assert "docker-compose.yml" in KEY_FILE_NAMES
    assert "Dockerfile" in KEY_FILE_NAMES
    assert "README.md" in KEY_FILE_NAMES
