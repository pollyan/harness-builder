from pathlib import Path

from harness_builder.scanner.detectors.shallow_code import detect_shallow_code_structure


def test_detect_shallow_java_and_dotnet_code_roles():
    java_repo = Path("tests/fixtures/minimal-java-maven")
    dotnet_repo = Path("tests/fixtures/minimal-dotnet")

    java_result = detect_shallow_code_structure(java_repo)
    dotnet_result = detect_shallow_code_structure(dotnet_repo)

    assert "app/src/main/java/com/example/UserController.java" in java_result["controllers"]
    assert "app/src/main/java/com/example/UserService.java" in java_result["services"]
    assert "src/Web/Controllers/CatalogController.cs" in dotnet_result["controllers"]
