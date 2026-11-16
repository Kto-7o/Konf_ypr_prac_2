"""Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).

Точка входа. Загружает конфигурацию из YAML-файла, строит граф
зависимостей заданного пакета (с учетом транзитивности) обходом в
ширину и выводит его на экран вместе с найденными циклами.
Источник данных - репозиторий Ubuntu или тестовый репозиторий.

Пример запуска:
    python3 src/main.py --config config.yaml
"""

import argparse
import sys
from typing import List, Optional, Union

from apt_repo import AptSource, RepositoryError, load_index
from config import DEFAULT_CONFIG, Config, ConfigError, load_config
from graph import Graph, build_graph, find_cycles, format_graph
from local_repo import LocalSource, load_local_repo

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


def report(config: Config, graph: Graph, source: Source) -> List[str]:
    """Формирует текстовый отчет о графе зависимостей."""
    title = config.package
    if not config.test_mode:
        title += f" {config.version}"
    if config.filter:
        title += f" (без пакетов, содержащих {config.filter!r})"
    if not graph:
        return [f"Граф зависимостей {title}: пакет исключен фильтром"]
    lines = [f"Граф зависимостей {title}:"] + format_graph(graph)
    lines.append(f"Пакетов в графе: {len(graph)}")
    cycles = find_cycles(graph, config.package)
    for cycle in cycles:
        lines.append("Циклическая зависимость: " + " -> ".join(cycle))
    if not cycles:
        lines.append("Циклических зависимостей нет")
    if source.missing:
        missing = ", ".join(sorted(source.missing))
        lines.append(f"Нет в репозитории (без зависимостей): {missing}")
    return lines


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
    graph = build_graph(config.package, source.dependencies, config.filter)
    print(*report(config, graph, source), sep="\n")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
