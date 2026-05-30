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


def test_detect_shallow_empty_repo(tmp_path):
    """Empty repo → all empty lists."""
    result = detect_shallow_code_structure(tmp_path)

    assert result["controllers"] == []
    assert result["services"] == []
    assert result["entitiesOrModels"] == []
    assert result["tests"] == []
    assert result["frontendComponents"] == []


def test_detect_shallow_controller_by_directory(tmp_path):
    """Files in a 'controllers/' directory should be detected even without controller suffix."""
    ctrl_dir = tmp_path / "src" / "controllers"
    ctrl_dir.mkdir(parents=True)
    (ctrl_dir / "home.py").write_text("pass")

    result = detect_shallow_code_structure(tmp_path)

    assert len(result["controllers"]) == 1


def test_detect_shallow_service_by_suffix(tmp_path):
    """Files ending with Service.java should be detected."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "OrderService.java").write_text("class OrderService {}")

    result = detect_shallow_code_structure(tmp_path)

    assert "src/OrderService.java" in result["services"]


def test_detect_shallow_entity_by_suffix(tmp_path):
    """Files ending with Entity.java or Model.cs should be detected."""
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "User.java").write_text("class User {}")
    (tmp_path / "models" / "Order.cs").write_text("class Order {}")

    result = detect_shallow_code_structure(tmp_path)

    assert len(result["entitiesOrModels"]) == 2


def test_detect_shallow_test_files(tmp_path):
    """Test files should be detected by path containing 'test' and correct extension."""
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "UserServiceTest.java").write_text("class T {}")
    (test_dir / "calc.spec.ts").write_text("// test")

    result = detect_shallow_code_structure(tmp_path)

    assert len(result["tests"]) >= 1


def test_detect_shallow_frontend_components(tmp_path):
    """.vue, .tsx, .jsx files should be detected."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.vue").write_text("<template/>")
    (tmp_path / "src" / "Button.tsx").write_text("export default () => {}")
    (tmp_path / "src" / "Card.jsx").write_text("export default () => {}")

    result = detect_shallow_code_structure(tmp_path)

    assert len(result["frontendComponents"]) == 3


def test_detect_shallow_ignores_node_modules(tmp_path):
    """Files inside node_modules should be ignored."""
    nm = tmp_path / "node_modules" / "lib"
    nm.mkdir(parents=True)
    (nm / "index.tsx").write_text("export {}")

    result = detect_shallow_code_structure(tmp_path)

    assert result["frontendComponents"] == []


def test_detect_shallow_results_are_sorted(tmp_path):
    """All result lists should be sorted."""
    (tmp_path / "src").mkdir()
    for name in ["ZService.java", "AService.java", "MService.java"]:
        (tmp_path / "src" / name).write_text("class X {}")

    result = detect_shallow_code_structure(tmp_path)

    assert result["services"] == sorted(result["services"])
