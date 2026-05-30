from pathlib import Path

from harness_builder.scanner.detectors.node_frontend import detect_node_frontend


def test_detect_node_frontend_scripts_and_vue_files():
    repo = Path("tests/fixtures/minimal-java-maven")

    result = detect_node_frontend(repo)

    assert result["detected"] is True
    assert result["projects"][0]["path"] == "frontend"
    assert result["projects"][0]["scripts"]["build"] == "vite build"
    assert result["projects"][0]["vueFileCount"] == 1


def test_detect_node_frontend_no_package_json(tmp_path):
    """No package.json → detected=False."""
    result = detect_node_frontend(tmp_path)

    assert result["detected"] is False
    assert result["projects"] == []


def test_detect_node_frontend_invalid_json(tmp_path):
    """A malformed package.json should be skipped, not crash."""
    (tmp_path / "package.json").write_text("{invalid json!!!")

    result = detect_node_frontend(tmp_path)

    assert result["detected"] is False
    assert result["projects"] == []


def test_detect_node_frontend_empty_scripts(tmp_path):
    """package.json with no scripts should still be detected."""
    (tmp_path / "package.json").write_text('{"name": "bare"}')

    result = detect_node_frontend(tmp_path)

    assert result["detected"] is True
    assert result["projects"][0]["scripts"] == {}


def test_detect_node_frontend_dev_dependencies(tmp_path):
    """devDependencies should be extracted and sorted."""
    (tmp_path / "package.json").write_text(
        '{"devDependencies": {"eslint": "^8.0", "prettier": "^3.0"}, "dependencies": {"lodash": "^4.0"}}'
    )

    result = detect_node_frontend(tmp_path)

    assert result["projects"][0]["dependencies"] == ["lodash"]
    assert result["projects"][0]["devDependencies"] == ["eslint", "prettier"]


def test_detect_node_frontend_ignores_node_modules(tmp_path):
    """package.json inside node_modules should be ignored."""
    nm = tmp_path / "node_modules" / "some-pkg"
    nm.mkdir(parents=True)
    (nm / "package.json").write_text('{"name": "some-pkg"}')

    result = detect_node_frontend(tmp_path)

    assert result["detected"] is False


def test_detect_node_frontend_no_vue_files(tmp_path):
    """A pure Node project without Vue files should have vueFileCount=0."""
    (tmp_path / "package.json").write_text('{"scripts": {"start": "node index.js"}}')

    result = detect_node_frontend(tmp_path)

    assert result["detected"] is True
    assert result["projects"][0]["vueFileCount"] == 0


def test_detect_node_frontend_multiple_projects(tmp_path):
    """Multiple package.json files should produce multiple projects."""
    (tmp_path / "package.json").write_text('{"name": "root"}')
    sub = tmp_path / "packages" / "lib"
    sub.mkdir(parents=True)
    (sub / "package.json").write_text('{"name": "lib"}')

    result = detect_node_frontend(tmp_path)

    assert result["detected"] is True
    assert len(result["projects"]) == 2


def test_detect_node_frontend_root_project_path_is_dot(tmp_path):
    """A package.json at the repo root should have path '.'."""
    (tmp_path / "package.json").write_text('{"name": "root"}')

    result = detect_node_frontend(tmp_path)

    assert result["projects"][0]["path"] == "."
