"""Тесты точки входа: описание на D2, изображение и коды возврата."""

from pathlib import Path

import pytest

import main as main_module
from main import EXIT_FAILURE, EXIT_OK, main
from visualize import VisualizationError

ROOT = Path(__file__).parent.parent
PACKAGES = ROOT / "tests" / "data" / "Packages"


@pytest.fixture(name="rendered")
def fake_render(monkeypatch):
    """Подменяет вызов утилиты d2: создает пустой PNG-файл."""
    calls = []

    def render(source, image):
        """Запоминает аргументы и создает файл изображения."""
        calls.append((source, image))
        Path(image).write_bytes(b"")

    monkeypatch.setattr(main_module, "render_png", render)
    return calls


def write_config(tmp_path, **values):
    """Записывает конфигурацию (по умолчанию - curl из тестового
    индекса) и возвращает аргументы командной строки."""
    params = {
        "package": "curl",
        "repository": PACKAGES.as_uri(),
        "test_mode": "false",
        "version": '"8.5.0-2ubuntu10"',
        "output": str(tmp_path / "graph.png"),
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


def test_d2_and_png(tmp_path, capsys, rendered):
    """Описание D2 выводится, сохраняется и передается утилите d2."""
    assert main(local(tmp_path, "A", "simple")) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("Граф зависимостей A (D2):\ndirection: down\n")
    assert '"A" -> "B"' in out
    source = tmp_path / "graph.d2"
    assert rendered == [(str(source), str(tmp_path / "graph.png"))]
    assert '"E" -> "G"' in source.read_text(encoding="utf-8")
    assert f"Изображение графа: {tmp_path / 'graph.png'}" in out


def test_cycles_and_reverse(tmp_path, capsys, rendered):
    """Циклы выделяются; обратные зависимости рисуются к пакету."""
    assert main(local(tmp_path, "E", "cycles", reverse="true")) == EXIT_OK
    out = capsys.readouterr().out
    assert '"C" -> "E"' in out
    assert "Циклическая зависимость: E -> F -> E" in out
    assert 'style.stroke: "#cc0000"' in out
    assert len(rendered) == 1


def test_apt_graph(tmp_path, capsys, rendered):
    """Граф из индекса Ubuntu: имена с точками в кавычках."""
    assert main(write_config(tmp_path)) == EXIT_OK
    out = capsys.readouterr().out
    assert '"curl" -> "libcurl4t64"' in out
    assert "Нет в репозитории (без зависимостей): multiarch-support" in out


def test_root_filtered(tmp_path, capsys, rendered):
    """Если фильтр исключил пакет, изображение не строится."""
    assert main(local(tmp_path, "APP", "complex", "AP")) == EXIT_OK
    assert "пакет исключен фильтром" in capsys.readouterr().out
    assert rendered == []


def test_visualization_error(tmp_path, capsys, monkeypatch):
    """Ошибка утилиты d2: код возврата 1, описание D2 сохранено."""

    def fail(source, image):
        """Имитирует отсутствие утилиты d2."""
        raise VisualizationError("утилита d2 не найдена")

    monkeypatch.setattr(main_module, "render_png", fail)
    assert main(local(tmp_path, "A", "simple")) == EXIT_FAILURE
    assert "Ошибка визуализации" in capsys.readouterr().err
    assert (tmp_path / "graph.d2").exists()


def test_errors(tmp_path, capsys):
    """Ошибки конфигурации и репозитория: код возврата 1."""
    assert main(write_config(tmp_path, package="CURL")) == EXIT_FAILURE
    assert main(local(tmp_path, "Z", "simple")) == EXIT_FAILURE
    err = capsys.readouterr().err.splitlines()
    assert err[0].startswith("Ошибка конфигурации: ")
    assert err[1].startswith("Ошибка репозитория: ")
