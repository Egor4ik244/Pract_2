import re


DEPENDENCY_PATTERN = re.compile(
    r"(?P<package>[a-z0-9][a-z0-9+.-]+)"
    r"(?::(?P<architecture>[a-z0-9][a-z0-9-]*))?"
    r"(?:\s*\(\s*(?P<operator><<|<=|=|>=|>>)"
    r"\s*(?P<version>[^\s()]+)\s*\))?"
)


def parse_dependency_group(group):
    """Разбирает группу альтернативных зависимостей."""
    alternatives = []

    for expression in group.split("|"):
        expression = expression.strip()
        match = DEPENDENCY_PATTERN.fullmatch(expression)

        if match is None:
            raise ValueError(
                f"Некорректная зависимость: {expression}"
            )

        if match.group("architecture") is not None:
            raise ValueError(
                "Архитектурные квалификаторы пока не поддерживаются: "
                f"{expression}"
            )

        alternatives.append(
            (
                match.group("package"),
                match.group("operator"),
                match.group("version")
            )
        )

    return alternatives
