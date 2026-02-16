import os

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import path_pc_global
from keyboards import (build_docker_actions_keyboard,
                       build_docker_containers_keyboard, build_files_keyboard,
                       build_service_actions_keyboard,
                       build_services_list_keyboard, build_startup_markup,
                       sysinfo_menu)
from utils.admin_service import AdminService
from states import AdminStates  # импорт состояний для FSM
from utils.docker_manager import DockerContainer, DockerManager
from utils.service_manager import ServiceManager
from utils.system_info import send_system_info

callbacks_router = Router()

@callbacks_router.callback_query(F.data == "list_files")
async def listfiles_markup(call: CallbackQuery):
    try:
        builder = build_files_keyboard(path_pc_global, path_pc_global)
        path = f"Path: \t`{path_pc_global}`"
        await call.message.answer(
            path, reply_markup=builder.as_markup(), parse_mode="MarkdownV2"
        )
        await call.answer()
    except Exception as err:
        await call.message.answer(f"Error \\- `{err}`", parse_mode="MarkdownV2")
        await call.answer()


@callbacks_router.callback_query(lambda call: call.data.startswith(("file_", "dir_", "back")))
async def handle_callback(call: CallbackQuery):
    data = call.data

    if data.startswith("file_"):
        filename = data.split("_", 1)[1]
        filepath = os.path.join(path_pc_global, filename)
        try:
            file = FSInputFile(filepath, filename=None)
            await call.message.answer_document(document=file)
        except Exception as err:
            await call.message.answer(
                f"Error \\- `{err}`", parse_mode="MarkdownV2"
            )
        await call.answer()

    elif data.startswith("dir_"):
        dirname = data.split("_", 1)[1]
        new_path = os.path.join(path_pc_global, dirname)
        try:
            builder = build_files_keyboard(new_path, path_pc_global, add_back=True)
            path_text = f"Path: \t`{new_path}`"
            await call.message.edit_text(
                text=path_text,
                reply_markup=builder.as_markup(),
                parse_mode="MarkdownV2",
            )
            await call.answer()

        except Exception as err:
            await call.message.answer(f"Error \\- `{err}`", parse_mode="MarkdownV2")
            await call.answer()


    elif data == "back":
        current_path_raw = call.message.text.split(' ')
        if len(current_path_raw)<2:
             await call.message.answer("An error has occurred")
             await call.answer()
             return
        current_path = current_path_raw[-1]
        parent_path = os.path.dirname(current_path)

        if parent_path == path_pc_global or parent_path == path_pc_global[:-1]:
            await listfiles_markup(call)
            await call.answer()
            return

        try:
            builder = build_files_keyboard(parent_path, path_pc_global, add_back=True)
            path_text = f"Path: \t`{parent_path}`"
            await call.message.edit_text(
                text=path_text,
                reply_markup=builder.as_markup(),
                parse_mode="MarkdownV2",
            )
            await call.answer()

        except Exception as err:
            await call.message.answer(
                f"Error \\- `{err}`", parse_mode="MarkdownV2"
            )
            await call.answer()
    elif data == "back_to_main":
        builder = build_startup_markup()
        await call.message.edit_text(
            text="Главное меню",
            reply_markup=builder.as_markup()
        )
        await call.answer()

@callbacks_router.callback_query(lambda c: c.data == 'system_info')
async def process_running_processes_callback(callback_query: CallbackQuery):
    await callback_query.answer()
    await send_system_info(await callback_query.message.edit_text("Получение информации..."))

@callbacks_router.callback_query(lambda c: c.data == 'services_status')
async def process_services_status_callback(callback_query: CallbackQuery):
    await callback_query.answer("Получение списка сервисов...")
    servers = await ServiceManager.get_servers()  # Получаем список сервисов
    keyboard = build_services_list_keyboard(servers)
    text = "Выберите сервис для управления:"
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup())


def _find_container_by_prefix(containers: list[DockerContainer], prefix: str) -> DockerContainer | None:
    for container in containers:
        if container.id.startswith(prefix):
            return container
    return None


@callbacks_router.callback_query(lambda c: c.data == 'docker_status')
async def process_docker_status_callback(callback_query: CallbackQuery):
    await callback_query.answer("Получение списка Docker контейнеров...")
    manager = DockerManager()
    containers, err = manager.get_containers(all_containers=True)

    if err:
        await callback_query.message.edit_text(f"Ошибка Docker: {err}")
        return

    if not containers:
        await callback_query.message.edit_text("Docker контейнеры не найдены.")
        return

    keyboard = build_docker_containers_keyboard(containers)
    await callback_query.message.edit_text("Выберите контейнер:", reply_markup=keyboard.as_markup())


@callbacks_router.callback_query(lambda c: c.data.startswith('dcont_'))
async def process_docker_container_detail(callback_query: CallbackQuery):
    container_prefix = callback_query.data.split("dcont_", 1)[1]
    manager = DockerManager()
    containers, err = manager.get_containers(all_containers=True)

    if err:
        await callback_query.message.edit_text(f"Ошибка Docker: {err}")
        await callback_query.answer()
        return

    container = _find_container_by_prefix(containers, container_prefix)
    if not container:
        await callback_query.message.edit_text("Контейнер не найден. Обновите список.")
        await callback_query.answer()
        return

    text = f"Контейнер: {container.name}\nID: {container.id}\nСтатус: {container.status}"
    keyboard = build_docker_actions_keyboard(container.id)
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback_query.answer()


@callbacks_router.callback_query(lambda c: c.data.startswith('dstart_'))
async def process_start_container(callback_query: CallbackQuery):
    container_id = callback_query.data.split("dstart_", 1)[1]
    manager = DockerManager()
    result = manager.start_container(container_id)
    containers, err = manager.get_containers(all_containers=True)
    container = _find_container_by_prefix(containers, container_id) if not err else None

    status_text = container.status if container else "Не удалось определить"
    name_text = container.name if container else container_id
    text = f"Контейнер: {name_text}\nID: {container_id}\nСтатус: {status_text}\n\nРезультат: {result}"
    keyboard = build_docker_actions_keyboard(container_id)
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback_query.answer(result)


@callbacks_router.callback_query(lambda c: c.data.startswith('dstop_'))
async def process_stop_container(callback_query: CallbackQuery):
    container_id = callback_query.data.split("dstop_", 1)[1]
    manager = DockerManager()
    result = manager.stop_container(container_id)
    containers, err = manager.get_containers(all_containers=True)
    container = _find_container_by_prefix(containers, container_id) if not err else None

    status_text = container.status if container else "Не удалось определить"
    name_text = container.name if container else container_id
    text = f"Контейнер: {name_text}\nID: {container_id}\nСтатус: {status_text}\n\nРезультат: {result}"
    keyboard = build_docker_actions_keyboard(container_id)
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback_query.answer(result)


@callbacks_router.callback_query(lambda c: c.data.startswith('drestart_'))
async def process_restart_container(callback_query: CallbackQuery):
    container_id = callback_query.data.split("drestart_", 1)[1]
    manager = DockerManager()
    result = manager.restart_container(container_id)
    containers, err = manager.get_containers(all_containers=True)
    container = _find_container_by_prefix(containers, container_id) if not err else None

    status_text = container.status if container else "Не удалось определить"
    name_text = container.name if container else container_id
    text = f"Контейнер: {name_text}\nID: {container_id}\nСтатус: {status_text}\n\nРезультат: {result}"
    keyboard = build_docker_actions_keyboard(container_id)
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback_query.answer(result)

@callbacks_router.callback_query(lambda c: c.data.startswith('service_'))
async def process_service_detail(callback_query: CallbackQuery):
    service_name = callback_query.data.split("service_", 1)[1]
    manager = ServiceManager(service_name)
    status = manager.get_status()
    text = f"Сервис: {service_name}\nСтатус: {status}"
    keyboard = build_service_actions_keyboard(service_name)
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback_query.answer()

@callbacks_router.callback_query(lambda c: c.data.startswith('start_'))
async def process_start_service(callback_query: CallbackQuery):
    service_name = callback_query.data.split("start_", 1)[1]
    manager = ServiceManager(service_name)
    result = manager.start_service()
    status = manager.get_status()
    text = f"Сервис: {service_name}\nСтатус: {status}\n\nРезультат: {result}"
    keyboard = build_service_actions_keyboard(service_name)
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback_query.answer(result)

@callbacks_router.callback_query(lambda c: c.data.startswith('stop_'))
async def process_stop_service(callback_query: CallbackQuery):
    service_name = callback_query.data.split("stop_", 1)[1]
    manager = ServiceManager(service_name)
    result = manager.stop_service()
    status = manager.get_status()
    text = f"Сервис: {service_name}\nСтатус: {status}\n\nРезультат: {result}"
    keyboard = build_service_actions_keyboard(service_name)
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback_query.answer(result)

@callbacks_router.callback_query(lambda c: c.data.startswith('restart_'))
async def process_restart_service(callback_query: CallbackQuery):
    service_name = callback_query.data.split("restart_", 1)[1]
    manager = ServiceManager(service_name)
    result = manager.restart_service()
    status = manager.get_status()
    text = f"Сервис: {service_name}\nСтатус: {status}\n\nРезультат: {result}"
    keyboard = build_service_actions_keyboard(service_name)
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup())
    await callback_query.answer(result)

UPLOAD_DIR = os.path.join(path_pc_global, "uploads")

@callbacks_router.message(F.document)
async def handle_docs_photo(message: Message):
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filepath = os.path.join(UPLOAD_DIR, message.document.file_name)
        await message.bot.download(message.document, destination=filepath)
        await message.reply(f"Сохранено в {UPLOAD_DIR}")
    except Exception as e:
        await message.reply(f"Error \\- `{e}`", parse_mode="MarkdownV2")

@callbacks_router.callback_query(F.data == "refresh_sysinfo")
async def refresh_sysinfo_handler(call: CallbackQuery):
    await send_system_info(await call.message.edit_text("Получение информации..."))

@callbacks_router.callback_query(F.data == "add_admin")
async def add_admin_handler(call: CallbackQuery, state: FSMContext):
    await call.message.answer(
        "Введите Telegram-ID пользователя, которого хотите сделать администратором:"
    )
    await call.answer()
    await state.set_state(AdminStates.waiting_for_user_id)

@callbacks_router.message(AdminStates.waiting_for_user_id)
async def process_add_admin(message: Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        return await message.answer("❌ Неверный формат, ожидается число. Попробуйте ещё раз.")
    svc = AdminService()
    added = svc.add(user_id)
    text = "✅ Пользователь добавлен в админы" if added else "ℹ️ Этот пользователь уже в списке"
    await message.answer(text)
    await state.clear()

