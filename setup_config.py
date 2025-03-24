#!/usr/bin/env python3
import os

config_file = "config.py"

if os.path.exists(config_file):
    print(f"файл config '{config_file}' уже существует.")
    exit(0)

print("Настройка проекта: создание файла config.py")
api_token = input("Введите API Token бота: ").strip()
admin_ids = input("Введите ID администраторов (через запятую): ").strip()

# Преобразуем строку ID в список
admin_list = [admin.strip() for admin in admin_ids.split(",") if admin.strip()]

with open(config_file, "w") as f:
    f.write("# Файл конфигурации, созданный setup.py. Не добавляйте в систему контроля версий.\n")
    f.write(f"API_TOKEN = '{api_token}'\n")
    f.write(f"ADMIN_IDS = {admin_list}\n")
    f.write("path_pc_global = '/root'\n")

print(f"Файл '{config_file}' успешно создан.")