#!/bin/bash
# Демонстрация этапа 3 на реальном репозитории Ubuntu (нужен интернет)
for file in config.yaml configs/curl_filter.yaml configs/git.yaml; do
    echo "== $file =="
    python3 src/main.py --config "$file"
    echo "код возврата: $?"
done
