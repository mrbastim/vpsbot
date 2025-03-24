import os
import datetime
import subprocess
from config import path_pc_global
from aiogram import Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import Command

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
        "Available Commands:\n`/start` \n`/files` \(`list 'Path'`; `get 'Path'`\)\n`/vpn` \(`add [client_name] [password_option]` или `revoke [client_name]`\)",
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
      /vpn add <client_name> [password_option]
      /vpn revoke <client_name>
    Если password_option не указан, по умолчанию используется значение 1 (без пароля).
    """
    args = message.text.split()
    if len(args) < 3:
        await message.reply("Использование:\n Для добавления: `/vpn add <client_name> [password_option]`\n \
                            Для отзыва: `/vpn revoke <client_name>`\n \
                            Опция пароля для нового клиента (1 - без пароля, 2 - с паролем)", 
                            parse_mode="MarkdownV2")
        return

    operation = args[1].lower()
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
