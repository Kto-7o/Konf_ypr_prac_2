"""Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).

Точка входа. Загружает конфигурацию из YAML-файла, получает из
репозитория Ubuntu описание заданной версии пакета и выводит на экран
все его прямые зависимости.

Пример запуска:
    python3 src/main.py --config config.yaml
"""

import argparse
import sys
from typing import List, Optional

from apt_repo import (
    RepositoryError,
    direct_dependencies,
    find_package,
    load_index,
)
from config import DEFAULT_CONFIG, Config, ConfigError, load_config

EXIT_OK = 0
EXIT_FAILURE = 1


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


def show_direct_dependencies(config: Config) -> None:
    """Выводит прямые зависимости пакета из репозитория Ubuntu.

    Raises:
        RepositoryError: репозиторий недоступен, пакет или версия
            не найдены.
    """
    if config.test_mode:
        raise RepositoryError(
            "режим тестового репозитория поддерживается начиная с этапа 3"
        )
    index = load_index(config.repository)
    fields = find_package(index, config.package, config.version)
    dependencies = direct_dependencies(fields)
    print(f"Прямые зависимости {config.package} {config.version}:")
    if not dependencies:
        print("  (нет зависимостей)")
    for dependency in dependencies:
        print(f"  {dependency.text}")


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
        show_direct_dependencies(config)
    except RepositoryError as error:
        print(f"Ошибка репозитория: {error}", file=sys.stderr)
        return EXIT_FAILURE
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
