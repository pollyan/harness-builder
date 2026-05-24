from pathlib import Path

from harness_builder.scanner.detectors.java_maven import detect_java_maven


def test_detect_java_maven_modules_and_assets():
    repo = Path("tests/fixtures/minimal-java-maven")

    result = detect_java_maven(repo)

    assert result["detected"] is True
    assert result["buildFiles"] == ["pom.xml", "app/pom.xml"]
    assert result["mavenModules"] == [{"name": "app", "path": "app"}]
    assert "app/src/main/resources/application.yml" in result["springConfigFiles"]
    assert "sql/schema.sql" in result["sqlAssets"]
