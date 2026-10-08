import html
import os

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import path_pc_global
from keyboards import (
    build_docker_actions_keyboard,
    build_docker_containers_keyboard,
    build_files_keyboard,
    build_service_actions_keyboard,
    build_services_list_keyboard,
    build_startup_markup,
)
from middlewares.access import AdminMiddleware
from utils.callback_paths import resolve
from utils.docker_manager import DockerContainer, DockerManager
from utils.path_utils import UnsafePathError, safe_filename, safe_join
from utils.service_manager import ServiceManager
from utils.system_info import send_system_info

callbacks_router = Router()
admin_callbacks_router = Router()
admin_callbacks_router.callback_query.middleware(AdminMiddleware())
admin_callbacks_router.message.middleware(AdminMiddleware())

UPLOAD_DIR = os.path.join(path_pc_global, "uploads")
MAX_UPLOAD_SIZE = 512 * 1024 * 1024


def _md(text: str) -> str:
    """Экранирование MarkdownV2."""
    return text.replace("\\", "\\\\").replace("`", "\\`")


def _resolve_callback(callback_data: str) -> str:
    """Путь по callback_data (в т.ч. токены для длинных путей)."""
    return resolve(callback_data, path_pc_global)


@admin_callbacks_router.callback_query(F.data == "list_files")
async def listfiles_markup(call: CallbackQuery):
    try:
        builder = build_files_keyboard(path_pc_global, path_pc_global)
        text = f"Path: \t`{_md(path_pc_global)}`"
    except OSError as err:
        await call.message.answer(
            f"Error \\- `{_md(str(err))}`", parse_mode="MarkdownV2"
        )
        await call.answer()
        return

    try:
        await call.message.edit_text(
            text, reply_markup=builder.as_markup(), parse_mode="MarkdownV2"
        )
    except Exception:
        # Клавиатура была на другом сообщении — отправляем новое.
        await call.message.answer(
            text, reply_markup=builder.as_markup(), parse_mode="MarkdownV2"
        )
    await call.answer()


async def _show_dir(call: CallbackQuery, path: str, add_back: bool) -> None:
    builder = build_files_keyboard(path, path_pc_global, add_back=add_back)
    await call.message.edit_text(
        text=f"Path: \t`{_md(path)}`",
        reply_markup=builder.as_markup(),
        parse_mode="MarkdownV2",
    )


@admin_callbacks_router.callback_query(
    lambda call: call.data.startswith(("file_", "dir_"))
)
async def handle_callback(call: CallbackQuery):
    data = call.data

    if data.startswith("file_"):
        try:
            filepath = _resolve_callback(data)
            file = FSInputFile(filepath, filename=os.path.basename(filepath))
            await call.message.answer_document(document=file)
        except UnsafePathError:
            await call.message.answer("⛔️ Доступ за пределами /root запрещён")
        except Exception as err:
            await call.message.answer(
                f"Error \\- `{_md(str(err))}`", parse_mode="MarkdownV2"
            )
        await call.answer()
        return

    if data.startswith("dir_"):
        try:
            await _show_dir(call, _resolve_callback(data), add_back=True)
        except UnsafePathError:
            await call.message.answer("⛔️ Доступ за пределами /root запрещён")
        except Exception as err:
            await call.message.answer(
                f"Error \\- `{_md(str(err))}`", parse_mode="MarkdownV2"
            )
        await call.answer()


@callbacks_router.callback_query(F.data == "back_to_main")
async def back_to_main(call: CallbackQuery):
    await call.message.edit_text(
        text="Главное меню", reply_markup=build_startup_markup().as_markup()
    )
    await call.answer()


@admin_callbacks_router.callback_query(F.data == "system_info")
async def process_system_info_callback(call: CallbackQuery):
    await call.answer()
    await send_system_info(await call.message.edit_text("Получение информации..."))


@admin_callbacks_router.callback_query(F.data == "refresh_sysinfo")
async def refresh_sysinfo_handler(call: CallbackQuery):
    await call.answer()
    await send_system_info(await call.message.edit_text("Получение информации..."))


@admin_callbacks_router.callback_query(F.data == "services_status")
async def process_services_status_callback(call: CallbackQuery):
    await call.answer("Получение списка сервисов...")
    servers = await ServiceManager.get_servers()
    keyboard = build_services_list_keyboard(servers)
    await call.message.edit_text(
        "Выберите сервис для управления:", reply_markup=keyboard.as_markup()
    )


def _find_container_by_prefix(
    containers: list[DockerContainer], prefix: str
) -> DockerContainer | None:
    for container in containers:
        if container.id.startswith(prefix):
            return container
    return None


@admin_callbacks_router.callback_query(F.data == "docker_status")
async def process_docker_status_callback(call: CallbackQuery):
    await call.answer("Получение списка Docker контейнеров...")
    containers, err = await DockerManager().get_containers(all_containers=True)

    if err:
        await call.message.edit_text(f"Ошибка Docker: {html.escape(err)}")
        return
    if not containers:
        await call.message.edit_text("Docker контейнеры не найдены.")
        return
    await call.message.edit_text(
        "Выберите контейнер:",
        reply_markup=build_docker_containers_keyboard(containers).as_markup(),
    )


@admin_callbacks_router.callback_query(F.data.startswith("dcont_"))
async def process_docker_container_detail(call: CallbackQuery):
    container_prefix = call.data.split("dcont_", 1)[1]
    containers, err = await DockerManager().get_containers(all_containers=True)

    if err:
        await call.message.edit_text(f"Ошибка Docker: {html.escape(err)}")
        await call.answer()
        return
    container = _find_container_by_prefix(containers, container_prefix)
    if not container:
        await call.message.edit_text("Контейнер не найден. Обновите список.")
        await call.answer()
        return
    await call.message.edit_text(
        f"Контейнер: {html.escape(container.name)}\n"
        f"ID: {container.id}\nСтатус: {html.escape(container.status)}",
        reply_markup=build_docker_actions_keyboard(container.id).as_markup(),
        parse_mode="HTML",
    )
    await call.answer()


async def _docker_action(call: CallbackQuery, container_id: str, action) -> None:
    result = await action(container_id)
    containers, err = await DockerManager().get_containers(all_containers=True)
    container = _find_container_by_prefix(containers, container_id) if not err else None

    status_text = (
        html.escape(container.status) if container else "Не удалось определить"
    )
    name_text = html.escape(container.name) if container else container_id
    await call.message.edit_text(
        text=f"Контейнер: {name_text}\nID: {container_id}\n"
        f"Статус: {status_text}\n\nРезультат: {html.escape(result)}",
        reply_markup=build_docker_actions_keyboard(container_id).as_markup(),
        parse_mode="HTML",
    )
    await call.answer(result[:200])


@admin_callbacks_router.callback_query(F.data.startswith("dstart_"))
async def process_start_container(call: CallbackQuery):
    manager = DockerManager()
    await _docker_action(
        call, call.data.split("dstart_", 1)[1], manager.start_container
    )


@admin_callbacks_router.callback_query(F.data.startswith("dstop_"))
async def process_stop_container(call: CallbackQuery):
    manager = DockerManager()
    await _docker_action(call, call.data.split("dstop_", 1)[1], manager.stop_container)


@admin_callbacks_router.callback_query(F.data.startswith("drestart_"))
async def process_restart_container(call: CallbackQuery):
    manager = DockerManager()
    await _docker_action(
        call, call.data.split("drestart_", 1)[1], manager.restart_container
    )


@admin_callbacks_router.callback_query(F.data.startswith("service_"))
async def process_service_detail(call: CallbackQuery):
    try:
        service_name = call.data.split("service_", 1)[1]
        manager = ServiceManager(service_name)
        status = await manager.get_status()
    except ValueError as err:
        await call.message.edit_text(
            f"Ошибка: {html.escape(str(err))}", parse_mode="HTML"
        )
        await call.answer()
        return

    await call.message.edit_text(
        text=f"Сервис: {html.escape(service_name)}\nСтатус: {html.escape(status)}",
        reply_markup=build_service_actions_keyboard(service_name).as_markup(),
        parse_mode="HTML",
    )
    await call.answer()


async def _service_action(call: CallbackQuery, service_name: str, action) -> None:
    try:
        manager = ServiceManager(service_name)
    except ValueError as err:
        await call.message.edit_text(
            f"Ошибка: {html.escape(str(err))}", parse_mode="HTML"
        )
        await call.answer()
        return

    result = await action()
    status = await manager.get_status()
    await call.message.edit_text(
        text=f"Сервис: {html.escape(service_name)}\nСтатус: {html.escape(status)}\n\n"
        f"Результат: {html.escape(result)}",
        reply_markup=build_service_actions_keyboard(service_name).as_markup(),
        parse_mode="HTML",
    )
    await call.answer(result[:200])


async def _service_action_from_call(
    call: CallbackQuery, marker: str, verb: str
) -> None:
    name = call.data.split(marker, 1)[1]
    await _service_action(call, name, lambda: _dispatch_service(name, verb))


async def _dispatch_service(name: str, verb: str) -> str:
    manager = ServiceManager(name)
    return await {
        "start": manager.start_service,
        "stop": manager.stop_service,
        "restart": manager.restart_service,
    }[verb]()


@admin_callbacks_router.callback_query(F.data.startswith("start_"))
async def process_start_service(call: CallbackQuery):
    await _service_action_from_call(call, "start_", "start")


@admin_callbacks_router.callback_query(F.data.startswith("stop_"))
async def process_stop_service(call: CallbackQuery):
    await _service_action_from_call(call, "stop_", "stop")


@admin_callbacks_router.callback_query(F.data.startswith("restart_"))
async def process_restart_service(call: CallbackQuery):
    await _service_action_from_call(call, "restart_", "restart")


@admin_callbacks_router.message(F.document)
async def handle_document_upload(message: Message):
    document = message.document
    try:
        name = safe_filename(document.file_name)
    except UnsafePathError:
        await message.answer("⛔️ Недопустимое имя файла")
        return

    if document.file_size and document.file_size > MAX_UPLOAD_SIZE:
        await message.answer(f"⛔️ Файл больше {MAX_UPLOAD_SIZE // (1024 * 1024)} МБ")
        return

    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filepath = safe_join(UPLOAD_DIR, name)
        await message.bot.download(document, destination=filepath)
        await message.answer(
            f"✅ Сохранено в `{_md(UPLOAD_DIR)}`\n`{_md(filepath)}`",
            parse_mode="MarkdownV2",
        )
    except Exception as e:
        await message.answer(f"Error \\- `{_md(str(e))}`", parse_mode="MarkdownV2")
