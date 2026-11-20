import gzip
from urllib.error import URLError
from urllib.request import urlopen


class UbuntuRepository:
    """Получает сведения о пакетах из индекса Ubuntu."""

    def __init__(self, text):
        self._packages = self._parse_packages(text)

    def _parse_packages(self, text):
        """Преобразует текст индекса в список записей."""
        packages = []
        fields = {}
        current_field = None

        for line in text.splitlines():
            if not line:
                if fields:
                    packages.append(fields)

                fields = {}
                current_field = None
                continue

            if line.startswith((" ", "\t")):
                self._append_continuation(fields, current_field, line)
                continue

            current_field = self._parse_field(fields, line)

        if fields:
            packages.append(fields)

        return packages

    def _append_continuation(self, fields, current_field, line):
        """Добавляет строку продолжения к текущему полю."""
        if current_field is None:
            raise ValueError("Продолжение поля без начальной строки")

        fields[current_field] += "\n" + line[1:]

    def _parse_field(self, fields, line):
        """Сохраняет новое поле и возвращает его имя."""
        name, separator, value = line.partition(":")

        if not separator or not name or name.strip() != name:
            raise ValueError(f"Некорректная строка индекса: {line}")

        if name in fields:
            raise ValueError(f"Повторяющееся поле: {name}")

        fields[name] = value.lstrip()
        return name

    def get_dependencies(self, package, version):
        """Возвращает группы прямых обязательных зависимостей."""
        package_found = False

        for fields in self._packages:
            if fields.get("Package") != package:
                continue

            package_found = True

            if fields.get("Version") != version:
                continue

            dependencies = []

            for name in ("Pre-Depends", "Depends"):
                value = fields.get(name, "")
                value = " ".join(value.split())

                for group in value.split(","):
                    group = group.strip()

                    if group:
                        dependencies.append(group)

            return dependencies

        if package_found:
            raise ValueError(
                f"Версия {version} пакета {package} не найдена"
            )
        raise ValueError(f"Пакет {package} не найден")

    @classmethod
    def from_url(cls, url):
        """Создаёт репозиторий из индекса по URL."""
        try:
            with urlopen(url, timeout=30) as response:
                data = response.read()
        except (URLError, OSError, ValueError) as error:
            raise ValueError(
                f"Не удалось загрузить индекс: {error}"
            ) from error

        if data.startswith(b"\x1f\x8b"):
            try:
                data = gzip.decompress(data)
            except (OSError, EOFError) as error:
                raise ValueError(
                    f"Не удалось распаковать индекс: {error}"
                ) from error

        try:
            text= data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(
                "Индекс должен содержать текст в кодировке UTF-8"
            ) from error

        return cls(text)

    def get_versions(self, package):
        """Возвращает доступные версии пакета."""
        versions = []

        for fields in self._packages:
            if fields.get("Package") != package:
                continue

            version = fields.get("Version")

            if version and version not in versions:
                versions.append(version)

        return versions
