import unittest

from src.fixture_repository import FixtureRepository
from src.graph import DependencyGraph


class TestDependencyGraph(unittest.TestCase):
    """Проверяет построение графа зависимостей."""

    def setUp(self):
        """Создаёт граф с ветвлением и циклом."""
        repository = FixtureRepository(
            {
                "A": ["B", "C"],
                "B": ["D"],
                "C": ["D"],
                "D": ["A"],
            }
        )
        self.builder = DependencyGraph(
            repository.get_dependencies
        )

    def test_zero_depth(self):
        """Проверяет, что глубина ноль оставляет только корень."""
        result = self.builder.build("A", 0)

        self.assertEqual(result, {"A": []})

    def test_direct_dependencies(self):
        """Проверяет ограничение одним уровнем."""
        result = self.builder.build("A", 1)

        self.assertEqual(
            result,
            {
                "A": ["B", "C"],
                "B": [],
                "C": [],
            },
        )

    def test_transitive_dependencies(self):
        """Проверяет общую транзитивную зависимость."""
        result = self.builder.build("A", 2)

        self.assertEqual(
            result,
            {
                "A": ["B", "C"],
                "B": ["D"],
                "C": ["D"],
                "D": [],
            },
        )

    def test_cycle(self):
        """Проверяет сохранение цикла без повторного обхода."""
        result = self.builder.build("A", 10)

        self.assertEqual(
            result,
            {
                "A": ["B", "C"],
                "B": ["D"],
                "C": ["D"],
                "D": ["A"],
            },
        )

    def test_self_dependency(self):
        """Проверяет зависимость пакета от самого себя."""
        repository = FixtureRepository({"A": ["A"]})
        builder = DependencyGraph(repository.get_dependencies)

        self.assertEqual(
            builder.build("A", 10),
            {"A": ["A"]},
        )

    def test_package_without_dependencies(self):
        """Проверяет пакет без зависимостей."""
        repository = FixtureRepository({"A": []})
        builder = DependencyGraph(repository.get_dependencies)

        self.assertEqual(builder.build("A", 5), {"A": []})

    def test_invalid_depth(self):
        """Проверяет отклонение неправильной глубины."""
        for depth in (-1, "2", 1.5):
            with self.subTest(depth=depth):
                with self.assertRaises(ValueError):
                    self.builder.build("A", depth)

    def test_breadth_first_order(self):
        """Проверяет порядок обхода и отсутствие повторов."""
        graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": ["A"],
        }
        calls = []

        def get_dependencies(package):
            """Запоминает порядок запросов зависимостей."""
            calls.append(package)
            return graph[package]

        builder = DependencyGraph(get_dependencies)
        builder.build("A", 10)

        self.assertEqual(calls, ["A", "B", "C", "D"])

    def test_multiletter_package(self):
        """Проверяет цикл с именем из нескольких букв."""
        graph = {
            "AB": ["C"],
            "C": ["AB"],
        }
        calls = []

        def get_dependencies(package):
            """Запоминает обращения к пакетам."""
            calls.append(package)
            return graph[package]

        builder = DependencyGraph(get_dependencies)
        result = builder.build("AB", 10)

        self.assertEqual(result, graph)
        self.assertEqual(calls, ["AB", "C"])


if __name__ == "__main__":
    unittest.main()
    