import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import API_TOKEN, ADMIN_ID
from handlers.commands import commands_router
from handlers.callbacks import callbacks_router
from keyboards import build_startup_markup

DEBUG = False

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(commands_router)
dp.include_router(callbacks_router)


async def send_startup_message(dp: Dispatcher):
    builder = build_startup_markup()
    await bot.send_message(ADMIN_ID, "Bot started", reply_markup=builder.as_markup())

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