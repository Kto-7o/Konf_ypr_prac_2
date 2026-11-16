#!/bin/bash
# Демонстрация этапа 5: описание графа на D2 и изображения PNG для
# трех пакетов Ubuntu (curl, wget, nano) и двух тестовых репозиториев.
# Нужны интернет и утилита d2 (https://d2lang.com/tour/install).
for file in configs/visual_curl.yaml configs/visual_wget.yaml \
        configs/visual_nano.yaml configs/visual_test_cycles.yaml \
        configs/visual_test_reverse.yaml; do
    echo "== $file =="
    python3 src/main.py --config "$file"
    echo "код возврата: $?"
done
ls -l examples
