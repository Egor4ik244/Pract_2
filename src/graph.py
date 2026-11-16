class DependencyGraph:
    """Строит граф зависимостей обходом в ширину."""

    def __init__(self, get_dependencies):
        self._get_dependencies = get_dependencies

    def build(self, package, max_depth):
        """Возвращает граф с ограничением глубины."""
        if not isinstance(max_depth, int) or max_depth < 0:
            raise ValueError(
                "Глубина должна быть целым неотрицательным числом"
            )

        graph = {package: []}
        discovered = {package}

        self._visit_level(
            [package],
            0,
            max_depth,
            graph,
            discovered
        )

        return graph

    def _visit_level(
            self,
            level,
            depth,
            max_depth,
            graph,
            discovered
    ):
        """Обрабатывает уровень и переходит к следующему."""
        if not level or depth >= max_depth:
            return

        next_level = []
        for package in level:
            dependencies = self._get_dependencies(package)

            for dependency in dependencies:
                if dependency not in graph[package]:
                    graph[package].append(dependency)

                if dependency in discovered:
                    continue

                discovered.add(dependency)
                graph[dependency] = []
                next_level.append(dependency)

        self._visit_level(
            next_level,
            depth + 1,
            max_depth,
            graph,
            discovered
        )
        