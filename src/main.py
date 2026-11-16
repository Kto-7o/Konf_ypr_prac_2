"""Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).

Точка входа. Загружает конфигурацию из YAML-файла и выводит все
параметры, настраиваемые пользователем, в формате «ключ = значение».

Пример запуска:
    python3 src/main.py --config config.yaml
"""

import argparse
import sys
from typing import List, Optional

from config import DEFAULT_CONFIG, ConfigError, format_params, load_config

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


def main(argv: Optional[List[str]] = None) -> int:
    """Запускает приложение.

    Args:
        argv: аргументы командной строки; None - использовать sys.argv.

    Returns:
        Код возврата процесса: 0 - успех, 1 - ошибка конфигурации.
    """
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as error:
        for message in error.messages:
            print(f"Ошибка конфигурации: {message}", file=sys.stderr)
        return EXIT_FAILURE
    print(*format_params(config), sep="\n")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
