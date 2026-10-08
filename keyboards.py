import os

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from utils.callback_paths import register
from utils.docker_manager import DockerContainer


def _rel(target: str, base: str) -> str:
    """Относительный путь с разделителем `/` (callback_data не зависит от ОС)."""
    return os.path.relpath(target, base).replace(os.sep, "/")


def build_files_keyboard(
    directory: str, base_path: str, add_back: bool = False
) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    entries = sorted(os.scandir(directory), key=lambda e: e.name)

    for entry in entries:
        if entry.is_dir():
            prefix, label = "dir_", f"{entry.name} | D"
        elif entry.is_file():
            prefix, label = "file_", f"{entry.name} | F"
        else:
            continue

        relpath = _rel(os.path.join(directory, entry.name), base_path)
        builder.button(text=label, callback_data=register(prefix, relpath, base_path))

    builder.adjust(2)
    if add_back:
        parent = os.path.dirname(os.path.abspath(directory))
        parent_rel = _rel(parent, os.path.abspath(base_path))
        if parent_rel in (".", "") or not parent_rel.startswith(".."):
            builder.button(
                text="⬆️ Back", callback_data=register("dir_", parent_rel, base_path)
            )
        else:
            builder.button(text="⬆️ Back", callback_data="back_to_main")
    else:
        builder.button(text="Back", callback_data="back_to_main")
    builder.adjust(1)
    return builder


def build_startup_markup() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Commands", callback_data="commands")
    builder.button(text="List files", callback_data="list_files")
    builder.button(text="System info", callback_data="system_info")
    builder.button(text="Services", callback_data="services_status")
    builder.button(text="Docker", callback_data="docker_status")
    builder.adjust(2)
    return builder


def build_services_list_keyboard(services: list) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for service in services:
        builder.button(text=service.name[:40], callback_data=f"service_{service.name}")
    builder.button(text="Назад", callback_data="back_to_main")
    builder.adjust(2)
    return builder


def build_service_actions_keyboard(service_name: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Запустить", callback_data=f"start_{service_name}")
    builder.button(text="Остановить", callback_data=f"stop_{service_name}")
    builder.button(text="Перезапустить", callback_data=f"restart_{service_name}")
    builder.button(text="Назад", callback_data="services_status")
    builder.adjust(2)
    return builder


def build_docker_containers_keyboard(
    containers: list[DockerContainer],
) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for container in containers:
        status_short = container.status[:18]
        builder.button(
            text=f"{container.name} | {status_short}",
            callback_data=f"dcont_{container.id}",
        )
    builder.button(text="Назад", callback_data="back_to_main")
    builder.adjust(1)
    return builder


def build_docker_actions_keyboard(container_id: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Запустить", callback_data=f"dstart_{container_id}")
    builder.button(text="Остановить", callback_data=f"dstop_{container_id}")
    builder.button(text="Перезапустить", callback_data=f"drestart_{container_id}")
    builder.button(text="Назад", callback_data="docker_status")
    builder.adjust(2)
    return builder


sysinfo_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Обновить", callback_data="refresh_sysinfo"),
            InlineKeyboardButton(text="Назад", callback_data="back_to_main"),
        ],
    ]
)
