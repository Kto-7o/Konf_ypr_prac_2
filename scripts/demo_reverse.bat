@echo off
REM Демонстрация этапа 4: обратные зависимости на тестовых репозиториях
REM и в репозитории Ubuntu (для последнего нужен интернет)
chcp 65001 >nul
for %%f in (configs\reverse_*.yaml) do (
    echo == %%f ==
    python src\main.py --config %%f
)
pause
