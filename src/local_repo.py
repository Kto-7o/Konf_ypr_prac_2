"""Тестовый репозиторий: граф пакетов, заданный текстовым файлом.

Формат файла - одна строка на пакет:
    A: B C      # пакет A зависит от B и C
    D:          # пакет D без зависимостей
Пакеты называются большими латинскими буквами. Зависимости
перечисляются через пробел или запятую. Пустые строки и комментарии
(от символа # до конца строки) пропускаются. Пакет, на который есть
ссылка, но который не описан в файле, считается пакетом без
зависимостей.
"""

import re
from typing import Dict, List, Set

from apt_repo import RepositoryError

NAME_RE = re.compile(r"^[A-Z]+$")
SEPARATOR_RE = re.compile(r"[\s,]+")

LocalRepo = Dict[str, List[str]]


def _parse_line(line: str, number: int) -> List[str]:
    """Разбирает строку «ИМЯ: ЗАВИСИМОСТИ» в список [имя, *зависимости].

    Raises:
        RepositoryError: неверный формат строки или имени пакета.
    """
    name, colon, rest = line.partition(":")
    if not colon:
        raise RepositoryError(f"строка {number}: ожидается «ИМЯ: зависимости»")
    names = [name.strip()] + [n for n in SEPARATOR_RE.split(rest) if n]
    for item in names:
        if not NAME_RE.match(item):
            raise RepositoryError(
                f"строка {number}: недопустимое имя пакета {item!r} "
                "(нужны большие латинские буквы)"
            )
    return names


def parse_local_repo(text: str) -> LocalRepo:
    """Разбирает текст тестового репозитория.

    Raises:
        RepositoryError: ошибка формата или повторное описание пакета.
    """
    repo: LocalRepo = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, *dependencies = _parse_line(line, number)
        if name in repo:
            raise RepositoryError(f"строка {number}: пакет {name} уже описан")
        repo[name] = dependencies
    return repo


def load_local_repo(path: str) -> LocalRepo:
    """Читает и разбирает файл тестового репозитория.

    Raises:
        RepositoryError: файл не читается или имеет неверный формат.
    """
    try:
        with open(path, encoding="utf-8") as file:
            text = file.read()
    except (OSError, UnicodeDecodeError) as error:
        raise RepositoryError(f"не удалось прочитать {path}: {error}") from None
    try:
        return parse_local_repo(text)
    except RepositoryError as error:
        raise RepositoryError(f"{path}, {error}") from None


class LocalSource:
    """Источник зависимостей - тестовый репозиторий.

    Attributes:
        missing: пакеты, на которые есть ссылки, но нет описания.
    """

    def __init__(self, repo: LocalRepo, root: str):
        """Проверяет, что анализируемый пакет описан в репозитории.

        Raises:
            RepositoryError: пакет root отсутствует.
        """
        if root not in repo:
            raise RepositoryError(
                f"пакет {root} не найден в тестовом репозитории"
            )
        self.repo = repo
        self.missing: Set[str] = set()

    def dependencies(self, name: str) -> List[str]:
        """Возвращает прямые зависимости пакета."""
        if name not in self.repo:
            self.missing.add(name)
            return []
        return list(dict.fromkeys(self.repo[name]))
