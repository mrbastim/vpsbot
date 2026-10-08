import os
import sys

if not os.path.exists("config.py"):
    print(
        "Предупреждение: файл config.py не найден. Запустите setup_config.py в корне проекта для создания файла конфигурации."
    )
    sys.exit(1)

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from config import ADMIN_IDS, API_TOKEN
from handlers.callbacks import admin_callbacks_router, callbacks_router
from handlers.commands import admin_router, commands_router
from keyboards import build_startup_markup
from middlewares.access import AccessMiddleware
from utils.admin_service import AdminService

DEBUG = False

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

admin_service = AdminService()

dp.message.middleware(AccessMiddleware(admin_service))
dp.callback_query.middleware(AccessMiddleware(admin_service))

dp.include_router(commands_router)
dp.include_router(admin_router)
dp.include_router(callbacks_router)
dp.include_router(admin_callbacks_router)


@dp.errors()
async def error_handler(event: ErrorEvent):
    logging.exception(
        "Необработанная ошибка при обработке апдейта %s: %s",
        event.update.update_id,
        event.exception,
        exc_info=event.exception,
    )


async def send_startup_message(dp: Dispatcher):
    builder = build_startup_markup()
    for admin in ADMIN_IDS:
        await bot.send_message(admin, "Бот запущен", reply_markup=builder.as_markup())


async def on_shutdown(dispatcher: Dispatcher):
    if not DEBUG:
        try:
            for admin in ADMIN_IDS:
                await bot.send_message(admin, "Бот остановлен")
        except Exception:
            logging.exception("Ошибка при отправке сообщения об остановке")
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")
