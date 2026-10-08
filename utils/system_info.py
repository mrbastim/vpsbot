import asyncio
import os

import psutil
from aiogram.enums import ParseMode
from aiogram.types import Message
from keyboards import sysinfo_menu


def _bytes2human(n: int) -> str:
    """Локальная замена приватного psutil._common.bytes2human."""
    symbols = ("B", "K", "M", "G", "T", "P", "E", "Z", "Y")
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols[1:]):
        if n >= prefix[s]:
            value = int(n / prefix[s])
            return f"{value}{s}"
    return f"{int(n)}{symbols[0]}"


async def disk_usage() -> str:
    templ = "%-17s %8s %8s %8s %5s%% %9s  %s\n"
    output = templ % ("Device", "Total", "Used", "Free", "Use ", "Type", "Mount")

    for part in psutil.disk_partitions(all=False):
        if os.name == "nt" and ("cdrom" in part.opts or part.fstype == ""):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        output += templ % (
            part.device,
            _bytes2human(usage.total),
            _bytes2human(usage.used),
            _bytes2human(usage.free),
            int(usage.percent),
            part.fstype,
            part.mountpoint,
        )
    return output


async def send_system_info(message: Message) -> None:
    try:
        psutil.cpu_percent(interval=None)
        await asyncio.sleep(0.2)
        cpu_percent = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        disks = await disk_usage()

        delimiter = "+" + "-" * 40 + "+"
        body = (
            f"CPU Usage: {cpu_percent}%\n"
            f"RAM Usage: {ram.percent}% "
            f"({_bytes2human(ram.used)}/{_bytes2human(ram.total)})\n"
        )
        await message.edit_text(
            text=f"<pre>{delimiter}\n{body}{delimiter}\n{disks}{delimiter}</pre>",
            parse_mode=ParseMode.HTML,
            reply_markup=sysinfo_menu,
        )
    except Exception as e:
        await message.reply(f"Ошибка при сборе информации: {e}")
