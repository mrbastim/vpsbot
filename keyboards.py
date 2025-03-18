import os
from aiogram.utils.keyboard import InlineKeyboardBuilder

def build_files_keyboard(directory: str, base_path: str, add_back: bool = False) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    try:
        entries = os.scandir(directory)
        for entry in entries:
            if entry.is_dir():
                callback_data = f"dir_{os.path.relpath(os.path.join(directory, entry.name), base_path)}"
                text = f"{entry.name} | D"
            elif entry.is_file():
                callback_data = f"file_{os.path.relpath(os.path.join(directory, entry.name), base_path)}"
                text = f"{entry.name} | F"
            builder.button(text=text, callback_data=callback_data)
        if add_back:
            builder.button(text="Back", callback_data="back")
        else:
            builder.button(text="Back", callback_data="back_to_main")
        builder.adjust(2)
    except Exception as err:
        raise err
    return builder

def build_startup_markup() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Commands", callback_data="commands")
    builder.button(text="List files", callback_data="list_files")
    builder.button(text="System info", callback_data="system_info")
    builder.button(text="Services", callback_data="services_status")  # Новая кнопка для мониторинга сервисов
    builder.adjust(2)
    return builder

def build_services_list_keyboard(services: list) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for service in services:
        builder.button(text=service.name, callback_data=f"service_{service.name}")
    builder.button(text="Назад", callback_data="back_to_main")
    builder.adjust(2)
    return builder

def build_service_actions_keyboard(service_name: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Запустить", callback_data=f"start_{service_name}")
    builder.button(text="Остановить", callback_data=f"stop_{service_name}")
    builder.button(text="Назад", callback_data="services_status")
    builder.adjust(2)
    return builder
