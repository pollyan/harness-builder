import xml.etree.ElementTree as ET
from pathlib import Path

from harness_builder.scanner.detectors.java_maven import (
    detect_java_maven,
    _strip_namespace,
    _find_child_text,
    _read_modules,
)


def test_detect_java_maven_modules_and_assets():
    repo = Path("tests/fixtures/minimal-java-maven")

    result = detect_java_maven(repo)

    assert result["detected"] is True
    assert result["buildFiles"] == ["pom.xml", "app/pom.xml"]
    assert result["mavenModules"] == [{"name": "app", "path": "app"}]
    assert "app/src/main/resources/application.yml" in result["springConfigFiles"]
    assert "sql/schema.sql" in result["sqlAssets"]


def test_detect_java_maven_no_pom(tmp_path):
    """No pom.xml → detected=False, empty lists."""
    result = detect_java_maven(tmp_path)

    assert result["detected"] is False
    assert result["buildFiles"] == []
    assert result["mavenModules"] == []
    assert result["springConfigFiles"] == []
    assert result["sqlAssets"] == []


def test_detect_java_maven_spring_properties(tmp_path):
    """application.properties should also be detected."""
    (tmp_path / "pom.xml").write_text("<project/>")
    config_dir = tmp_path / "src" / "main" / "resources"
    config_dir.mkdir(parents=True)
    (config_dir / "application.properties").write_text("server.port=8080")

    result = detect_java_maven(tmp_path)

    assert result["detected"] is True
    assert any("application.properties" in f for f in result["springConfigFiles"])


def test_detect_java_maven_spring_yaml(tmp_path):
    """application.yaml (not .yml) should also be detected."""
    (tmp_path / "pom.xml").write_text("<project/>")
    config_dir = tmp_path / "src" / "main" / "resources"
    config_dir.mkdir(parents=True)
    (config_dir / "application.yaml").write_text("server:\n  port: 8080")

    result = detect_java_maven(tmp_path)

    assert any("application.yaml" in f for f in result["springConfigFiles"])


def test_detect_java_maven_multiple_sql(tmp_path):
    """Multiple SQL files should all be found and sorted."""
    (tmp_path / "pom.xml").write_text("<project/>")
    (tmp_path / "db").mkdir()
    (tmp_path / "db" / "schema.sql").write_text("create table t;")
    (tmp_path / "db" / "data.sql").write_text("insert into t;")

    result = detect_java_maven(tmp_path)

    assert len(result["sqlAssets"]) == 2


def test_detect_java_maven_pom_sorting(tmp_path):
    """POM files should be sorted by depth then lexicographically."""
    (tmp_path / "pom.xml").write_text("<project/>")
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "pom.xml").write_text("<project/>")
    shallow = tmp_path / "z"
    shallow.mkdir()
    (shallow / "pom.xml").write_text("<project/>")

    result = detect_java_maven(tmp_path)

    # "pom.xml" (depth 0) before "z/pom.xml" (depth 1) before "a/b/c/pom.xml" (depth 3)
    assert result["buildFiles"][0] == "pom.xml"
    assert result["buildFiles"][1] == "z/pom.xml"
    assert result["buildFiles"][2] == "a/b/c/pom.xml"


def test_strip_namespace_no_namespace():
    assert _strip_namespace("project") == "project"


def test_strip_namespace_with_namespace():
    assert _strip_namespace("{http://maven.apache.org/POM/4.0.0}project") == "project"


def test_find_child_text_basic():
    root = ET.fromstring("<root><module>a</module><module>b</module></root>")
    assert _find_child_text(root, "module") == ["a", "b"]


def test_find_child_text_no_match():
    root = ET.fromstring("<root><other>value</other></root>")
    assert _find_child_text(root, "module") == []


def test_find_child_text_empty_text():
    root = ET.fromstring("<root><module></module></root>")
    assert _find_child_text(root, "module") == []


def test_read_modules_invalid_xml(tmp_path):
    """Malformed XML should return empty list, not crash."""
    bad_pom = tmp_path / "pom.xml"
    bad_pom.write_text("<not-closed")

    assert _read_modules(bad_pom) == []


def test_read_modules_no_modules_element(tmp_path):
    """A pom.xml without <modules> should return empty list."""
    pom = tmp_path / "pom.xml"
    pom.write_text("<project><groupId>com.example</groupId></project>")

    assert _read_modules(pom) == []
