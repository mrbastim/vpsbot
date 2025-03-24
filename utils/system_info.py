import os
import psutil
from psutil._common import bytes2human
from aiogram.types import Message
from aiogram.enums import ParseMode
from keyboards import sysinfo_menu

async def disk_usage():
    templ = "%-17s %8s %8s %8s %5s%% %9s  %s\n"
    output = templ % ("Device", "Total", "Used", "Free", "Use ", "Type", "Mount")

    for part in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'cdrom' in part.opts or part.fstype == '':
                continue
        usage = psutil.disk_usage(part.mountpoint)
        output += templ % (
            part.device,
            bytes2human(usage.total),
            bytes2human(usage.used),
            bytes2human(usage.free),
            int(usage.percent),
            part.fstype,
            part.mountpoint
        )
    return output

async def send_system_info(message: Message):
    try:
        cpu_percent = psutil.cpu_percent(interval=1) 
        ram = psutil.virtual_memory()
        ram_percent = ram.percent 

        system_info = f"""CPU Usage: {cpu_percent}%
RAM Usage: {ram_percent}%
"""
        disk_percent = await disk_usage()
        delimiter = '+' + '-'*40 + '+'
        await message.edit_text(text=f"<pre>{delimiter}\n{system_info}{delimiter}\n{disk_percent}{delimiter}</pre>",
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=sysinfo_menu)
    except Exception as e:
        await message.reply(f"Error \- `{e}`", parse_mode="MarkdownV2")