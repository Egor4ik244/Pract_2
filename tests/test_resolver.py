import unittest

from src.graph import DependencyGraph
from src.repository import UbuntuRepository
from src.resolver import DependencyResolver


INDEX = """Package: example-app
Version: 1.0
Depends: missing-lib | example-lib (>= 2.0)

Package: example-lib
Version: 1.0

Package: example-lib
Version: 2.5

Package: example-lib
Version: 2.10
Depends: example-app (= 1.0)

Package: other-lib
Version: 9.0
"""


class TestDependencyResolver(unittest.TestCase):
    """Проверяет выбор пакетов и версий зависимостей."""

    def setUp(self):
        """Создаёт репозиторий и resolver."""
        repository = UbuntuRepository(INDEX)
        self.resolver = DependencyResolver(repository)

    def test_highest_matching_version(self):
        """Проверяет выбор наибольшей подходящей версии."""
        result = self.resolver.resolve_group(
            "example-lib (>= 2.0)"
        )

        self.assertEqual(result, ("example-lib", "2.10"))

    def test_exact_version(self):
        """Проверяет точное ограничение версии."""
        result = self.resolver.resolve_group(
            "example-lib (= 2.5)"
        )

        self.assertEqual(result, ("example-lib", "2.5"))

    def test_version_without_constraint(self):
        """Проверяет выбор версии без ограничения."""
        result = self.resolver.resolve_group("example-lib")

        self.assertEqual(result, ("example-lib", "2.10"))

    def test_missing_first_alternative(self):
        """Проверяет переход к существующей альтернативе."""
        result = self.resolver.resolve_group(
            "missing-lib | example-lib"
        )

        self.assertEqual(result, ("example-lib", "2.10"))

    def test_unsuitable_first_alternative(self):
        """Проверяет переход при неподходящей версии."""
        result = self.resolver.resolve_group(
            "example-lib (>= 3.0) | other-lib"
        )

        self.assertEqual(result, ("other-lib", "9.0"))

    def test_first_available_alternative(self):
        """Проверяет приоритет порядка альтернатив."""
        result = self.resolver.resolve_group(
            "example-lib | other-lib"
        )

        self.assertEqual(result, ("example-lib", "2.10"))

    def test_unresolved_dependency(self):
        """Проверяет отсутствие подходящей зависимости."""
        with self.assertRaisesRegex(
            ValueError,
            "В индексе нет подходящей зависимости",
        ):
            self.resolver.resolve_group(
                "missing-lib | example-lib (>= 3.0)"
            )

    def test_dependencies(self):
        """Проверяет преобразование групп в вершины графа."""
        result = self.resolver.get_dependencies(
            ("example-app", "1.0")
        )

        self.assertEqual(
            result,
            [("example-lib", "2.10")],
        )

    def test_versioned_cycle(self):
        """Проверяет обход цикла с версиями."""
        builder = DependencyGraph(
            self.resolver.get_dependencies
        )

        result = builder.build(("example-app", "1.0"), 10)

        self.assertEqual(
            result,
            {
                ("example-app", "1.0"): [
                    ("example-lib", "2.10"),
                ],
                ("example-lib", "2.10"): [
                    ("example-app", "1.0"),
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()
    