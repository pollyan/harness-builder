from pathlib import Path

from harness_builder.scanner.models import ScanContext


def test_scan_context_defaults():
    ctx = ScanContext(repo_root=Path("/tmp"), out_dir=Path("/tmp/out"))
    assert ctx.inventory == {}
    assert ctx.commands == {}
    assert ctx.repo_root == Path("/tmp")
    assert ctx.out_dir == Path("/tmp/out")


def test_scan_context_with_data():
    ctx = ScanContext(
        repo_root=Path("/tmp"),
        out_dir=Path("/tmp/out"),
        inventory={"a": 1},
        commands={"b": 2},
    )
    assert ctx.inventory == {"a": 1}
    assert ctx.commands == {"b": 2}


def test_scan_context_instances_are_independent():
    """Ensure mutable defaults don't leak between instances."""
    ctx1 = ScanContext(repo_root=Path("/a"), out_dir=Path("/b"))
    ctx1.inventory["x"] = 1
    ctx2 = ScanContext(repo_root=Path("/c"), out_dir=Path("/d"))
    assert "x" not in ctx2.inventory
