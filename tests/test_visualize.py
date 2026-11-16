"""Тесты формирования описания на D2 и запуска утилиты d2."""

import subprocess

import pytest

import visualize
from visualize import (
    VisualizationError,
    cycle_edges,
    d2_path,
    quote,
    render_png,
    save_text,
    to_d2,
)


def test_quote():
    """Имена с точками и кавычками экранируются."""
    assert quote("libdb5.3t64") == '"libdb5.3t64"'
    assert quote('a"b') == '"a\\"b"'


def test_to_d2_forward():
    """Узлы, выделенный корень и ребра «пакет -> зависимость»."""
    text = to_d2({"A": ["B"], "B": []}, "A")
    assert text.splitlines() == [
        "direction: down",
        '"A": {style.fill: "#ffd966"}',
        '"B"',
        '"A" -> "B"',
    ]


def test_to_d2_cycles_highlighted():
    """Ребра циклов выделяются красным."""
    text = to_d2({"A": ["B"], "B": ["A", "C"], "C": []}, "A")
    assert '"B" -> "A": {style.stroke: "#cc0000"}' in text
    assert '"A" -> "B": {style.stroke: "#cc0000"}' in text
    assert '"B" -> "C"\n' in text


def test_to_d2_reverse():
    """В графе обратных зависимостей ребра идут от зависящего пакета."""
    text = to_d2({"D": ["B", "C"], "B": [], "C": []}, "D", reverse=True)
    assert '"B" -> "D"' in text
    assert '"C" -> "D"' in text


def test_cycle_edges():
    """Ребра всех циклов."""
    graph = {"A": ["B"], "B": ["A"], "C": ["C"]}
    assert cycle_edges(graph, "A") == {("A", "B"), ("B", "A")}


def test_d2_path():
    """Файл D2 сохраняется рядом с изображением."""
    assert d2_path("out/graph.png") == "out/graph.d2"


def test_save_text(tmp_path):
    """Описание сохраняется; ошибка записи сообщается."""
    path = tmp_path / "g.d2"
    save_text(str(path), "x -> y\n")
    assert path.read_text(encoding="utf-8") == "x -> y\n"
    with pytest.raises(VisualizationError, match="не удалось сохранить"):
        save_text(str(tmp_path / "no" / "g.d2"), "")


def test_render_png_without_d2(monkeypatch):
    """Отсутствие утилиты d2 - понятная ошибка."""
    monkeypatch.setattr(visualize.shutil, "which", lambda name: None)
    with pytest.raises(VisualizationError, match="d2 не найдена"):
        render_png("g.d2", "g.png")


def test_render_png_command(monkeypatch):
    """Утилита вызывается как «d2 ИСХОДНИК ИЗОБРАЖЕНИЕ»."""
    calls = []

    def fake_run(command, **kwargs):
        """Запоминает команду и имитирует успешное выполнение."""
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(visualize.shutil, "which", lambda name: "/bin/d2")
    monkeypatch.setattr(visualize.subprocess, "run", fake_run)
    render_png("g.d2", "g.png")
    assert calls == [["/bin/d2", "g.d2", "g.png"]]


def test_render_png_failure(monkeypatch):
    """Ненулевой код возврата d2 - ошибка с текстом stderr."""
    monkeypatch.setattr(visualize.shutil, "which", lambda name: "/bin/d2")
    monkeypatch.setattr(
        visualize.subprocess, "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 1, "", "err: bad syntax"),
    )
    with pytest.raises(VisualizationError, match="bad syntax"):
        render_png("g.d2", "g.png")
