"""Загрузка и проверка конфигурации из YAML-файла.

Параметры конфигурации:
    package     имя анализируемого пакета;
    repository  URL-адрес репозитория или путь к файлу тестового
                репозитория;
    test_mode   режим работы с тестовым репозиторием (true/false);
    version     версия пакета;
    output      имя файла с изображением графа (PNG);
    filter      подстрока для фильтрации пакетов (необязательный).
"""

import os
import re
from dataclasses import dataclass, fields
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

import yaml

DEFAULT_CONFIG = "config.yaml"
DEFAULTS: Dict[str, Any] = {"filter": ""}
APT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9+.-]+$")
TEST_NAME_RE = re.compile(r"^[A-Z]+$")
VERSION_RE = re.compile(r"^[0-9][0-9A-Za-z.+~:-]*$")
URL_SCHEMES = ("http", "https", "file")
IMAGE_SUFFIX = ".png"


class ConfigError(Exception):
    """Ошибка конфигурации; хранит список сообщений обо всех ошибках."""

    def __init__(self, messages: List[str]):
        """Сохраняет список сообщений об ошибках."""
        super().__init__("\n".join(messages))
        self.messages = messages


@dataclass(frozen=True)
class Config:
    """Параметры, настраиваемые пользователем.

    Attributes:
        package: имя анализируемого пакета.
        repository: URL репозитория или путь к тестовому репозиторию.
        test_mode: True - работа с тестовым репозиторием.
        version: версия пакета.
        output: имя файла с изображением графа.
        filter: подстрока; пакеты, содержащие ее, не учитываются.
    """

    package: str
    repository: str
    test_mode: bool
    version: str
    output: str
    filter: str


PARAMS = tuple(field.name for field in fields(Config))


def _require_string(value: Any) -> Optional[str]:
    """Проверяет, что значение - непустая строка."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"ожидается строка, получено число {value!r} (нужны кавычки)"
    if not isinstance(value, str):
        return f"ожидается строка, получено {type(value).__name__}"
    if not value.strip():
        return "значение не должно быть пустым"
    return None


def _check_package(value: Any, test_mode: bool) -> Optional[str]:
    """Проверяет имя пакета (формат зависит от режима)."""
    error = _require_string(value)
    if error:
        return error
    if test_mode and not TEST_NAME_RE.match(value):
        return (
            f"недопустимое имя {value!r}: в тестовом репозитории "
            "пакеты называются большими латинскими буквами"
        )
    if not test_mode and not APT_NAME_RE.match(value):
        return (
            f"недопустимое имя {value!r}: допускаются строчные "
            "латинские буквы, цифры и символы + . - (от 2 символов)"
        )
    return None


def _check_url(value: str) -> Optional[str]:
    """Проверяет URL-адрес репозитория."""
    parsed = urlparse(value)
    if parsed.scheme not in URL_SCHEMES:
        return f"ожидается URL со схемой http, https или file: {value!r}"
    if parsed.scheme != "file" and not parsed.netloc:
        return f"в URL не указан адрес сервера: {value!r}"
    return None


def _check_repository(value: Any, test_mode: bool) -> Optional[str]:
    """Проверяет URL репозитория или путь к тестовому репозиторию."""
    error = _require_string(value)
    if error:
        return error
    if not test_mode:
        return _check_url(value)
    if not os.path.isfile(value):
        return f"файл тестового репозитория не найден: {value}"
    return None


def _check_test_mode(value: Any, _test_mode: bool) -> Optional[str]:
    """Проверяет режим работы: допускаются только true и false."""
    if not isinstance(value, bool):
        return f"ожидается true или false, получено {value!r}"
    return None


def _check_version(value: Any, _test_mode: bool) -> Optional[str]:
    """Проверяет версию пакета в формате Debian."""
    error = _require_string(value)
    if error:
        return error
    if not VERSION_RE.match(value):
        return (
            f"недопустимая версия {value!r}: начинается с цифры, "
            "далее латинские буквы, цифры и символы . + ~ : -"
        )
    return None


def _check_output(value: Any, _test_mode: bool) -> Optional[str]:
    """Проверяет имя файла изображения графа."""
    error = _require_string(value)
    if error:
        return error
    if not value.lower().endswith(IMAGE_SUFFIX):
        return f"имя файла должно оканчиваться на {IMAGE_SUFFIX}: {value!r}"
    directory = os.path.dirname(value)
    if directory and not os.path.isdir(directory):
        return f"каталог для файла не существует: {directory}"
    return None


def _check_filter(value: Any, _test_mode: bool) -> Optional[str]:
    """Проверяет подстроку фильтрации (может быть пустой)."""
    if value is not None and not isinstance(value, str):
        return f"ожидается строка, получено {type(value).__name__}"
    return None


_CHECKS: Dict[str, Callable[[Any, bool], Optional[str]]] = {
    "package": _check_package,
    "repository": _check_repository,
    "test_mode": _check_test_mode,
    "version": _check_version,
    "output": _check_output,
    "filter": _check_filter,
}


def _read_yaml(path: str) -> Dict[Any, Any]:
    """Читает YAML-файл и возвращает словарь параметров.

    Raises:
        ConfigError: файл не найден, не читается или имеет неверный
            формат.
    """
    try:
        with open(path, encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        raise ConfigError([f"файл конфигурации не найден: {path}"]) from None
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigError([f"не удалось прочитать {path}: {error}"]) from None
    except yaml.YAMLError as error:
        message = f"ошибка синтаксиса YAML в {path}: {error}"
        raise ConfigError([message]) from None
    if not isinstance(data, dict):
        raise ConfigError([f"{path}: ожидается набор строк «ключ: значение»"])
    return data


def _collect_errors(raw: Dict[Any, Any]) -> List[str]:
    """Проверяет все параметры и возвращает список ошибок."""
    errors = [
        f"неизвестный параметр: {key}" for key in raw if key not in PARAMS
    ]
    errors += [
        f"{key}: параметр не задан"
        for key in PARAMS
        if key not in raw and key not in DEFAULTS
    ]
    test_mode = raw.get("test_mode") is True
    for key, check in _CHECKS.items():
        if key in raw:
            message = check(raw[key], test_mode)
            if message:
                errors.append(f"{key}: {message}")
    return errors


def load_config(path: str = DEFAULT_CONFIG) -> Config:
    """Загружает и проверяет конфигурацию.

    Args:
        path: путь к YAML-файлу конфигурации.

    Returns:
        Объект Config с проверенными параметрами.

    Raises:
        ConfigError: со списком всех найденных ошибок.
    """
    raw = _read_yaml(path)
    errors = _collect_errors(raw)
    if errors:
        raise ConfigError(errors)
    values = {key: raw.get(key, DEFAULTS.get(key)) for key in PARAMS}
    if values["filter"] is None:
        values["filter"] = ""
    return Config(**values)


def format_params(config: Config) -> List[str]:
    """Формирует строки «ключ = значение» для всех параметров."""
    lines = []
    for key in PARAMS:
        value = getattr(config, key)
        if isinstance(value, bool):
            value = str(value).lower()
        elif value == "":
            value = "''"
        lines.append(f"{key} = {value}")
    return lines
