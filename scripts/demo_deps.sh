#!/bin/bash
# Демонстрация этапа 2: прямые зависимости пакетов из репозитория Ubuntu
for file in config.yaml configs/git.yaml configs/errors/unknown_version.yaml \
        configs/errors/unknown_package.yaml configs/errors/bad_url.yaml; do
    echo "== $file =="
    python3 src/main.py --config "$file"
    echo "код возврата: $?"
done
