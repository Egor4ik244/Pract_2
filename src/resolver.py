from .dependencies import parse_dependency_group
from .versions import compare_versions, satisfies_version


class DependencyResolver:
    """Выбирает пакеты и версии для обхода зависимостей."""

    def __init__(self, repository):
        self._repository = repository

    def resolve_group(self, group):
        """Выбирает первую доступную альтернативу."""
        alternatives = parse_dependency_group(group)

        for package, operator, required in alternatives:
            version = self._select_version(
                package,
                operator,
                required
            )

            if version is not None:
                return package, version

        raise ValueError(
            f"В индексе нет подходящей зависимости: {group}"
        )

    def _select_version(self, package, operator, required):
        """Находит наибольшую подходящую версию пакета."""
        selected = None

        for version in self._repository.get_versions(package):
            if operator is not None:
                if not satisfies_version(
                    version,
                    operator,
                    required
                ):
                    continue

            if selected is None:
                selected = version
            elif compare_versions(version, selected) > 0:
                selected = version

        return selected

    def get_dependencies(self, node):
        """Возвращает зависимости вершины с учётом версий."""
        package, version = node
        groups = self._repository.get_dependencies(
            package,
            version
        )

        dependencies = []

        for group in groups:
            dependency = self.resolve_group(group)

            if dependency not in dependencies:
                dependencies.append(dependency)

        return dependencies
    