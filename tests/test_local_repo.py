"""Тесты тестового репозитория (граф пакетов из файла)."""

from pathlib import Path

import pytest

from apt_repo import RepositoryError
from local_repo import LocalSource, load_local_repo, parse_local_repo

REPOS = Path(__file__).parent.parent / "repos"


def test_parse_formats():
    """Разделители, комментарии, пустые строки, пакеты без зависимостей."""
    repo = parse_local_repo("# c\nA: B, C D  # x\n\nB:\n")
    assert repo == {"A": ["B", "C", "D"], "B": []}


@pytest.mark.parametrize(
    "text, fragment",
    [
        ("A B\n", "ожидается"),
        ("a: B\n", "недопустимое имя"),
        ("A: B1\n", "недопустимое имя"),
        ("A: B\nA: C\n", "уже описан"),
    ],
)
def test_parse_errors(text, fragment):
    """Ошибки формата сообщаются с номером строки."""
    with pytest.raises(RepositoryError, match=fragment) as info:
        parse_local_repo(text)
    assert "строка" in str(info.value)


def test_load_sample_repos():
    """Файлы из каталога repos/ корректны (кроме broken.txt)."""
    for name in ("simple", "cycles", "complex"):
        assert load_local_repo(str(REPOS / f"{name}.txt"))
    with pytest.raises(RepositoryError, match="broken.txt, строка 3"):
        load_local_repo(str(REPOS / "broken.txt"))


def test_load_missing_file(tmp_path):
    """Нечитаемый файл - ошибка."""
    with pytest.raises(RepositoryError, match="не удалось прочитать"):
        load_local_repo(str(tmp_path / "none.txt"))


def test_source():
    """Источник: зависимости без повторов, неописанные пакеты."""
    source = LocalSource({"A": ["B", "B", "C"], "B": []}, "A")
    assert source.dependencies("A") == ["B", "C"]
    assert source.dependencies("C") == []
    assert source.missing == {"C"}


def test_source_unknown_root():
    """Анализируемый пакет должен быть описан или упомянут."""
    with pytest.raises(RepositoryError, match="не найден"):
        LocalSource({"A": []}, "B")
    assert LocalSource({"A": ["B"]}, "B").dependencies("B") == []


def test_source_dependents():
    """Обратные зависимости: пакеты, зависящие от данного."""
    source = LocalSource({"A": ["C", "C"], "B": ["C"], "C": []}, "C")
    assert source.dependents("C") == ["A", "B"]
    assert source.dependents("A") == []
