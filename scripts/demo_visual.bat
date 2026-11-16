@echo off
REM Демонстрация этапа 5: описание графа на D2 и изображения PNG для
REM трех пакетов Ubuntu (curl, wget, nano) и двух тестовых репозиториев.
REM Нужны интернет и утилита d2 (https://d2lang.com/tour/install).
chcp 65001 >nul
for %%f in (configs\visual_*.yaml) do (
    echo == %%f ==
    python src\main.py --config %%f
)
dir examples
pause
