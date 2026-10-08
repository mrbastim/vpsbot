from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from utils.admin_service import AdminService

DENIED = "❌ У вас нет доступа к этому боту"
ADMIN_ONLY = "❌ Недостаточно прав"


async def _reject(event, text: str) -> None:
    """Отвечает отправителю и снимает «часики» на callback."""
    if isinstance(event, CallbackQuery):
        if event.message:
            await event.message.answer(text)
        await event.answer()
    else:
        await event.answer(text)


class AccessMiddleware(BaseMiddleware):
    """Пускает только пользователей из белого списка."""

    def __init__(self, service: AdminService = None):
        super().__init__()
        self.svc = service or AdminService()

    async def __call__(self, handler, event, data):
        if not self.svc.exists(event.from_user.id):
            await _reject(event, DENIED)
            return
        return await handler(event, data)


class AdminMiddleware(BaseMiddleware):
    """Ограничивает роутер только администраторами."""

    def __init__(self, service: AdminService = None):
        super().__init__()
        self.svc = service or AdminService()

    async def __call__(self, handler, event, data):
        if not self.svc.is_admin(event.from_user.id):
            await _reject(event, ADMIN_ONLY)
            return
        return await handler(event, data)
