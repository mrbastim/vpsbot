from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import API_TOKEN, ADMIN_ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def send_startup_message():
    # Implementation for sending startup message to admin
    pass

async def on_shutdown(dispatcher: Dispatcher):
    # Implementation for shutdown procedures
    pass

async def main():
    await send_startup_message()
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())