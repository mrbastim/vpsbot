import os

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import path_pc_global
from keyboards import (build_files_keyboard, build_service_actions_keyboard,
                       build_services_list_keyboard, build_startup_markup,
                       sysinfo_menu)
from utils.admin_service import AdminService
from states import AdminStates  # импорт состояний для FSM
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
        await call.message.answer(f"Error \- `{err}`", parse_mode="MarkdownV2")
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
                f"Error \- `{err}`", parse_mode="MarkdownV2"
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
            await call.message.answer(f"Error \- `{err}`", parse_mode="MarkdownV2")
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
                f"Error \- `{err}`", parse_mode="MarkdownV2"
            )
            await call.answer()
    elif data == "back_to_main":
        builder = build_startup_markup()
        await call.message.edit_text(
            text="Главное меню",
            reply_markup=builder.as_markup()
        )
        await call.answer()

@callbacks_router.callback_query(lambda c: c.data == 'commands')
async def process_commands_callback(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer(
        "Available Commands:\n`/start` \n`/files` \(`list 'Path'`; `get 'Path'`\)",
        parse_mode="MarkdownV2"
    )

@callbacks_router.callback_query(lambda c: c.data == 'list_files')
async def process_list_files_callback(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        builder = build_files_keyboard(path_pc_global, path_pc_global)
        path = f"Path: \t`{path_pc_global}`"
        await callback_query.message.answer(
            path, 
            reply_markup=builder.as_markup(), 
            parse_mode="MarkdownV2"
        )

    except Exception as err:
        await callback_query.message.answer(
            f"Error \- `{err}`", parse_mode="MarkdownV2"
        )

@callbacks_router.callback_query(lambda c: c.data == 'system_info')
async def process_running_processes_callback(callback_query: CallbackQuery):
    await send_system_info(await callback_query.message.answer("Получение информации..."))

@callbacks_router.callback_query(lambda c: c.data == 'services_status')
async def process_services_status_callback(callback_query: CallbackQuery):
    await callback_query.answer("Получение списка сервисов...")
    servers = await ServiceManager.get_servers()  # Получаем список сервисов
    keyboard = build_services_list_keyboard(servers)
    text = "Выберите сервис для управления:"
    await callback_query.message.edit_text(text, reply_markup=keyboard.as_markup())

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

@callbacks_router.message(F.document)
async def handle_docs_photo(message: Message):
    try:
        file_info = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        filepath = os.path.join(path_pc_global, message.document.file_name)

        with open(filepath, 'wb') as new_file:
            new_file.write(downloaded_file)

        await message.reply(f"Saved in {path_pc_global}")
    except Exception as e:
        await message.reply(f"Error \- `{e}`", parse_mode="MarkdownV2")

@callbacks_router.callback_query(F.data == "system_info")
async def running_processes_handler(call: CallbackQuery, state: FSMContext):
    await send_system_info(await call.message.edit_text("Получение информации..."))

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

