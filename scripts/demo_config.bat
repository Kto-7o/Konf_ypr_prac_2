@echo off
REM Демонстрация этапа 1: вывод параметров и обработка ошибок конфигурации
chcp 65001 >nul
echo == корректная конфигурация ==
python src\main.py --config config.yaml
echo код возврата: %errorlevel%

echo == файл конфигурации не найден ==
python src\main.py --config no_such_config.yaml
echo код возврата: %errorlevel%

for %%f in (configs\errors\*.yaml) do (
    echo == %%f ==
    python src\main.py --config %%f
)
pause
