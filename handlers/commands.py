import asyncio
import datetime
import html
import os
import re
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS, path_pc_global
from middlewares.access import AdminMiddleware
from states import AdminStates
from utils.admin_service import AdminService
from utils.path_utils import UnsafePathError, safe_join

commands_router = Router()
admin_router = Router()
admin_router.message.middleware(AdminMiddleware())

CLIENT_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
SCRIPT_DIR = Path(__file__).resolve().parent.parent


@commands_router.message(Command("start", "help"))
async def send_welcome(message: Message):
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Доброе утро"
    elif hour < 18:
        greeting = "Добрый день"
    elif hour < 22:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"

    if not AdminService().is_admin(message.from_user.id):
        await message.reply(
            f"{greeting}! У вас базовый доступ к боту. "
            "Команды управления сервером доступны только администраторам."
        )
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="Commands", callback_data="commands")
    builder.button(text="List files", callback_data="list_files")
    builder.button(text="System info", callback_data="system_info")
    builder.button(text="Services", callback_data="services_status")
    builder.button(text="Docker", callback_data="docker_status")
    builder.adjust(2)
    await message.reply(
        f"{greeting}, выберите действие", reply_markup=builder.as_markup()
    )


@commands_router.callback_query(lambda call: call.data == "commands")
async def show_commands(call):
    await call.message.answer(
        "Available Commands:\n"
        "`/start` \n"
        "`/files` \\(`list 'Path'`; `get 'Path'`\\)\n"
        "`/vpn` \\(`add [client_name] [password_option]`, "
        "`revoke [client_name]` или `list`\\)\n"
        "`Docker` \\- управление контейнерами через кнопку в главном меню\n"
        "`/add_admin` \\(`user_id`\\)\n"
        "`/del_admin` \\(`user_id`\\)\n\n"
        "Команды `/files`, `/vpn`, `/add_admin`, `/del_admin` доступны только админам.\n",
        parse_mode="MarkdownV2",
    )
    await call.answer()


def _resolve(rel_path: str) -> str:
    """Путь относительно /root; выход за пределы запрещён."""
    return safe_join(path_pc_global, rel_path or ".")


@admin_router.message(Command("files"))
async def files_handler(message: Message):
    command = message.text.split(maxsplit=2)
    if len(command) < 2:
        await message.reply(
            "Использование: `/files list [path]` или `/files get <path>`",
            parse_mode="MarkdownV2",
        )
        return

    action = command[1]
    try:
        path = _resolve(command[2].strip() if len(command) > 2 else "")
    except UnsafePathError:
        await message.reply("⛔️ Доступ за пределами разрешённой директории запрещён")
        return

    if action == "list":
        try:
            entries = sorted(os.scandir(path), key=lambda e: e.name)
        except OSError as err:
            await message.reply(f"Error \\- `{_md(str(err))}`", parse_mode="MarkdownV2")
            return

        lines = []
        for entry in entries:
            try:
                kind = "DIR" if entry.is_dir() else "FILE"
            except OSError:
                kind = "?"
            lines.append(f"{kind}\t\\|\t`{_md(entry.name)}`")
        listing = "\n".join(lines)
        if len(listing) > 3500:
            listing = listing[:3500] + "\n… (список обрезан)"
        await message.reply(
            f"{listing}\nPath: \t`{_md(path)}`", parse_mode="MarkdownV2"
        )

    elif action == "get":
        try:
            file = FSInputFile(path, filename=os.path.basename(path))
            await message.reply_document(document=file)
        except Exception as err:
            await message.reply(f"Error \\- `{_md(str(err))}`", parse_mode="MarkdownV2")
    else:
        await message.reply(
            "Неверное действие. Используйте `list` или `get`.", parse_mode="MarkdownV2"
        )


def _md(text: str) -> str:
    """Экранирование MarkdownV2 (внутри code entity нужно минимум)."""
    return text.replace("\\", "\\\\").replace("`", "\\`")


@admin_router.message(Command("vpn"))
async def vpn_handler(message: Message):
    """
    Использование:
      /vpn list
      /vpn add <client_name> [password_option]
      /vpn revoke <client_name>
    """
    args = message.text.split()
    operation = args[1].lower() if len(args) > 1 else None

    if operation == "list":
        try:
            proc = await asyncio.create_subprocess_exec(
                "bash",
                str(SCRIPT_DIR / "list-vpn-clients.sh"),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            clients = stdout.strip().splitlines()
            if proc.returncode != 0:
                await message.reply(
                    f"Ошибка получения списка: {stderr.decode(errors='replace').strip()}"
                )
            elif clients:
                await message.reply(
                    "Существующие клиенты VPN:\n" + "\n".join(f"- {c}" for c in clients)
                )
            else:
                await message.reply("Клиенты VPN не найдены.")
        except Exception as e:
            await message.reply(f"Ошибка получения списка: {e}")
        return

    if operation == "add":
        if len(args) < 3:
            await message.reply(
                "Использование: `/vpn add <client_name> [password_option]`",
                parse_mode="MarkdownV2",
            )
            return
        client_name = args[2]
        password_option = args[3] if len(args) >= 4 else "1"
        if not CLIENT_NAME_RE.match(client_name):
            await message.reply(
                "⛔️ Имя клиента: 1–32 символа, только латиница, цифры, `_` и `-`"
            )
            return
        if password_option not in ("1", "2"):
            await message.reply(
                "⛔️ `password_option` \\- только `1` или `2`", parse_mode="MarkdownV2"
            )
            return
        cmd = [
            str(SCRIPT_DIR / "openvpn-config-tg.sh"),
            "-c",
            client_name,
            "-p",
            password_option,
        ]
    elif operation == "revoke":
        if len(args) < 3:
            await message.reply(
                "Использование: `/vpn revoke <client_name>`", parse_mode="MarkdownV2"
            )
            return
        client_name = args[2]
        if not CLIENT_NAME_RE.match(client_name):
            await message.reply(
                "⛔️ Имя клиента: 1–32 символа, только латиница, цифры, `_` и `-`"
            )
            return
        cmd = [str(SCRIPT_DIR / "openvpn-config-tg.sh"), "-r", client_name]
    else:
        await message.reply(
            "Неверная команда. Используйте `add`, `revoke` или `list`.",
            parse_mode="MarkdownV2",
        )
        return

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode(errors="replace") + stderr.decode(errors="replace")
        ok = proc.returncode == 0
        prefix = "" if ok else "⚠️ Код возврата %s\n" % proc.returncode
        await message.reply(
            f"<pre>{html.escape(prefix + output)}</pre>", parse_mode="HTML"
        )
    except Exception as e:
        await message.reply(f"Ошибка выполнения: {e}")


@admin_router.message(Command("add_admin"))
async def cmd_add_admin_start(message: Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_user_id)
    await message.answer(
        "Введите Telegram-ID пользователя, которого хотите сделать администратором:"
    )


@commands_router.message(AdminStates.waiting_for_user_id)
async def cmd_add_admin_finish(message: Message, state: FSMContext):
    svc = AdminService()
    if not svc.is_admin(message.from_user.id):
        await message.answer("❌ Недостаточно прав")
        await state.clear()
        return
    try:
        user_id = int(message.text.strip())
    except (ValueError, AttributeError):
        return await message.answer(
            "Неверный формат, ожидаю число. Попробуйте ещё раз."
        )
    added = svc.add(user_id, is_admin=True)
    text = (
        "✅ Пользователь добавлен в админы"
        if added
        else "ℹ️ Этот пользователь уже в списке"
    )
    await message.answer(text)
    await state.clear()


@commands_router.message(Command("del_admin"))
async def cmd_del_admin(message: Message):
    svc = AdminService()
    if not svc.is_admin(message.from_user.id):
        return await message.answer("❌ Недостаточно прав")
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Использование: `/del_admin <user_id>`")
    try:
        user_id = int(args[1])
    except ValueError:
        return await message.answer("Неверный формат, ожидаю число.")
    if user_id in {int(a) for a in ADMIN_IDS}:
        return await message.answer("❌ Нельзя удалить администратора из config.py")
    removed = svc.remove(user_id)
    await message.answer(
        "✅ Пользователь удалён" if removed else "ℹ️ Пользователь не найден"
    )
