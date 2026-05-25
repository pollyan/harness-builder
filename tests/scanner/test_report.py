from harness_builder.scanner.report import render_scanner_report


def test_render_report_basic():
    inventory = {"repo": {"name": "my-project", "path": "/tmp/my-project"}}
    commands = {"commands": {"build": [{"name": "b1"}], "test": [], "frontend": []}}
    report = render_scanner_report(inventory, commands)

    assert "# Scanner Report — my-project" in report
    assert "my-project" in report
    assert "/tmp/my-project" in report
    assert "build 命令数：1" in report
    assert "test 命令数：0" in report
    assert "frontend 命令数：0" in report
    assert "人工校准点" in report


def test_render_report_empty_commands():
    inventory = {"repo": {"name": "empty", "path": "/dev/null"}}
    commands = {"commands": {}}
    report = render_scanner_report(inventory, commands)

    assert "build 命令数：0" in report
    assert "test 命令数：0" in report
    assert "frontend 命令数：0" in report


def test_render_report_multiple_commands():
    inventory = {"repo": {"name": "big", "path": "/big"}}
    commands = {
        "commands": {
            "build": [{"name": "b1"}, {"name": "b2"}],
            "test": [{"name": "t1"}],
            "frontend": [{"name": "f1"}, {"name": "f2"}, {"name": "f3"}],
        }
    }
    report = render_scanner_report(inventory, commands)

    assert "build 命令数：2" in report
    assert "test 命令数：1" in report
    assert "frontend 命令数：3" in report
