"""Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).

Точка входа. Загружает конфигурацию из YAML-файла, строит обходом в
ширину граф зависимостей заданного пакета (с учетом транзитивности)
или, в режиме reverse, граф обратных зависимостей, выводит его
описание на языке диаграмм D2 и сохраняет изображение графа в PNG.
Источник данных - репозиторий Ubuntu или тестовый репозиторий.

Пример запуска:
    python3 src/main.py --config config.yaml
"""

import argparse
import sys
from typing import List, Optional, Union

from apt_repo import AptSource, RepositoryError, load_index
from config import DEFAULT_CONFIG, Config, ConfigError, load_config
from graph import Graph, build_graph, find_cycles
from local_repo import LocalSource, load_local_repo
from visualize import (
    VisualizationError,
    d2_path,
    render_png,
    save_text,
    to_d2,
)

EXIT_OK = 0
EXIT_FAILURE = 1

Source = Union[AptSource, LocalSource]


def build_parser() -> argparse.ArgumentParser:
    """Создает разборщик параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Визуализатор графа зависимостей пакетов Ubuntu.",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=DEFAULT_CONFIG,
        help="путь к YAML-файлу конфигурации (по умолчанию %(default)s)",
    )
    return parser


def make_source(config: Config) -> Source:
    """Создает источник зависимостей согласно режиму работы.

    Raises:
        RepositoryError: репозиторий недоступен или пакет не найден.
    """
    if config.test_mode:
        repo = load_local_repo(config.repository)
        return LocalSource(repo, config.package)
    index = load_index(config.repository)
    return AptSource(index, config.package, config.version)


def make_graph(config: Config, source: Source) -> Graph:
    """Строит граф прямых или обратных зависимостей (BFS)."""
    if config.reverse:
        return build_graph(config.package, source.dependents, config.filter)
    return build_graph(config.package, source.dependencies, config.filter)


def title(config: Config) -> str:
    """Формирует заголовок отчета."""
    kind = "Обратные зависимости" if config.reverse else "Граф зависимостей"
    text = f"{kind} {config.package}"
    if not config.test_mode:
        text += f" {config.version}"
    if config.filter:
        text += f" (без пакетов, содержащих {config.filter!r})"
    return text


def summary(config: Config, graph: Graph, source: Source) -> List[str]:
    """Формирует итоговые строки: число пакетов, циклы, пропуски.

    Цикл всегда выводится в направлении «пакет -> его зависимость».
    """
    lines = [f"Пакетов в графе: {len(graph)}"]
    for cycle in find_cycles(graph, config.package):
        if config.reverse:
            cycle = cycle[::-1]
        lines.append("Циклическая зависимость: " + " -> ".join(cycle))
    if source.missing:
        missing = ", ".join(sorted(source.missing))
        lines.append(f"Нет в репозитории (без зависимостей): {missing}")
    return lines


def visualize(config: Config, graph: Graph) -> List[str]:
    """Сохраняет описание графа на D2 и строит изображение PNG.

    Raises:
        VisualizationError: ошибка записи файла или утилиты d2.
    """
    source = d2_path(config.output)
    save_text(source, to_d2(graph, config.package, config.reverse))
    render_png(source, config.output)
    return [
        f"Описание графа на D2: {source}",
        f"Изображение графа: {config.output}",
    ]


def run(config: Config, source: Source) -> int:
    """Строит граф, выводит его на D2 и сохраняет изображение."""
    graph = make_graph(config, source)
    if not graph:
        print(f"{title(config)}: пакет исключен фильтром")
        return EXIT_OK
    print(f"{title(config)} (D2):")
    print(to_d2(graph, config.package, config.reverse))
    print(*summary(config, graph, source), sep="\n")
    try:
        print(*visualize(config, graph), sep="\n")
    except VisualizationError as error:
        print(f"Ошибка визуализации: {error}", file=sys.stderr)
        return EXIT_FAILURE
    return EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    """Запускает приложение.

    Args:
        argv: аргументы командной строки; None - использовать sys.argv.

    Returns:
        Код возврата процесса: 0 - успех, 1 - ошибка.
    """
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as error:
        for message in error.messages:
            print(f"Ошибка конфигурации: {message}", file=sys.stderr)
        return EXIT_FAILURE
    try:
        source = make_source(config)
    except RepositoryError as error:
        print(f"Ошибка репозитория: {error}", file=sys.stderr)
        return EXIT_FAILURE
    return run(config, source)


if __name__ == "__main__":
    sys.exit(main())
