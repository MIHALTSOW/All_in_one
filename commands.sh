#!/bin/bash

echo "Установка зависимостей"
pip install -r requirements.txt
pip freeze > requirements.txt

echo "JWT токен"
pip install "passlib[bcrypt]"    # установка библиотеки passlib
openssl rand -hex 32    # генерация секретного ключа

echo "Env файл"
pip install python-dotenv

python3 -m pip install types-passlib    # установка типов passlib








