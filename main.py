import argparse
import os
import sys


class AppConfig:

    def __init__(
        self,
        package: str,
        repo: str,
        mode: str,
        pkg_version: str,
        ascii_tree: bool,
        max_depth: int,
    ):
        self.package = package
        self.repo = repo
        self.mode = mode
        self.pkg_version = pkg_version
        self.ascii_tree = ascii_tree
        self.max_depth = max_depth

    def print_summary(self) -> None:
        print(f"package: {self.package}")
        print(f"repo: {self.repo}")
        print(f"mode: {self.mode}")
        print(f"pkg-version: {self.pkg_version}")
        print(f"ascii: {self.ascii_tree}")
        print(f"max_depth: {self.max_depth}")


class ConfigParser:

    def __init__(self):
        self._parser = argparse.ArgumentParser(
            description="Инструмент визуализации графа зависимостей apt."
        )
        self._setup_arguments() 

    def _setup_arguments(self) -> None:
        self._parser.add_argument("--package", required=True)
        self._parser.add_argument("--repo", required=True)
        self._parser.add_argument(
            "--mode", required=True, choices=["real", "test"]
        )
        self._parser.add_argument("--pkg-version", required=True)
        self._parser.add_argument(
            "--ascii", action="store_true", dest="ascii_tree"
        )  
        self._parser.add_argument("--max-depth", type=int, required=True)

    def parse(self) -> AppConfig:
        args = self._parser.parse_args()

        if args.max_depth < 0:
            raise ValueError("Максимальная глубина не может быть отрицательной")

        if args.mode == "test" and not os.path.exists(args.repo):
            raise FileNotFoundError(
                f"Тестовый файл репозитория не найден: {args.repo}"
            )

        return AppConfig(
            package=args.package,
            repo=args.repo,
            mode=args.mode,
            pkg_version=args.pkg_version,
            ascii_tree=args.ascii_tree,
            max_depth=args.max_depth,
        )


def main() -> None:
    try:
        parser = ConfigParser()
        config = parser.parse()
        config.print_summary()

    except (ValueError, FileNotFoundError) as err:
        print(f"Ошибка валидации: {err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"Критическая ошибка: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
