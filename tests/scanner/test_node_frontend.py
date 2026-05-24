from pathlib import Path

from harness_builder.scanner.detectors.node_frontend import detect_node_frontend


def test_detect_node_frontend_scripts_and_vue_files():
    repo = Path("tests/fixtures/minimal-java-maven")

    result = detect_node_frontend(repo)

    assert result["detected"] is True
    assert result["projects"][0]["path"] == "frontend"
    assert result["projects"][0]["scripts"]["build"] == "vite build"
    assert result["projects"][0]["vueFileCount"] == 1
