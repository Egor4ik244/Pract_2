import unittest

from src.versions import compare_versions, satisfies_version


class TestVersions(unittest.TestCase):
    """Проверяет сравнение версий Debian."""

    def test_version_order(self):
        """Проверяет числовые части, эпохи и специальные символы."""
        cases = [
            ("1.9", "1.10", -1),
            ("1.0~rc1", "1.0", -1),
            ("1.0-2", "1.0-10", -1),
            ("1:1.0", "2.0", 1),
            ("1.01", "1.1", 0),
            ("1.0", "1.0-0", 0),
            ("1.0~~", "1.0~", -1),
            ("1.0a", "1.0+", -1),
            ("1.0-1ubuntu2", "1.0-1ubuntu10", -1),
            ("0:1.0", "1.0", 0),
        ]

        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(
                    compare_versions(left, right),
                    expected,
                )
                self.assertEqual(
                    compare_versions(right, left),
                    -expected,
                )

    def test_version_constraints(self):
        """Проверяет все поддерживаемые операторы."""
        cases = [
            ("<<", "1.0", "2.0", True),
            ("<<", "2.0", "2.0", False),
            ("<=", "2.0", "2.0", True),
            ("<=", "3.0", "2.0", False),
            ("=", "1.01", "1.1", True),
            ("=", "1.0", "2.0", False),
            (">=", "2.0", "2.0", True),
            (">=", "1.0", "2.0", False),
            (">>", "3.0", "2.0", True),
            (">>", "2.0", "2.0", False),
        ]

        for operator, version, required, expected in cases:
            with self.subTest(
                operator=operator,
                version=version,
                required=required,
            ):
                self.assertEqual(
                    satisfies_version(version, operator, required),
                    expected,
                )

    def test_unknown_operator(self):
        """Проверяет отклонение неизвестного оператора."""
        with self.assertRaisesRegex(
            ValueError,
            "Неизвестный оператор",
        ):
            satisfies_version("1.0", "!=", "2.0")


if __name__ == "__main__":
    unittest.main()
    