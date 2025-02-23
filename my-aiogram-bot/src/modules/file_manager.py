import os
from aiogram.types import FSInputFile

path_pc_global = "/root"

async def list_files(path: str):
    try:
        entries = os.scandir(path)
        files_list = []
        for entry in entries:
            file_type = "DIR" if entry.is_dir() else "FILE"
            files_list.append((file_type, entry.name))
        return files_list
    except Exception as err:
        raise Exception(f"Error listing files: {err}")

async def send_file(chat_id: int, filename: str):
    filepath = os.path.join(path_pc_global, filename)
    try:
        file = FSInputFile(filepath, filename=None)
        await bot.send_document(chat_id, file)
    except Exception as err:
        raise Exception(f"Error sending file: {err}")