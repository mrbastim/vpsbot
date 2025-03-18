import os
from config import path_pc_global
from aiogram import Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.system_info import send_system_info


callbacks_router = Router()

@callbacks_router.callback_query(F.data == "list_files")
async def listfiles_markup(call: CallbackQuery):
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


@callbacks_router.callback_query(lambda call: call.data.startswith(("file_", "dir_", "back")))
async def handle_callback(call: CallbackQuery):
    chat_id = call.message.chat.id
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
    await send_system_info(await call.message.answer("Получение информации..."))


