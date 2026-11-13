import argparse
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from repository import UbuntuRepository


class AppConfig:
    """Хранит настройки приложения."""

    def __init__(
            self,
            package,
            repo,
            mode,
            pkg_version,
            ascii_tree,
            max_depth
        ):
            self.package = package
            self.repo = repo
            self.mode = mode
            self.pkg_version = pkg_version
            self.ascii_tree = ascii_tree
            self.max_depth = max_depth

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

    def parse(self):
        """Читает аргументы и создает объект настроек."""
        args = self._parser.parse_args()
        self._validate(args)

        return AppConfig(
            package=args.package,
            repo=args.repo,
            mode=args.mode,
            pkg_version=args.pkg_version,
            ascii_tree=args.ascii_tree,
            max_depth=args.max_depth
        )

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


def main():
    """Запускает приложение"""
    try:
        parser = ConfigParser()
        config = parser.parse()

        if config.mode == "test":
            config.print_summary()
            return 0;

        repository = UbuntuRepository.from_url(config.repo)
        dependencies = repository.get_dependencies(
            config.package,
            config.pkg_version
        )

        print(
            f"Прямые зависимости "
            f"{config.package} ({config.pkg_version}):"
        )

        if dependencies:
            for dependency in dependencies:
                print(dependency)
        else:
            print("Обязательных зависимостей нет")
            
    except ValueError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

