"""Тесты точки входа: вывод параметров и коды возврата."""

from main import EXIT_FAILURE, EXIT_OK, main

CONFIG = """\
package: curl
repository: http://archive.ubuntu.com/ubuntu/Packages.gz
test_mode: false
version: "8.5.0"
output: graph.png
"""


def test_prints_all_params(tmp_path, capsys):
    """При запуске выводятся все параметры."""
    path = tmp_path / "config.yaml"
    path.write_text(CONFIG, encoding="utf-8")
    assert main(["--config", str(path)]) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "package = curl"
    assert len(out) == 6


def test_config_error_exit_code(tmp_path, capsys):
    """Ошибки конфигурации выводятся в stderr, код возврата 1."""
    path = tmp_path / "config.yaml"
    path.write_text(CONFIG.replace("curl", "CURL"), encoding="utf-8")
    assert main(["--config", str(path)]) == EXIT_FAILURE
    err = capsys.readouterr().err
    assert err.startswith("Ошибка конфигурации: package: ")
