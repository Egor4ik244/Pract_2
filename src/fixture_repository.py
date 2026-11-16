import json
from pathlib import Path
import re


class FixtureRepository:
    """Хранит граф тестового репозитория."""

    def __init__(self, graph):
        self._validate(graph)
        self._graph = {
            package: dependencies.copy()
            for package, dependencies in graph.items()
        }

    @classmethod
    def from_file(cls, filename):
        """Создаёт репозиторий из JSON-файла."""
        try:
            test = Path(filename).read_text(encoding='utf-8')
            graph = json.loads(test)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(
                f"Не удалось прочитать тестовый репозиторий: {error}"
            ) from error

        return cls(graph)

    def _validate(self, graph):
        """Проверяет структуру графа."""
        if not isinstance(graph, dict):
            raise ValueError("Тестовый граф должен быть объектом JSON")

        for package, dependencies in graph.items():
            self._validate_name(package)

            if not isinstance(dependencies, list):
                raise ValueError(
                    f"Зависимости {package} должны быть списком"
                )

            for dependency in dependencies:
                self._validate_name(dependency)

                if dependency not in graph:
                    raise ValueError(
                        f"Пакет {dependency} не описан в репозитории"
                    )

    def _validate_name(self, name):
        """Проверяет имя тестового пакета."""
        if not isinstance(name, str):
            raise ValueError("Имя пакета должно быть строкой")

        if not re.fullmatch(r"[A-Z]+", name):
            raise ValueError(
                "ИМя пакета должно состоять из заглавных "
                "латинских букв" 
            )

    def get_dependencies(self, package):
        """Возвращает прямые зависимости пакета."""
        if package not in self._graph:
            raise ValueError(f"Пакет {package} не найден")

        return self._graph[package].copy()
