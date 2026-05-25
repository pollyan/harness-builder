from harness_builder.scanner.report import render_scanner_report


# ── Existing tests (unchanged) ────────────────────────────────────────

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


# ── v2 report enhancement tests ───────────────────────────────────────


def _make_inventory(**overrides):
    """Build a v2 inventory dict with sensible defaults."""
    inv = {
        "repo": {"name": "test-project", "path": "/tmp/test-project"},
        "fileTree": {"files": [{"path": "pom.xml", "name": "pom.xml"}]},
        "analysis": {
            "enabled": True,
            "stackAnalysis": {
                "primary": {"name": "Java / Maven", "confidence": "high", "evidence": ["pom.xml"]},
                "secondary": [],
            },
            "moduleAnalysis": [
                {"module": "src/main", "guessedRole": "Application", "confidence": "high", "evidence": []},
            ],
            "commandCandidates": [
                {"category": "build", "command": "mvn clean package", "confidence": "high", "evidence": []},
            ],
            "architecturePattern": "monolith",
            "anomalies": ["Mixed build systems detected"],
            "calibrationPoints": [],
        },
        "evidence": {
            "java": {"detected": True, "buildTool": "maven"},
        },
        "validation": {
            "points": [],
            "summary": "all confirmed",
        },
    }
    inv.update(overrides)
    return inv


def _make_commands():
    return {
        "commands": {
            "build": [{"name": "b1", "command": "mvn clean package", "confidence": "high", "verified": False}],
            "test": [],
            "frontend": [],
            "run": [],
            "docker": [],
        }
    }


def test_report_shows_tech_stack_when_analysis_enabled():
    """When LLM analysis is enabled, tech stack must appear in report."""
    report = render_scanner_report(_make_inventory(), _make_commands())
    assert "Java / Maven" in report
    assert "技术栈" in report


def test_report_shows_module_responsibilities():
    """Module analysis from LLM should be rendered."""
    report = render_scanner_report(_make_inventory(), _make_commands())
    assert "src/main" in report
    assert "Application" in report


def test_report_shows_architecture_pattern():
    """Architecture pattern from LLM should be visible."""
    report = render_scanner_report(_make_inventory(), _make_commands())
    assert "monolith" in report
    assert "架构" in report


def test_report_shows_anomalies():
    """Anomalies from LLM analysis should be displayed."""
    report = render_scanner_report(_make_inventory(), _make_commands())
    assert "Mixed build systems detected" in report


def test_report_distinguishes_facts_from_inference():
    """Report must clearly label deterministic evidence vs LLM inference."""
    report = render_scanner_report(_make_inventory(), _make_commands())
    # Evidence (script) section
    assert "确定性证据" in report or "脚本检测" in report or "证据" in report
    # Analysis (LLM) section
    assert "LLM" in report or "推断" in report or "分析" in report


def test_report_shows_validation_results():
    """Validation summary must appear in report."""
    report = render_scanner_report(_make_inventory(), _make_commands())
    assert "校验" in report or "validation" in report.lower()
    assert "all confirmed" in report


def test_report_shows_validation_mismatch():
    """When LLM and scripts disagree, mismatch must be shown."""
    inv = _make_inventory()
    inv["validation"] = {
        "points": [
            {
                "type": "stack-mismatch",
                "stack": "dotnet",
                "llmClaim": ".NET detected",
                "scriptEvidence": "not detected",
                "resolution": "calibration",
            }
        ],
        "summary": "1 calibration point(s)",
    }
    report = render_scanner_report(inv, _make_commands())
    assert ".NET detected" in report
    assert "calibration" in report.lower() or "校准" in report


def test_report_no_crash_when_analysis_disabled():
    """When analysis is disabled (no LLM), report must still render."""
    inv = _make_inventory(analysis={"enabled": False})
    report = render_scanner_report(inv, _make_commands())
    assert "# Scanner Report" in report
    assert "test-project" in report


def test_report_no_crash_when_fields_missing():
    """Report must not crash if optional v2 fields are absent."""
    inv = {"repo": {"name": "minimal", "path": "/tmp/min"}}
    commands = {"commands": {"build": []}}
    report = render_scanner_report(inv, commands)
    assert "# Scanner Report" in report
    assert "minimal" in report


def test_report_shows_evidence_section():
    """Evidence from script detectors must be visible."""
    report = render_scanner_report(_make_inventory(), _make_commands())
    assert "maven" in report.lower()


def test_report_shows_command_catalog_summary():
    """Command catalog entries must remain visible in enhanced report."""
    report = render_scanner_report(_make_inventory(), _make_commands())
    assert "mvn clean package" in report


def test_report_shows_command_confidence():
    """Command confidence level should be visible."""
    report = render_scanner_report(_make_inventory(), _make_commands())
    assert "high" in report


def test_report_shows_file_tree_summary():
    """File tree should have a summary section."""
    report = render_scanner_report(_make_inventory(), _make_commands())
    assert "文件" in report or "File" in report
