import re
from itertools import zip_longest


def _compare_values(left, right):
    """Возвращает знак результата сравнения."""
    return (left > right) - (left < right)


def _split_version(version):
    """Разделяет корректную версию на эпоху, основу и ревизию."""
    epoch = 0

    if ":" in version:
        epoch_text, version = version.split(":", 1)
        epoch = int(epoch_text)

    upstream, separator, revision = version.rpartition("-")

    if not separator:
        upstream = version
        revision = "0"

    return epoch, upstream, revision


def _character_order(character):
    """Определяет порядок нечислового символа."""
    if character == "~":
        return -1

    if not character:
        return 0

    if character.isascii() and character.isalpha():
        return ord(character)

    return ord(character) + 256


def _compare_text(left, right):
    """Сравнивает нечисловые участки версии."""
    for first, second in zip_longest(left, right, fillvalue=""):
        result = _compare_values(
            _character_order(first),
            _character_order(second)
        )

        if result:
            return result

    return 0


def _compare_numbers(left, right):
    """Сравнивает числовые участки без ведущих нулей."""
    left = left.lstrip("0")
    right = right.lstrip("0")

    result = _compare_values(len(left), len(right))

    if result:
        return result

    return _compare_values(left, right)


def _compare_parts(left, right):
    """Сравнивает чередующиеся текстовые и числовые участки."""
    pattern = r"([^0-9]*)([0-9]*)(.*)"

    while left or right:
        left_text, left_number, left = re.fullmatch(pattern, left).groups()

        right_text, right_number, right = re.fullmatch(pattern, right).groups()

        result = _compare_text(left_text, right_text)

        if result:
            return result

        result = _compare_numbers(left_number, right_number)

        if result:
            return result

    return 0


def compare_versions(left, right):
    """Сравнивает две корректные версии Debian."""
    left_epoch, left_upstream, left_revision = _split_version(left)
    right_epoch, right_upstream, right_revision = _split_version(right)

    result = _compare_values(left_epoch, right_epoch)

    if result:
        return result

    result = _compare_parts(left_upstream, right_upstream)

    if result:
        return result

    return _compare_parts(left_revision, right_revision)

def satisfies_version(version, operator, required):
    """Проверяет соответствие версии заданному ограничению."""
    result = compare_versions(version, required)

    checks = {
        "<<": result < 0,
        "<=": result <= 0,
        "=": result == 0,
        ">=": result >= 0,
        ">>": result > 0
    }

    if operator not in checks:
        raise ValueError(
            f"Неизвестный оператор версии: {operator}"
        )

    return checks[operator]
