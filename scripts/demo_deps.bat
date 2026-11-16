@echo off
REM Демонстрация этапа 2: прямые зависимости пакетов из репозитория Ubuntu
chcp 65001 >nul
for %%f in (config.yaml configs\git.yaml configs\errors\unknown_version.yaml configs\errors\unknown_package.yaml configs\errors\bad_url.yaml) do (
    echo == %%f ==
    python src\main.py --config %%f
)
pause
