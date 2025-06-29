from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from services.admin_service import AdminService


class AccessMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.svc = AdminService()

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        if not self.svc.exists(user_id):
            text = "❌ У вас нет доступа к этому боту"
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(text)
            return
        return await handler(event, data)
