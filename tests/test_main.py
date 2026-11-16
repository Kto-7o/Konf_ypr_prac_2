"""Тесты точки входа: вывод графа зависимостей и коды возврата."""

from pathlib import Path

from main import EXIT_FAILURE, EXIT_OK, main

ROOT = Path(__file__).parent.parent
PACKAGES = ROOT / "tests" / "data" / "Packages"


def write_config(tmp_path, **values):
    """Записывает конфигурацию (по умолчанию - curl из тестового
    индекса) и возвращает аргументы командной строки."""
    params = {
        "package": "curl",
        "repository": PACKAGES.as_uri(),
        "test_mode": "false",
        "version": '"8.5.0-2ubuntu10"',
        "output": "graph.png",
        **values,
    }
    path = tmp_path / "config.yaml"
    text = "".join(f"{key}: {value}\n" for key, value in params.items())
    path.write_text(text, encoding="utf-8")
    return ["--config", str(path)]


def local(tmp_path, package, repo, exclude="", reverse="false"):
    """Аргументы для запуска на файле из каталога repos/."""
    return write_config(
        tmp_path,
        package=package,
        repository=str(ROOT / "repos" / f"{repo}.txt"),
        test_mode="true",
        filter=f'"{exclude}"',
        reverse=reverse,
    )


def test_local_reverse(tmp_path, capsys):
    """Обратные зависимости в тестовом репозитории."""
    assert main(local(tmp_path, "E", "simple", reverse="true")) == EXIT_OK
    assert capsys.readouterr().out.splitlines() == [
        "Обратные зависимости E:",
        "  E <- B, C",
        "  B <- A",
        "  C <- A",
        "  A <- (нет)",
        "Зависят от E: 3",
        "Циклических зависимостей нет",
    ]


def test_local_reverse_cycle_and_filter(tmp_path, capsys):
    """Обратные зависимости с циклом; фильтр."""
    assert main(local(tmp_path, "E", "cycles", reverse="true")) == EXIT_OK
    out = capsys.readouterr().out
    assert "Циклическая зависимость: E -> F -> E" in out
    args = local(tmp_path, "BASE", "complex", "LIB", reverse="true")
    assert main(args) == EXIT_OK
    out = capsys.readouterr().out
    assert "LIB" not in out.split("\n", 1)[1]


def test_apt_reverse(tmp_path, capsys):
    """Обратные зависимости в индексе Ubuntu."""
    args = write_config(
        tmp_path, package="zlib1g", version='"1:1.3.dfsg-3.1ubuntu2"',
        reverse="true",
    )
    assert main(args) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "Обратные зависимости zlib1g 1:1.3.dfsg-3.1ubuntu2:"
    assert out[1] == "  zlib1g <- curl, libcurl4t64"


def test_apt_graph(tmp_path, capsys):
    """Граф из индекса Ubuntu с транзитивными зависимостями и циклом."""
    assert main(write_config(tmp_path)) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "Граф зависимостей curl 8.5.0-2ubuntu10:"
    edges = "  libcurl4t64 -> multiarch-support, libc6, libssl3t64, zlib1g"
    assert edges in out
    assert "Циклическая зависимость: libc6 -> libgcc-s1 -> libc6" in out
    assert out[-1] == "Нет в репозитории (без зависимостей): multiarch-support"


def test_apt_virtual_package(tmp_path, capsys):
    """Виртуальный пакет заменяется реальным (поле Provides)."""
    args = write_config(
        tmp_path, package="librtmp1",
        version='"2.4+20151223.gitfa8646d.1-2build7"',
    )
    assert main(args) == EXIT_OK
    out = capsys.readouterr().out
    assert "librtmp1 -> libc6, libgnutls30t64, libgmp10" in out


def test_local_cycles(tmp_path, capsys):
    """Тестовый репозиторий с циклами."""
    assert main(local(tmp_path, "A", "cycles")) == EXIT_OK
    out = capsys.readouterr().out
    assert "Циклическая зависимость: A -> B -> C -> A" in out
    assert "Циклическая зависимость: D -> D" in out


def test_local_filter(tmp_path, capsys):
    """Фильтр в тестовом режиме."""
    assert main(local(tmp_path, "APP", "complex", "LIB")) == EXIT_OK
    out = capsys.readouterr().out
    assert "LIB" not in out.split("\n", 1)[1]
    assert "Пакетов в графе: 6" in out


def test_local_root_filtered(tmp_path, capsys):
    """Фильтр исключил сам пакет."""
    assert main(local(tmp_path, "APP", "complex", "AP")) == EXIT_OK
    assert "пакет исключен фильтром" in capsys.readouterr().out


def test_repository_errors(tmp_path, capsys):
    """Ошибки репозитория: код возврата 1, сообщение в stderr."""
    assert main(local(tmp_path, "Z", "simple")) == EXIT_FAILURE
    assert main(write_config(tmp_path, version='"9.9"')) == EXIT_FAILURE
    err = capsys.readouterr().err.splitlines()
    assert all(line.startswith("Ошибка репозитория: ") for line in err)


def test_config_error_exit_code(tmp_path, capsys):
    """Ошибки конфигурации выводятся в stderr, код возврата 1."""
    assert main(write_config(tmp_path, package="CURL")) == EXIT_FAILURE
    err = capsys.readouterr().err
    assert err.startswith("Ошибка конфигурации: package: ")
