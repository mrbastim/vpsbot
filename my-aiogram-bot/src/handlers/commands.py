from aiogram import types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os

from src.config import ADMIN_ID
from src.modules.file_manager import list_files, get_file

path_pc_global = "/root"

async def send_welcome(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Commands", callback_data="commands")
    builder.button(text="List files", callback_data="list_files")
    builder.button(text="System info", callback_data="system_info")
    builder.adjust(2)
    await message.reply("Welcome", reply_markup=builder.as_markup())

@dp.message(Command('start', 'help'))
async def start_command_handler(message: types.Message):
    await send_welcome(message)

@dp.message(Command('files'))
async def files_command_handler(message: types.Message):
    command = message.text.split()
    if len(command) < 2:
        await message.reply("Usage: `/files list [path]` or `/files get [path]`", parse_mode="MarkdownV2")
        return

    action = command[1]
    path = path_pc_global if len(command) == 2 else os.path.join(path_pc_global, command[2])

    if action == "list":
        await list_files(message, path)
    elif action == "get":
        if len(command) < 3:
            await message.reply("Please provide a filename to get.", parse_mode="MarkdownV2")
            return
        await get_file(message, path, command[2])
    else:
        await message.reply("Invalid action. Use 'list' or 'get'.", parse_mode="MarkdownV2")