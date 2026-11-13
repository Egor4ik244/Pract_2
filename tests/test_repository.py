import gzip
from io import BytesIO
import unittest
from unittest.mock import patch

from src.repository import UbuntuRepository


INDEX = """Package: example-app
Version: 1.0
Pre-Depends: base-lib
Depends: example-lib (>= 2.0),
 tool-a | tool-b

Package: example-app
Version: 2.0
Depends: new-lib

Package: independent
Version: 1.0
"""


class TestUbuntuRepository(unittest.TestCase):
    """Проверяет чтение индекса и получение зависимостей."""

    def setUp(self):
        """Создаёт репозиторий перед каждым тестом."""
        self.repository = UbuntuRepository(INDEX)

    def test_dependencies(self):
        """Проверяет зависимости и продолжение строки."""
        result = self.repository.get_dependencies(
            "example-app", "1.0"
        )

        self.assertEqual(
            result,
            [
                "base-lib",
                "example-lib (>= 2.0)",
                "tool-a | tool-b",
            ],
        )

    def test_exact_version(self):
        """Проверяет выбор указанной версии."""
        result = self.repository.get_dependencies(
            "example-app", "2.0"
        )

        self.assertEqual(result, ["new-lib"])

    def test_no_dependencies(self):
        """Проверяет пакет без зависимостей."""
        result = self.repository.get_dependencies(
            "independent", "1.0"
        )

        self.assertEqual(result, [])

    def test_missing_package(self):
        """Проверяет отсутствие пакета."""
        with self.assertRaisesRegex(
            ValueError, "Пакет missing не найден"
        ):
            self.repository.get_dependencies("missing", "1.0")

    def test_missing_version(self):
        """Проверяет отсутствие указанной версии."""
        with self.assertRaisesRegex(
            ValueError, "Версия 3.0 пакета example-app не найдена"
        ):
            self.repository.get_dependencies("example-app", "3.0")

    def test_invalid_index(self):
        """Проверяет отклонение повреждённых записей."""
        cases = [
            "Некорректная строка",
            " продолжение без поля",
            "Package: first\nPackage: second",
        ]

        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    UbuntuRepository(text)

    def test_load_plain_index(self):
        """Проверяет загрузку несжатого индекса."""
        data = INDEX.encode("utf-8")

        with patch(
            "src.repository.urlopen",
            return_value=BytesIO(data),
        ) as mocked_urlopen:
            repository = UbuntuRepository.from_url(
                "https://example.com/Packages"
            )

        self.assertEqual(
            repository.get_dependencies("example-app", "2.0"),
            ["new-lib"],
        )
        mocked_urlopen.assert_called_once_with(
            "https://example.com/Packages",
            timeout=30,
        )

    def test_load_gzip_index(self):
        """Проверяет распаковку загруженного индекса."""
        data = gzip.compress(INDEX.encode("utf-8"))

        with patch(
            "src.repository.urlopen",
            return_value=BytesIO(data),
        ):
            repository = UbuntuRepository.from_url(
                "https://example.com/Packages.gz"
            )

        self.assertEqual(
            repository.get_dependencies("example-app", "2.0"),
            ["new-lib"],
        )

    def test_network_error(self):
        """Проверяет обработку ошибки загрузки."""
        with patch(
            "src.repository.urlopen",
            side_effect=OSError("Соединение недоступно"),
        ):
            with self.assertRaisesRegex(
                ValueError, "Не удалось загрузить индекс"
            ):
                UbuntuRepository.from_url(
                    "https://example.com/Packages"
                )

    def test_invalid_encoding(self):
        """Проверяет ошибку декодирования."""
        with patch(
            "src.repository.urlopen",
            return_value=BytesIO(b"\xff"),
        ):
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                UbuntuRepository.from_url(
                    "https://example.com/Packages"
                )


if __name__ == "__main__":
    unittest.main()