@echo off
REM Демонстрация этапа 3: граф зависимостей (BFS), фильтр, циклы,
REM режим тестового репозитория
chcp 65001 >nul
for %%f in (configs\test_*.yaml configs\errors\test_*.yaml) do (
    echo == %%f ==
    python src\main.py --config %%f
)
pause
