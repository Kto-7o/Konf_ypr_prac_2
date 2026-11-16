#!/bin/bash
# Демонстрация этапа 1: вывод параметров и обработка ошибок конфигурации
echo "== корректная конфигурация =="
python3 src/main.py --config config.yaml
echo "код возврата: $?"

echo "== файл конфигурации не найден =="
python3 src/main.py --config no_such_config.yaml
echo "код возврата: $?"

for file in configs/errors/*.yaml; do
    echo "== $file =="
    python3 src/main.py --config "$file"
    echo "код возврата: $?"
done
