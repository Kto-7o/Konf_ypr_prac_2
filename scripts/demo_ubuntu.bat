@echo off
REM Демонстрация этапа 3 на реальном репозитории Ubuntu (нужен интернет)
chcp 65001 >nul
for %%f in (config.yaml configs\curl_filter.yaml configs\git.yaml) do (
    echo == %%f ==
    python src\main.py --config %%f
)
pause
