#!/bin/bash

clear
cd .. || exit 1  # Выход, если cd не удался
path_project="app"

# Форматирование и проверки
echo "=== START ISORT ==="
isort --profile black "$path_project"

echo "=== START BLACK ==="
black "$path_project"

echo "=== START FLAKE8 ==="
flake8 \
    --ignore=E501,W503,E203 \
    --extend-ignore=D100,D104,D105,D107,D205,D400,D200,D301,D202 \
    "$path_project"

echo "=== START MYPY ==="
mypy "$path_project" --strict