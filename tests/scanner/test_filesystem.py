from pathlib import Path

from harness_builder.scanner.detectors.filesystem import scan_filesystem


def test_scan_filesystem_detects_top_level_and_counts():
    repo = Path("tests/fixtures/minimal-java-maven")

    result = scan_filesystem(repo)

    assert result["topLevelDirectories"] == ["app", "frontend", "sql", "src"]
    assert "README.md" in result["keyFiles"]
    assert "pom.xml" in result["keyFiles"]
    assert result["fileCounts"]["total"] >= 3
    assert result["fileCounts"]["byExtension"][".java"] >= 1
