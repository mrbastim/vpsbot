#!/usr/bin/env python3
import os
import re
import sys

TOKEN_RE = re.compile(r"^\d+:[A-Za-z0-9_-]{30,}$")

config_file = "config.py"

if os.path.exists(config_file):
    print(f"файл config '{config_file}' уже существует.")
    sys.exit(0)

print("Настройка проекта: создание файла config.py")
api_token = input("Введите API Token бота: ").strip()
if not TOKEN_RE.match(api_token):
    print("Не похоже на токен Telegram-бота (ожидается `<цифры>:<35+ символов>`).")
    sys.exit(1)

admin_ids = input("Введите ID администраторов (через запятую): ").strip()
admin_list = []
for raw in admin_ids.split(","):
    value = raw.strip()
    if not value:
        continue
    if not value.lstrip("-").isdigit():
        print(f"Некорректный Telegram-ID: {value!r}")
        sys.exit(1)
    admin_list.append(value)

if not admin_list:
    print("Нужен хотя бы один администратор.")
    sys.exit(1)


def _py(value: str) -> str:
    return repr(value)


with open(config_file, "w", encoding="utf-8") as f:
    f.write("# Файл конфигурации, созданный setup_config.py. Не добавляйте в VCS.\n")
    f.write(f"API_TOKEN = {_py(api_token)}\n")
    f.write(f"ADMIN_IDS = {admin_list!r}\n")
    f.write("path_pc_global = '/root'\n")

print(f"Файл '{config_file}' успешно создан.")
