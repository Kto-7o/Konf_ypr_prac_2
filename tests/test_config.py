"""Тесты загрузки и проверки конфигурации."""

import pytest

from config import ConfigError, load_config

VALID = {
    "package": "curl",
    "repository": "http://archive.ubuntu.com/ubuntu/Packages.gz",
    "test_mode": "false",
    "version": '"8.5.0-2ubuntu10"',
    "output": "graph.png",
    "filter": '""',
}


def write_config(tmp_path, values):
    """Записывает YAML-файл конфигурации и возвращает путь к нему."""
    path = tmp_path / "config.yaml"
    text = "".join(f"{key}: {value}\n" for key, value in values.items())
    path.write_text(text, encoding="utf-8")
    return str(path)


def errors_for(tmp_path, **changes):
    """Возвращает сообщения об ошибках для измененной конфигурации."""
    values = {**VALID, **changes}
    values = {key: value for key, value in values.items() if value}
    with pytest.raises(ConfigError) as info:
        load_config(write_config(tmp_path, values))
    return info.value.messages


def test_valid_config(tmp_path):
    """Корректная конфигурация загружается полностью."""
    config = load_config(write_config(tmp_path, VALID))
    assert config.package == "curl"
    assert config.test_mode is False
    assert config.version == "8.5.0-2ubuntu10"
    assert config.output == "graph.png"
    assert config.filter == ""


def test_filter_is_optional(tmp_path):
    """Параметр filter можно не указывать."""
    values = {key: value for key, value in VALID.items() if key != "filter"}
    assert load_config(write_config(tmp_path, values)).filter == ""


def test_missing_file(tmp_path):
    """Отсутствующий файл конфигурации - ошибка."""
    with pytest.raises(ConfigError, match="не найден"):
        load_config(str(tmp_path / "nope.yaml"))


def test_bad_yaml(tmp_path):
    """Синтаксическая ошибка YAML - ошибка."""
    path = tmp_path / "bad.yaml"
    path.write_text('package: "curl\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="синтаксиса YAML"):
        load_config(str(path))


def test_not_mapping(tmp_path):
    """Корень документа должен быть словарем."""
    path = tmp_path / "list.yaml"
    path.write_text("- curl\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="ключ: значение"):
        load_config(str(path))


def test_missing_and_unknown(tmp_path):
    """Сообщается о каждом пропущенном и неизвестном параметре."""
    messages = errors_for(tmp_path, version=None, output=None, depth="3")
    assert "неизвестный параметр: depth" in messages
    assert "version: параметр не задан" in messages
    assert "output: параметр не задан" in messages


@pytest.mark.parametrize(
    "key, value, fragment",
    [
        ("package", "42", "ожидается строка"),
        ("package", '"Curl Tool"', "недопустимое имя"),
        ("repository", "ftp://host/x", "схемой http"),
        ("repository", "http:///x", "адрес сервера"),
        ("test_mode", "maybe", "true или false"),
        ("version", "1.0", "кавычки"),
        ("version", "v8", "недопустимая версия"),
        ("output", "graph.svg", ".png"),
        ("output", "no_dir/graph.png", "каталог"),
        ("filter", "[lib]", "ожидается строка"),
    ],
)
def test_bad_values(tmp_path, key, value, fragment):
    """Ошибка в любом параметре обнаруживается и описывается."""
    messages = errors_for(tmp_path, **{key: value})
    assert len(messages) == 1
    assert messages[0].startswith(f"{key}: ")
    assert fragment in messages[0]


def test_all_errors_reported(tmp_path):
    """Сообщается обо всех ошибках сразу."""
    messages = errors_for(tmp_path, package="1", test_mode="1", output="x")
    assert len(messages) == 3


def test_test_mode_rules(tmp_path):
    """В тестовом режиме имя - большие буквы, репозиторий - файл."""
    repo = tmp_path / "repo.txt"
    repo.write_text("A: B\n", encoding="utf-8")
    config = load_config(
        write_config(
            tmp_path,
            {**VALID, "package": "A", "repository": str(repo),
             "test_mode": "true"},
        )
    )
    assert config.test_mode is True
    messages = errors_for(tmp_path, test_mode="true")
    assert any(m.startswith("package: ") for m in messages)
    assert any("не найден" in m for m in messages)
