import asyncio
import os
import subprocess
import logging
import psutil
from psutil._common import bytes2human

from aiogram import Bot, Dispatcher, types, F, html
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile
from aiogram.enums import ParseMode
from typing import Optional

from config import API_TOKEN, ADMIN_ID 

DEBUG = True

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

path_pc_global = "/root" 

class ProcessesPageCallback(CallbackData, prefix="processes_page"):
    page: int
    message_id: Optional[int] = None

async def send_startup_message(dp: Dispatcher):
    builder = InlineKeyboardBuilder()
    builder.button(text="Commands", callback_data="commands")
    builder.button(text="List files", callback_data="list_files")
    builder.button(text="Running processes", callback_data="running_processes")
    builder.adjust(2)
    await bot.send_message(ADMIN_ID, "Bot started", reply_markup=builder.as_markup())


@dp.message(Command('start', 'help'))
async def send_welcome(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Commands", callback_data="commands")
    builder.button(text="List files", callback_data="list_files")
    builder.button(text="System info", callback_data="system_info")
    builder.adjust(2)
    await message.reply("Welcome", reply_markup=builder.as_markup())


@dp.callback_query(F.data == "commands")
async def echo_message(call: types.CallbackQuery):
    await call.message.answer(
        "Available Commands:\n`/start` \n`/files` \(`list 'Path'`; `get 'Path'`\)",
        parse_mode="MarkdownV2",
    )
    await call.answer()


@dp.callback_query(F.data == "list_files")
async def listfiles_markup(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    try:
        entries = os.scandir(path_pc_global)
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
        path = f"Path: \t`{path_pc_global}`"
        await call.message.answer(
            path, reply_markup=builder.as_markup(), parse_mode="MarkdownV2"
        )
        await call.answer()

    except Exception as err:
        await call.message.answer(f"Error \- `{err}`", parse_mode="MarkdownV2")
        await call.answer()


@dp.callback_query(lambda call: call.data.startswith(("file_", "dir_", "back")))
async def handle_callback(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("file_"):
        filename = data.split("_", 1)[1]
        filepath = os.path.join(path_pc_global, filename)
        try:
            file = FSInputFile(filepath, filename=None)
            await bot.send_document(chat_id, file)
        except Exception as err:
            await bot.send_message(
                chat_id, f"Error \- `{err}`", parse_mode="MarkdownV2"
            )
        await call.answer()

    elif data.startswith("dir_"):
        dirname = data.split("_", 1)[1]
        new_path = os.path.join(path_pc_global, dirname)
        try:
            builder = InlineKeyboardBuilder()
            entries = os.scandir(new_path)
            for entry in entries:
                name = entry.name
                if entry.is_dir():
                    name += " | D"
                    callback_data = f"dir_{os.path.relpath(os.path.join(new_path, entry.name), path_pc_global)}"
                elif entry.is_file():
                    name += " | F"
                    callback_data = f"file_{os.path.relpath(os.path.join(new_path, entry.name), path_pc_global)}"
                builder.button(text=name, callback_data=callback_data)
            builder.button(text="Back", callback_data=f"back")
            builder.adjust(2)
            path_text = f"Path: \t`{new_path}`"
            await bot.edit_message_text(
                text=path_text,
                business_connection_id=None,
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=builder.as_markup(),
                parse_mode="MarkdownV2",
            )
            await call.answer()

        except Exception as err:
            await bot.send_message(chat_id, f"Error \- `{err}`", parse_mode="MarkdownV2")
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
            builder = InlineKeyboardBuilder()
            entries = os.scandir(parent_path)
            for entry in entries:
                name = entry.name
                if entry.is_dir():
                    name += " | D"
                    callback_data = f"dir_{os.path.relpath(os.path.join(parent_path, entry.name), path_pc_global)}"
                elif entry.is_file():
                    name += " | F"
                    callback_data = f"file_{os.path.relpath(os.path.join(parent_path, entry.name), path_pc_global)}"
                builder.button(text=name, callback_data=callback_data)

            builder.button(text="Back", callback_data=f"back")
            builder.adjust(2)
            path_text = f"Path: \t`{parent_path}`"
            await bot.edit_message_text(
                text=path_text,
                business_connection_id=None,
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=builder.as_markup(),
                parse_mode="MarkdownV2",
            )
            await call.answer()

        except Exception as err:
            await bot.send_message(
                chat_id, f"Error \- `{err}`", parse_mode="MarkdownV2"
            )
            await call.answer()


@dp.message(Command('files'))
async def files_handler(message: types.Message):
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
            await bot.send_document(message.chat.id, file)
        except Exception as err:
            await message.reply(f"Error \- `{err}`", parse_mode="MarkdownV2")
    else:
        await message.reply("Invalid action. Use 'list' or 'get'.", parse_mode="MarkdownV2")


@dp.message(F.document)
async def handle_docs_photo(message: types.Message):
    try:
        file_info = await bot.get_file(message.document.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        filepath = os.path.join(path_pc_global, message.document.file_name)

        with open(filepath, 'wb') as new_file:
            new_file.write(downloaded_file)

        await message.reply(f"Saved in {path_pc_global}")
    except Exception as e:
        await message.reply(f"Error \- `{e}`", parse_mode="MarkdownV2")



async def send_processes_page(call: types.CallbackQuery, state: FSMContext, page: int = 1):
    try:
        psax = subprocess.run(["ps", "-a", "-x"], capture_output=True, text=True)
        output = psax.stdout

        lines = output.splitlines()
        per_page = 30
        start = (page - 1) * per_page
        end = min(page * per_page, len(lines))

        page_text = "\n".join(lines[start:end])

        builder = InlineKeyboardBuilder()
        if page > 1:
            builder.button(text="Previous", callback_data=ProcessesPageCallback(page=page - 1).pack())
        if end < len(lines):
            builder.button(text="Next", callback_data=ProcessesPageCallback(page=page + 1).pack())
        markup = builder.as_markup()

        message_id = await state.get_data("processes_message_id")

        if message_id:
            try:
                if page_text:
                    await bot.edit_message_text(page_text, call.message.chat.id, message_id, reply_markup=markup)
                else:
                    await bot.edit_message_text("No processes found on this page.", call.message.chat.id, message_id, reply_markup=markup)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    pass  
                else:
                    raise
        else:
            if page_text:
                message = await call.message.answer(page_text, reply_markup=markup)
            else:
                message = await call.message.answer("No processes found on this page.", reply_markup=markup)
            await state.update_data(processes_message_id=message.message_id)



    except Exception as err:
        await call.message.answer(f"Error \- `{err}`", parse_mode="MarkdownV2")


async def send_system_info(message: types.Message):
    try:
        cpu_percent = psutil.cpu_percent(interval=1) 
        ram = psutil.virtual_memory()
        ram_percent = ram.percent 

        system_info = f"""CPU Usage: {cpu_percent}%
RAM Usage: {ram_percent}%
"""
        disk_percent = await disk_usage()
        delimiter = '+' + '-'*40 + '+'
        await bot.edit_message_text(text=f"<pre>{delimiter}\n{system_info}{delimiter}\n{disk_percent}{delimiter}</pre>",
                                    business_connection_id=None,
                                    chat_id=message.chat.id,
                                    message_id=message.message_id,
                                    parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply(f"Error \- `{e}`", parse_mode="MarkdownV2")


@dp.callback_query(F.data == "system_info")
async def running_processes_handler(call: types.CallbackQuery, state: FSMContext):
    await send_system_info(call.message)

async def disk_usage():
    templ = "%-17s %8s %8s %8s %5s%% %9s  %s\n"
    output = templ % ("Device", "Total", "Used", "Free", "Use ", "Type", "Mount")

    for part in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'cdrom' in part.opts or part.fstype == '':
                continue
        usage = psutil.disk_usage(part.mountpoint)
        output += templ % (
            part.device,
            bytes2human(usage.total),
            bytes2human(usage.used),
            bytes2human(usage.free),
            int(usage.percent),
            part.fstype,
            part.mountpoint
        )

    return output

@dp.callback_query(ProcessesPageCallback.filter())
async def processes_page_handler(call: types.CallbackQuery, callback_data: ProcessesPageCallback, state: FSMContext):
    page = callback_data.page
    await send_system_info(call.message)



async def on_shutdown(dispatcher: Dispatcher):
    if not DEBUG:
        try:
            await bot.send_message(ADMIN_ID, "Бот остановлен")
        except Exception as e:
            logging.exception("Ошибка при отправке сообщения об остановке:", exc_info=e)
    await bot.session.close()


async def main():
    if DEBUG:
        print("Бот запущен")
    else:
        await send_startup_message(dp)


    dp.shutdown.register(on_shutdown)

    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")