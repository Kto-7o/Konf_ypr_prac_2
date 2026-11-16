@echo off
REM Запуск визуализатора в Windows; параметры передаются дальше:
REM   run.bat --config config.yaml
chcp 65001 >nul
python src\main.py %*
