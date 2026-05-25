"""Tests for file_tree_collector — Task 1 of Scanner v2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness_builder.scanner.detectors.file_tree_collector import collect_file_tree


@pytest.fixture
def basic_repo(tmp_path: Path) -> Path:
    """A minimal repo with files and subdirectories."""
    (tmp_path / "README.md").write_text("# hello")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / "src" / "utils.py").write_text("x = 1")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("assert True")
    return tmp_path


def test_basic(basic_repo: Path) -> None:
    """Collects files and directories from a basic repo structure."""
    tree = collect_file_tree(basic_repo)
    # Must be JSON-serializable
    serialized = json.dumps(tree)
    assert isinstance(serialized, str)

    assert tree["root"] == basic_repo.as_posix()
    files = tree["files"]
    dirs = tree["directories"]

    file_paths = {f["path"] for f in files}
    assert "README.md" in file_paths or any("README.md" in p for p in file_paths)

    dir_paths = {d["path"] for d in dirs}
    assert any("src" in p for p in dir_paths)
    assert any("tests" in p for p in dir_paths)


def test_key_files(tmp_path: Path) -> None:
    """Key config files are included in the manifest."""
    (tmp_path / "pom.xml").write_text("<project/>")
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "Dockerfile").write_text("FROM ubuntu")
    tree = collect_file_tree(tmp_path)
    file_names = {f["name"] for f in tree["files"]}
    assert "pom.xml" in file_names
    assert "package.json" in file_names
    assert "Dockerfile" in file_names


def test_file_metadata(tmp_path: Path) -> None:
    """Each file record has path, name, extension, sizeBytes."""
    (tmp_path / "hello.py").write_text("print('hi')")
    tree = collect_file_tree(tmp_path)
    f = tree["files"][0]
    assert "path" in f
    assert "name" in f
    assert "extension" in f
    assert "sizeBytes" in f
    assert f["name"] == "hello.py"
    assert f["extension"] == ".py"
    assert f["sizeBytes"] == len("print('hi')")


def test_excludes_ignored(tmp_path: Path) -> None:
    """Excluded directories (.git, node_modules, target, etc.) are skipped."""
    (tmp_path / "README.md").write_text("ok")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")
    (tmp_path / ".git" / "objects").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "foo.js").write_text("// foo")
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "app.jar").write_text("binary")
    tree = collect_file_tree(tmp_path)
    all_paths = [f["path"] for f in tree["files"]] + [d["path"] for d in tree["directories"]]
    for p in all_paths:
        assert ".git" not in p
        assert "node_modules" not in p
        assert "target" not in p


def test_empty_repo(tmp_path: Path) -> None:
    """Empty directory returns empty files and directories."""
    tree = collect_file_tree(tmp_path)
    assert tree["files"] == []
    assert tree["directories"] == []


def test_directory_child_count(basic_repo: Path) -> None:
    """Directory records include fileCount and subdirectoryCount."""
    tree = collect_file_tree(basic_repo)
    # Find the 'src' directory record
    src_dirs = [d for d in tree["directories"] if "src" in d["path"]]
    assert len(src_dirs) >= 1
    src = src_dirs[0]
    assert src["fileCount"] == 2  # main.py, utils.py
    assert src["subdirectoryCount"] == 0


def test_posix_paths(tmp_path: Path) -> None:
    """All paths use POSIX format (forward slashes)."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x=1")
    tree = collect_file_tree(tmp_path)
    for f in tree["files"]:
        assert "\\" not in f["path"]
    for d in tree["directories"]:
        assert "\\" not in d["path"]


def test_max_depth(tmp_path: Path) -> None:
    """Respects max_depth parameter."""
    # Create: a/b/c/d/e/f/g/deep.txt (7 levels deep)
    deep = tmp_path
    for i in range(7):
        deep = deep / f"level{i}"
    deep.parent.mkdir(parents=True, exist_ok=True)
    deep.write_text("deep")

    tree = collect_file_tree(tmp_path, max_depth=3)
    all_paths = [f["path"] for f in tree["files"]]
    # The deep file at depth 7 should not appear
    assert not any("level4" in p for p in all_paths)

    # With max_depth=10 it should appear
    tree_full = collect_file_tree(tmp_path, max_depth=10)
    all_paths_full = [f["path"] for f in tree_full["files"]]
    assert any("level6" in p for p in all_paths_full)
