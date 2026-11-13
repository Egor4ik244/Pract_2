from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "src" / "main.py"


class TestCli(unittest.TestCase):
    """Проверяет интерфейс командной строки."""

    @classmethod
    def setUpClass(cls):
        """Создаёт локальный сервер с тестовым индексом."""
        cls.directory = tempfile.TemporaryDirectory()
        folder = Path(cls.directory.name)
        index = (
            "Package: bash\n"
            "Version: 5.2\n"
            "Pre-Depends: base-lib\n"
            "Depends: example-lib (>= 2.0), tool-a | tool-b\n"
        )
        (folder / "Packages").write_text(index, encoding="utf-8")
        handler = partial(
            SimpleHTTPRequestHandler,
            directory=str(folder),
        )
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = cls.server.server_address[1]
        cls.repo_url = f"http://127.0.0.1:{port}/Packages"
        cls.thread = Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        """Останавливает сервер и удаляет временные файлы."""
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()
        cls.directory.cleanup()

    def setUp(self):
        """Подготавливает корректные аргументы для каждого теста."""
        self.arguments = [
            "--package", "bash",
            "--repo", self.repo_url,
            "--mode", "real",
            "--pkg-version", "5.2",
            "--max-depth", "3"
        ]

    def run_cli(self, arguments):
        """Запускает приложение и возвращает результат."""
        return subprocess.run(
            [sys.executable, str(MAIN), *arguments],
            capture_output=True,
            text=True,
        )

    def replace_argument(self, name, value):
        """Создаёт аргументы с одним заменённым значением."""
        arguments = self.arguments.copy()
        index = arguments.index(name)
        arguments[index + 1] = value
        return arguments

    def test_valid_arguments(self):
        """Проверяет вывод прямых зависимостей."""
        result = self.run_cli(self.arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        expected = [
            "Прямые зависимости bash (5.2):",
            "base-lib",
            "example-lib (>= 2.0)",
            "tool-a | tool-b",
        ]
        self.assertEqual(result.stdout.splitlines(), expected)

    def test_ascii_flag(self):
        """Проверяет принятие флага ASCII."""
        result = self.run_cli(self.arguments + ["--ascii"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("base-lib", result.stdout)

    def test_missing_package_in_repository(self):
        """Проверяет сообщение об отсутствующем пакете."""
        arguments = self.replace_argument("--package", "missing")
        result = self.run_cli(arguments)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Пакет missing не найден", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_missing_version_in_repository(self):
        """Проверяет сообщение об отсутствующей версии."""
        arguments = self.replace_argument("--pkg-version", "9.0")
        result = self.run_cli(arguments)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "Версия 9.0 пакета bash не найдена",
            result.stderr,
        )
        self.assertEqual(result.stdout, "")

    def test_invalid_values(self):
        """Проверяет отклонение ошибочных параметров."""
        cases = [
            ("--package", "BAD", 1),
            ("--repo", "invalid-url", 1),
            ("--mode", "unknown", 2),
            ("--pkg-version", "", 1),
            ("--pkg-version", "5 2", 1),
            ("--max-depth", "-1", 1),
            ("--max-depth", "abc", 2)
        ]

        for name, value, expected_code in cases:
            with self.subTest(argument=name, value=value):
                arguments = self.replace_argument(name, value)
                result = self.run_cli(arguments)

                self.assertEqual(result.returncode, expected_code)
                self.assertNotEqual(result.stderr, "")
                self.assertEqual(result.stdout, "")

    def test_missing_required_arguments(self):
        """Проверяет обязательность каждого параметра."""
        names = [
            "--package",
            "--repo",
            "--mode",
            "--pkg-version",
            "--max-depth",
        ]

        for name in names:
            with self.subTest(argument=name):
                arguments = self.arguments.copy()
                index = arguments.index(name)
                del arguments[index:index + 2]

                result = self.run_cli(arguments)

                self.assertEqual(result.returncode, 2)
                self.assertIn(name, result.stderr)

    def test_ascii_rejects_value(self):
        """Проверяет, что флаг ASCII не принимает значение."""
        result = self.run_cli(self.arguments + ["--ascii", "yes"])

        self.assertEqual(result.returncode, 2)
        self.assertNotEqual(result.stderr, "")

    def test_test_mode(self):
        """Проверяет запуск с существующим тестовым файлом."""
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repository.txt"
            repo.write_text("", encoding="utf-8")

            arguments = [
                "--package", "A",
                "--repo", str(repo),
                "--mode", "test",
                "--pkg-version", "1",
                "--max-depth", "0",
            ]

            result = self.run_cli(arguments)

            self.assertEqual(result.returncode, 0)
            self.assertIn("mode: test", result.stdout)
            self.assertIn("max-depth: 0", result.stdout)

    def test_missing_test_file(self):
        """Проверяет ошибку при отсутствии тестового файла."""
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "missing.txt"

            arguments = [
                "--package", "A",
                "--repo", str(repo),
                "--mode", "test",
                "--pkg-version", "1",
                "--max-depth", "2",
            ]

            result = self.run_cli(arguments)

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "Тестовый файл не найден",
                result.stderr,
            )


if __name__ == "__main__":
    unittest.main()

