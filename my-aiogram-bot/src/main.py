from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from config import API_TOKEN
from handlers import register_handlers

async def main():
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    register_handlers(dp)

    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")

if __name__ == '__main__':
    asyncio.run(main())