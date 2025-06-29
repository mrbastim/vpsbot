import datetime
import os
import subprocess

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.admin_service import AdminService

from config import ADMIN_IDS, path_pc_global
from states import AdminStates

commands_router = Router()

@commands_router.message(Command('start', 'help'))
async def send_welcome(message: Message):
    current_hour = datetime.datetime.now().hour
    if current_hour < 12:
        greeting = "Доброе утро"
    elif current_hour < 18:
        greeting = "Добрый день"
    elif current_hour < 22:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"

    builder = InlineKeyboardBuilder()
    builder.button(text="Commands", callback_data="commands")
    builder.button(text="List files", callback_data="list_files")
    builder.button(text="System info", callback_data="system_info")
    builder.button(text="Services", callback_data="services_status")
    builder.adjust(2)
    await message.reply(f"{greeting}, выберите действие", reply_markup=builder.as_markup())

@commands_router.callback_query(F.data == "commands")
async def echo_message(call: CallbackQuery):
    await call.message.answer(
        "Available Commands:\n`/start` \n`/files` \(`list 'Path'`; `get 'Path'`\)\
            \n`/vpn` \(`add [client_name] [password_option]`, `revoke [client_name]` или `list`\)\
            \n`/add_admin` \(`user_id`\)\n",
        parse_mode="MarkdownV2",
    )
    await call.answer()

@commands_router.message(Command('files'))
async def files_handler(message: Message):
    command = message.text.split()
    if len(command) < 2:
        await message.reply("Usage: `/files list [path]` or `/files get [path]`", parse_mode="MarkdownV2")
        return

    action = command[1]
    path = path_pc_global if len(command) == 2 else os.path.join(path_pc_global, command[2])
    if action == "list":
        try:
            entries = os.scandir(path)
            files_list = ""
            for entry in entries:
                file_type = "DIR" if entry.is_dir() else "FILE"
                files_list += f"{file_type}\t\|\t`{entry.name}`\n"
            await message.reply(f"{files_list}Path: \t`{path}`", parse_mode="MarkdownV2")

        except Exception as err:
            await message.reply(f"Error \- `{err}`", parse_mode="MarkdownV2")
    elif action == "get":
        if len(command) < 3:
            await message.reply("Please provide a filename to get.", parse_mode="MarkdownV2")
            return
        filepath = os.path.join(path, command[2])
        try:
            file = FSInputFile(filepath, filename=None)
            await message.reply_document(message.chat.id, file)
        except Exception as err:
            await message.reply(f"Error \- `{err}`", parse_mode="MarkdownV2")
    else:
        await message.reply("Invalid action. Use 'list' or 'get'.", parse_mode="MarkdownV2")

@commands_router.message(Command('vpn'))
async def vpn_handler(message: Message):
    """
    Использование:
      /vpn list
      /vpn add <client_name> [password_option]
      /vpn revoke <client_name>
    """
    args = message.text.split()
    operation = args[1].lower() if len(args) > 1 else None

    if operation == "list":
        # вытягиваем список клиентов через внешний скрипт
        cmd = ["bash", "list-vpn-clients.sh"]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            clients = result.stdout.strip().splitlines()
            if clients:
                msg = "Существующие клиенты VPN:\n" + "\n".join(f"- {c}" for c in clients)
            else:
                msg = "Клиенты VPN не найдены."
            await message.reply(msg)
        except Exception as e:
            await message.reply(f"Ошибка получения списка: {e}")
        return

    if operation == "add":
        client_name = args[2]
        password_option = args[3] if len(args) >= 4 else "1"
        cmd = ["bash", "openvpn-config-tg.sh", "-c", client_name, "-p", password_option]
    elif operation == "revoke":
        client_name = args[2]
        cmd = ["bash", "openvpn-config-tg.sh", "-r", client_name]
    else:
        await message.reply("Неверная команда. Используйте `add` или `revoke`.", parse_mode="MarkdownV2")
        return

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout + "\n" + result.stderr
        if password_option == "1":
            await message.reply(f"<pre>{output}</pre>", parse_mode="HTML")
        else:
            pass
    except Exception as e:
        await message.reply(f"Ошибка выполнения: {e}")

@commands_router.message(Command("add_admin"))
async def cmd_add_admin_start(message: Message, state: FSMContext):
    if str(message.from_user.id) not in ADMIN_IDS:
        return await message.answer("❌ У вас нет прав на добавление админов")
    await state.set_state(AdminStates.waiting_for_user_id)
    await message.answer("Введите Telegram-ID пользователя, которого хотите сделать администратором:")

@commands_router.message(AdminStates.waiting_for_user_id)
async def cmd_add_admin_finish(message: Message, state: FSMContext):
    svc = AdminService()
    try:
        user_id = int(message.text.strip())
    except ValueError:
        return await message.answer("Неверный формат, ожидаю число. Попробуйте ещё раз.")
    added = svc.add(user_id)
    text = "✅ Пользователь добавлен в админы" if added else "ℹ️ Этот пользователь уже в списке"
    await message.answer(text)
    await state.clear()


