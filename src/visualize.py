"""Визуализация графа зависимостей на языке диаграмм D2.

Текстовое описание графа на D2 формируется вручную, изображение PNG
строится утилитой командной строки d2 (https://d2lang.com):
    d2 graph.d2 graph.png
Путь к утилите можно задать переменной окружения D2_BIN.

Ребра всегда направлены от пакета к его зависимости. Анализируемый
пакет выделяется цветом, ребра циклических зависимостей - красным.
"""

import os
import shutil
import subprocess
from typing import List, Optional, Set, Tuple

from graph import Graph, find_cycles

D2_BINARY = os.environ.get("D2_BIN", "d2")
D2_SUFFIX = ".d2"
RENDER_TIMEOUT = 300
ROOT_FILL = "#ffd966"
CYCLE_STROKE = "#cc0000"

Edge = Tuple[str, str]


class VisualizationError(Exception):
    """Ошибка сохранения описания графа или построения изображения."""


def quote(name: str) -> str:
    """Заключает имя в кавычки, чтобы D2 не разбирал точки в нем."""
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def cycle_edges(graph: Graph, root: str) -> Set[Edge]:
    """Возвращает ребра графа, входящие в найденные циклы."""
    edges: Set[Edge] = set()
    for cycle in find_cycles(graph, root):
        edges.update(zip(cycle, cycle[1:]))
    return edges


def to_d2(graph: Graph, root: str, reverse: bool = False) -> str:
    """Формирует описание графа на языке D2.

    Args:
        graph: граф «пакет -> зависимости» (при reverse - «пакет ->
            зависящие от него пакеты»).
        root: анализируемый пакет.
        reverse: граф обратных зависимостей.

    Returns:
        Текст диаграммы D2.
    """
    lines = ["direction: down"]
    for name in graph:
        style = f": {{style.fill: \"{ROOT_FILL}\"}}" if name == root else ""
        lines.append(quote(name) + style)
    in_cycles = cycle_edges(graph, root)
    for name, children in graph.items():
        for child in children:
            source, target = (child, name) if reverse else (name, child)
            edge = f"{quote(source)} -> {quote(target)}"
            if (name, child) in in_cycles:
                edge += f": {{style.stroke: \"{CYCLE_STROKE}\"}}"
            lines.append(edge)
    return "\n".join(lines) + "\n"


def d2_path(image_path: str) -> str:
    """Возвращает имя файла D2 рядом с изображением: graph.png ->
    graph.d2."""
    return os.path.splitext(image_path)[0] + D2_SUFFIX


def save_text(path: str, text: str) -> None:
    """Сохраняет описание графа на D2.

    Raises:
        VisualizationError: файл не удалось записать.
    """
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
    except OSError as error:
        message = f"не удалось сохранить {path}: {error.strerror}"
        raise VisualizationError(message) from None


def render_png(source: str, image: str,
               binary: Optional[str] = None) -> None:
    """Строит изображение PNG из файла D2 утилитой d2.

    Raises:
        VisualizationError: утилита не найдена или завершилась с
            ошибкой.
    """
    executable = shutil.which(binary or D2_BINARY)
    if executable is None:
        raise VisualizationError(
            "утилита d2 не найдена; установите ее "
            "(https://d2lang.com/tour/install) или задайте путь в D2_BIN"
        )
    command: List[str] = [executable, source, image]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=RENDER_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise VisualizationError(f"не удалось запустить d2: {error}") from None
    if result.returncode != 0:
        details = result.stderr.strip() or f"код {result.returncode}"
        raise VisualizationError(f"d2 завершилась с ошибкой: {details}")
