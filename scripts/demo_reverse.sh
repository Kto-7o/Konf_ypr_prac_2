#!/bin/bash
# Демонстрация этапа 4: обратные зависимости на тестовых репозиториях
# и в репозитории Ubuntu (для последнего нужен интернет)
for file in configs/reverse_simple.yaml configs/reverse_complex.yaml \
        configs/reverse_filter.yaml configs/reverse_cycles.yaml \
        configs/reverse_missing.yaml configs/reverse_ubuntu.yaml; do
    echo "== $file =="
    python3 src/main.py --config "$file"
    echo "код возврата: $?"
done
