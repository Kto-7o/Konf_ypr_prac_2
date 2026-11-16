"""Тесты получения и разбора данных репозитория Ubuntu."""

import gzip
import lzma
from pathlib import Path

import pytest

from apt_repo import (
    AptSource,
    Dependency,
    RepositoryError,
    build_provides,
    decompress,
    direct_dependencies,
    find_package,
    load_index,
    parse_depends,
    parse_index,
    parse_stanza,
)

PACKAGES = Path(__file__).parent / "data" / "Packages"


def test_parse_stanza_continuation():
    """Строки-продолжения присоединяются к предыдущему полю."""
    fields = parse_stanza("Package: a\nDepends: b,\n c\nVersion: 1")
    assert fields == {"Package": "a", "Depends": "b, c", "Version": "1"}


def test_parse_depends():
    """Разбор ограничений версий, альтернатив и архитектуры."""
    deps = parse_depends("libc6 (>= 2.34), a | b (<< 2), python3:any, ")
    assert deps == [
        Dependency("libc6", "libc6 (>= 2.34)"),
        Dependency("a", "a | b (<< 2)"),
        Dependency("python3", "python3:any"),
    ]


def test_parse_index_groups_versions():
    """Несколько версий одного пакета хранятся вместе."""
    index = parse_index(PACKAGES.read_text(encoding="utf-8"))
    assert len(index["curl"]) == 2
    assert "gcc-14-base" in index


def test_parse_index_empty():
    """Текст без пакетов - ошибка."""
    with pytest.raises(RepositoryError, match="пуст"):
        parse_index("hello\n\nworld\n")


@pytest.mark.parametrize("pack", [bytes, gzip.compress, lzma.compress])
def test_decompress(pack):
    """Поддерживаются индексы без сжатия, gzip и xz."""
    assert decompress(pack(b"Package: a\r\n")) == "Package: a\n"


def test_decompress_broken_archive():
    """Поврежденный архив - ошибка."""
    with pytest.raises(RepositoryError, match="поврежденный"):
        decompress(gzip.compress(b"Package: a")[:12])


def test_load_index_from_file_url(tmp_path):
    """Индекс загружается по URL со схемой file."""
    path = tmp_path / "Packages.gz"
    path.write_bytes(gzip.compress(PACKAGES.read_bytes()))
    index = load_index(path.as_uri())
    assert index["libc6"][0]["Version"] == "2.39-0ubuntu8"


def test_load_index_missing(tmp_path):
    """Недоступный URL - ошибка."""
    with pytest.raises(RepositoryError, match="не удалось загрузить"):
        load_index((tmp_path / "nope").as_uri())


def test_find_package_version():
    """Выбирается заданная пользователем версия."""
    index = parse_index(PACKAGES.read_text(encoding="utf-8"))
    fields = find_package(index, "curl", "8.5.0-2ubuntu10.4")
    deps = [dep.text for dep in direct_dependencies(fields)]
    assert deps[1] == "libcurl4t64 (= 8.5.0-2ubuntu10.4)"


def test_find_package_errors():
    """Отсутствующий пакет или версия - ошибка со списком версий."""
    index = parse_index(PACKAGES.read_text(encoding="utf-8"))
    with pytest.raises(RepositoryError, match="не найден"):
        find_package(index, "wget", "1.0")
    with pytest.raises(RepositoryError, match="8.5.0-2ubuntu10.4"):
        find_package(index, "curl", "1.0")


def test_pre_depends_first():
    """Pre-Depends входят в прямые зависимости."""
    index = parse_index(PACKAGES.read_text(encoding="utf-8"))
    fields = find_package(index, "libcurl4t64", "8.5.0-2ubuntu10")
    names = [dep.name for dep in direct_dependencies(fields)]
    assert names == ["multiarch-support", "libc6", "libssl3t64", "zlib1g"]


def test_build_provides():
    """Виртуальный пакет сопоставляется предоставляющему его пакету."""
    index = parse_index(PACKAGES.read_text(encoding="utf-8"))
    assert build_provides(index) == {"libgnutls30": "libgnutls30t64"}


def test_apt_source():
    """Источник: заданная версия корня, разрешение виртуальных пакетов."""
    index = parse_index(PACKAGES.read_text(encoding="utf-8"))
    source = AptSource(index, "curl", "8.5.0-2ubuntu10.4")
    assert source.dependencies("curl") == ["libc6", "libcurl4t64", "zlib1g"]
    assert source.dependencies("librtmp1")[1] == "libgnutls30t64"
    assert source.dependencies("multiarch-support") == []
    assert source.missing == {"multiarch-support"}


def test_apt_source_unknown_version():
    """Неизвестная версия анализируемого пакета - ошибка."""
    index = parse_index(PACKAGES.read_text(encoding="utf-8"))
    with pytest.raises(RepositoryError):
        AptSource(index, "curl", "0.1")
