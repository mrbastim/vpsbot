from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram import Dispatcher
import os
from src.modules.file_manager import list_files, send_file

async def process_commands_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer(
        "Available Commands:\n`/start` \n`/files` \(`list 'Path'`; `get 'Path'`\)",
        parse_mode="MarkdownV2"
    )

async def process_list_files_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    builder = InlineKeyboardBuilder()
    try:
        entries = os.scandir("/root")
        for entry in entries:
            name = entry.name
            if entry.is_dir():
                name += " | D"
                callback_data = f"dir_{entry.name}"
            elif entry.is_file():
                name += " | F"
                callback_data = f"file_{entry.name}"
            builder.button(text=name, callback_data=callback_data)

        builder.adjust(2)
        path = f"Path: \t`/root`"
        await callback_query.message.answer(
            path, 
            reply_markup=builder.as_markup(), 
            parse_mode="MarkdownV2"
        )

    except Exception as err:
        await callback_query.message.answer(f"Error \- `{err}`", parse_mode="MarkdownV2")

async def handle_callback(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("file_"):
        filename = data.split("_", 1)[1]
        await send_file(chat_id, filename)

    elif data.startswith("dir_"):
        dirname = data.split("_", 1)[1]
        await list_files(chat_id, dirname)

    elif data == "back":
        await process_commands_callback(call)