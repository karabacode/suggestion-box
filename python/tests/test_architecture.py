import ast
from pathlib import Path
import unittest


APP_ROOT = Path(__file__).parents[1] / "app"

def imported_module_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


class ArchitectureTests(unittest.TestCase):
    def test_domain_and_ports_do_not_depend_on_frameworks_or_adapters(self) -> None:
        violations: list[str] = []
        protected_roots = (APP_ROOT / "domain", APP_ROOT / "application" / "ports")
        forbidden_prefixes = ("app.infrastructure", "app.presentation", "fastapi", "google")
        for root in protected_roots:
            for path in root.rglob("*.py"):
                for imported in imported_module_names(path):
                    if any(
                        imported == prefix or imported.startswith(f"{prefix}.")
                        for prefix in forbidden_prefixes
                    ):
                        violations.append(f"{path}: {imported}")

        self.assertEqual([], violations, "Architecture violations:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
