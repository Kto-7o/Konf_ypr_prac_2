#!/bin/bash
# Демонстрация этапа 3: граф зависимостей (BFS), фильтр, циклы,
# режим тестового репозитория
for file in configs/test_simple.yaml configs/test_cycles.yaml \
        configs/test_cycle_inner.yaml configs/test_complex.yaml \
        configs/test_filter.yaml configs/test_filter_root.yaml \
        configs/errors/test_no_package.yaml \
        configs/errors/test_broken_repo.yaml; do
    echo "== $file =="
    python3 src/main.py --config "$file"
    echo "код возврата: $?"
done
