import argparse
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from .repository import UbuntuRepository
from .fixture_repository import FixtureRepository
from .graph import DependencyGraph
from .resolver import DependencyResolver
from .visualization import open_image, render_graph, to_ascii


class AppConfig:
    """Хранит настройки приложения."""

    def __init__(self, args):
            """Сохраняет проверенные параметры командной строки."""
            self.package = args.package
            self.repo = args.repo
            self.mode = args.mode
            self.pkg_version = args.pkg_version
            self.ascii_tree = args.ascii_tree
            self.max_depth = args.max_depth
            self.reverse = args.reverse
            self.output = args.output
            self.no_open = args.no_open
            self.no_render = args.no_render


    def print_summary(self):
        """Выводит настройки в формате ключ-значение."""
        print(f"package: {self.package}")
        print(f"repo: {self.repo}")
        print(f"mode: {self.mode}")
        print(f"pkg_version: {self.pkg_version}")
        print(f"ascii: {self.ascii_tree}")
        print(f"max-depth: {self.max_depth}")


class ConfigParser:
    """Читает и проверяет аргументы командной строки."""

    def __init__(self):
        self._parser = argparse.ArgumentParser(
            description="Визуализация зависимостей пакетов Ubuntu."
        )
        self._setup_arguments()

    def _setup_arguments(self):
        """Описывает доступные аргументы."""
        self._parser.add_argument(
            "--package",
            required=True,
            help="Имя анализируемого пакета"
        )
        self._parser.add_argument(
            "--repo",
            required=True,
            help="URL репозитория или путь к текстовому файлу"
        )
        self._parser.add_argument(
            "--mode",
            required=True,
            choices=["real", "test"],
            help="Режим работы"
        )
        self._parser.add_argument(
            "--pkg-version",
            required=True,
            help="Версия анализируемого пакета"
        )
        self._parser.add_argument(
            "--ascii",
            action="store_true",
            dest="ascii_tree",
            help="Вывести зависимости в виде ASCII-дерева."
        )
        self._parser.add_argument(
            "--max-depth",
            required=True,
            type=int,
            help="Максимальная глубина анализа"
        )
        self._parser.add_argument(
            "--reverse",
            action="store_true",
            help="Вывести обратные зависимости тестового пакета"
        )
        self._parser.add_argument(
            "--output",
            default="output/dependencies",
            help="Путь результата без расширения",
        )
        self._parser.add_argument(
            "--no-open",
            action="store_true",
            help="Не открывать созданное изображение"
        )
        self._parser.add_argument(
            "--no-render",
            action="store_true",
            help="Вывести граф только в текстовом виде"
        )

    def parse(self):
        """Читает аргументы и создает объект настроек."""
        args = self._parser.parse_args()
        self._validate(args)

        return AppConfig(args)

    def _validate(self, args):
        """Проверяет значения аргументов."""
        self._validate_package(args.package, args.mode)
        self._validate_repo(args.repo, args.mode)

        if not args.pkg_version.strip():
            raise ValueError("Версия пакета не может быть пустой")

        if any(char.isspace() for char in args.pkg_version):
            raise ValueError("Версия пакета не должна содержать пробелы")

        if args.max_depth < 0:
            raise ValueError("Глубина не может быть отрицательной")

        if args.reverse and args.mode != "test":
            raise ValueError(
                "Обратные зависимости пока доступны "
                "только в тестовом режиме"
            )

        if not args.output.strip():
            raise ValueError("Путь результата не может быть пустым")

    def _validate_package(self, package, mode):
        """Проверяет имя пакета для выбранного режима."""
        if mode == "test":
            pattern = r"[A-Z]+"
        else:
            pattern = r"[a-z0-9][a-z0-9+.-]+"

        if not re.fullmatch(pattern, package):
            raise ValueError("Недопустимое имя пакета для выбранного режима")

    def _validate_repo(self, repo, mode):
        """Проверяет тестовый файл или URL репозитория."""
        if mode == "test":
            path = Path(repo)

            if not path.is_file():
                raise ValueError(f"Тестовый файл не найден: {repo}")

            try:
                with path.open("rb"):
                    pass
            except OSError as error:
                raise ValueError(
                    f"Не удалось открыть тестовый файл: {error}"
                ) from error
              
            return
         
        address = urlparse(repo)

        if address.scheme not in ("http", "https") or not address.hostname:
            raise ValueError("Укажите URL репозитория с http:// или https://")


def format_node(node):
    """Форматирует имя тестового или реального пакета."""
    if isinstance(node, tuple):
        package, version = node
        return f"{package} ({version})"

    return node


def print_graph(graph):
    """Выводит список связей построенного графа."""
    for node, dependencies in graph.items():
        targets = ", ".join(
            format_node(dependency)
            for dependency in dependencies
        )
        print(f"{format_node(node)}: {targets or '-'}")


def main():
    """Запускает приложение"""
    try:
        config = ConfigParser().parse()

        if config.mode == "test":
            repository = FixtureRepository.from_file(config.repo)
            repository.get_dependencies(config.package)

            if config.reverse:
                repository = repository.reversed()

            get_dependencies = repository.get_dependencies
            root = config.package
        else:
            repository = UbuntuRepository.from_url(config.repo)

            repository.get_dependencies(
                config.package,
                config.pkg_version
            )

            resolver = DependencyResolver(repository)
            get_dependencies = resolver.get_dependencies
            root = (config.package, config.pkg_version)

        builder = DependencyGraph(get_dependencies)
        graph = builder.build(root, config.max_depth)

        if config.ascii_tree:
            print(to_ascii(graph, root))
        else:
            print_graph(graph)

        if not config.no_render:
            dot_path, image_path = render_graph(
                graph,
                config.output
            )

            print(f"DOT: {dot_path}")

            if image_path is not None:
                print(f"PNG: {image_path}")

                if not config.no_open:
                    open_image(image_path)
            
    except (ValueError, OSError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
