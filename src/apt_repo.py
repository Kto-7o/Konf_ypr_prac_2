"""Получение данных о зависимостях из репозитория Ubuntu (apt).

Репозиторий задается URL индексного файла Packages (возможно, сжатого
gzip или xz), например:
    http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/
    Packages.gz

Файл состоит из блоков строк «Поле: значение», разделенных пустыми
строками; каждый блок описывает одну версию пакета. Строки,
начинающиеся с пробела, продолжают значение предыдущего поля.
Зависимости берутся из полей Pre-Depends и Depends.
"""

import gzip
import lzma
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Set

GZIP_MAGIC = b"\x1f\x8b"
XZ_MAGIC = b"\xfd7zXZ\x00"
DEPENDS_FIELDS = ("Pre-Depends", "Depends")
DOWNLOAD_TIMEOUT = 60
BLOCK_SEPARATOR = re.compile(r"\n[ \t]*\n")
DEP_NAME_RE = re.compile(r"^([^\s(:\[|]+)")

Stanza = Dict[str, str]
Index = Dict[str, List[Stanza]]


class RepositoryError(Exception):
    """Ошибка получения или разбора данных репозитория."""


@dataclass(frozen=True)
class Dependency:
    """Одна запись из списка зависимостей пакета.

    Attributes:
        name: имя пакета (для альтернатив «a | b» - первая из них).
        text: исходная запись, например «libc6 (>= 2.34)».
    """

    name: str
    text: str


def download(url: str) -> bytes:
    """Загружает файл по URL (http, https, file).

    Raises:
        RepositoryError: сервер недоступен или вернул ошибку.
    """
    try:
        with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT) as resp:
            return resp.read()
    except urllib.error.HTTPError as error:
        message = f"сервер вернул ошибку {error.code} для {url}"
        raise RepositoryError(message) from None
    except (urllib.error.URLError, OSError, ValueError) as error:
        reason = getattr(error, "reason", error)
        message = f"не удалось загрузить {url}: {reason}"
        raise RepositoryError(message) from None


def decompress(data: bytes) -> str:
    """Распаковывает индекс (gzip, xz или без сжатия) в текст.

    Raises:
        RepositoryError: архив поврежден.
    """
    try:
        if data.startswith(GZIP_MAGIC):
            data = gzip.decompress(data)
        elif data.startswith(XZ_MAGIC):
            data = lzma.decompress(data)
    except (OSError, EOFError, lzma.LZMAError) as error:
        raise RepositoryError(f"поврежденный архив индекса: {error}") from None
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n")


def parse_stanza(block: str) -> Stanza:
    """Разбирает блок «Поле: значение» с учетом строк-продолжений."""
    fields: Stanza = {}
    key = None
    for line in block.splitlines():
        if line[:1] in (" ", "\t"):
            if key is not None:
                fields[key] += " " + line.strip()
        elif ":" in line:
            key, _, value = line.partition(":")
            fields[key] = value.strip()
    return fields


def parse_index(text: str) -> Index:
    """Разбирает индекс Packages: имя пакета -> список его версий.

    Raises:
        RepositoryError: в тексте не найдено ни одного пакета.
    """
    index: Index = {}
    for block in BLOCK_SEPARATOR.split(text):
        fields = parse_stanza(block)
        name = fields.get("Package")
        if name:
            index.setdefault(name, []).append(fields)
    if not index:
        raise RepositoryError("индекс пакетов пуст или имеет неверный формат")
    return index


def load_index(url: str) -> Index:
    """Загружает и разбирает индекс Packages по URL."""
    return parse_index(decompress(download(url)))


def parse_depends(value: str) -> List[Dependency]:
    """Разбирает значение поля Depends.

    Записи разделяются запятыми; альтернативы - символом «|»;
    ограничение версии указывается в скобках; суффикс архитектуры
    вида «:any» отбрасывается.
    """
    result = []
    for group in value.split(","):
        text = " ".join(group.split())
        match = DEP_NAME_RE.match(text)
        if match:
            result.append(Dependency(match.group(1), text))
    return result


def find_package(index: Index, name: str, version: str) -> Stanza:
    """Находит описание заданной версии пакета.

    Raises:
        RepositoryError: пакет или его версия отсутствуют.
    """
    stanzas = index.get(name)
    if not stanzas:
        raise RepositoryError(f"пакет {name} не найден в репозитории")
    for fields in stanzas:
        if fields.get("Version") == version:
            return fields
    available = ", ".join(fields.get("Version", "?") for fields in stanzas)
    raise RepositoryError(
        f"версия {version} пакета {name} не найдена; "
        f"доступные версии: {available}"
    )


def direct_dependencies(fields: Stanza) -> List[Dependency]:
    """Возвращает прямые зависимости (Pre-Depends и Depends)."""
    result: List[Dependency] = []
    for field in DEPENDS_FIELDS:
        result += parse_depends(fields.get(field, ""))
    return result


def build_provides(index: Index) -> Dict[str, str]:
    """Сопоставляет виртуальные пакеты (поле Provides) реальным."""
    provides: Dict[str, str] = {}
    for name, stanzas in index.items():
        for dep in parse_depends(stanzas[0].get("Provides", "")):
            provides.setdefault(dep.name, name)
    return provides


class AptSource:
    """Источник зависимостей - индекс репозитория Ubuntu.

    Для анализируемого пакета берется заданная версия, для остальных
    пакетов - первая найденная в индексе. Из альтернатив «a | b»
    учитывается первая (ее выбирает apt по умолчанию). Виртуальный
    пакет заменяется первым пакетом, который его предоставляет.

    Attributes:
        missing: пакеты, отсутствующие в индексе (например, из других
            компонентов репозитория).
    """

    def __init__(self, index: Index, root: str, version: str):
        """Проверяет наличие заданной версии анализируемого пакета.

        Raises:
            RepositoryError: пакет или версия не найдены.
        """
        self.index = index
        self.root = find_package(index, root, version)
        self.provides = build_provides(index)
        self.missing: Set[str] = set()

    def resolve(self, name: str) -> str:
        """Возвращает реальный пакет для виртуального имени."""
        if name in self.index:
            return name
        return self.provides.get(name, name)

    def dependencies(self, name: str) -> List[str]:
        """Возвращает имена прямых зависимостей пакета без повторов."""
        if name == self.root["Package"]:
            fields = self.root
        elif name in self.index:
            fields = self.index[name][0]
        else:
            self.missing.add(name)
            return []
        dependencies = direct_dependencies(fields)
        names = [self.resolve(dep.name) for dep in dependencies]
        return list(dict.fromkeys(names))
