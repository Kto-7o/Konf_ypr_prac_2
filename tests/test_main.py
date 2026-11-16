"""Тесты точки входа: вывод прямых зависимостей и коды возврата."""

from pathlib import Path

from main import EXIT_FAILURE, EXIT_OK, main

PACKAGES = Path(__file__).parent / "data" / "Packages"


def run(tmp_path, package="curl", version="8.5.0-2ubuntu10", test_mode=False):
    """Создает конфигурацию для тестового индекса и запускает main."""
    path = tmp_path / "config.yaml"
    path.write_text(
        f"package: {package}\n"
        f"repository: {PACKAGES.as_uri()}\n"
        f"test_mode: {str(test_mode).lower()}\n"
        f'version: "{version}"\n'
        "output: graph.png\n",
        encoding="utf-8",
    )
    return main(["--config", str(path)])


def test_prints_direct_dependencies(tmp_path, capsys):
    """Выводятся все прямые зависимости заданной версии."""
    assert run(tmp_path) == EXIT_OK
    assert capsys.readouterr().out.splitlines() == [
        "Прямые зависимости curl 8.5.0-2ubuntu10:",
        "  libc6 (>= 2.34)",
        "  libcurl4t64 (= 8.5.0-2ubuntu10)",
        "  zlib1g (>= 1:1.1.4)",
    ]


def test_no_dependencies(tmp_path, capsys):
    """Пакет без зависимостей."""
    assert run(tmp_path, "gcc-14-base", "14-20240412-0ubuntu1") == EXIT_OK
    assert "(нет зависимостей)" in capsys.readouterr().out


def test_unknown_version(tmp_path, capsys):
    """Неизвестная версия - ошибка репозитория, код возврата 1."""
    assert run(tmp_path, version="9.9") == EXIT_FAILURE
    assert capsys.readouterr().err.startswith("Ошибка репозитория: ")


def test_config_error_exit_code(tmp_path, capsys):
    """Ошибки конфигурации выводятся в stderr, код возврата 1."""
    assert run(tmp_path, package="CURL") == EXIT_FAILURE
    err = capsys.readouterr().err
    assert err.startswith("Ошибка конфигурации: package: ")
