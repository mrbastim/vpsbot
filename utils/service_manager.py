import asyncio
import os
import re
from dataclasses import dataclass

SERVICE_NAME_RE = re.compile(r"^[A-Za-z0-9_.@-]{1,128}$")


class InvalidServiceName(ValueError):
    pass


@dataclass
class Server:
    id: str
    name: str


def _check_name(name: str) -> str:
    if not SERVICE_NAME_RE.match(name or ""):
        raise InvalidServiceName(f"Недопустимое имя сервиса: {name!r}")
    return name


async def _run(*args: str) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return (
        proc.returncode,
        stdout.decode(errors="replace").strip(),
        stderr.decode(errors="replace").strip(),
    )


class ServiceManager:
    def __init__(self, service_name):
        self.service_name = _check_name(service_name)

    async def get_status(self) -> str:
        try:
            code, out, err = await _run("systemctl", "is-active", self.service_name)
        except Exception as e:
            return f"Ошибка проверки статуса: {e}"
        if code == 0:
            return f"🟢 Active ({out})" if out else "🟢 Active"
        if code == 3:
            return "🔴 Inactive"
        if code == 4:
            return f"⚪ Не найден ({err or out})"
        return f"⚠️ Unknown (код {code}) {err or out}".strip()

    async def start_service(self) -> str:
        return await self._action("start", "запущен")

    async def stop_service(self) -> str:
        return await self._action("stop", "остановлен")

    async def restart_service(self) -> str:
        return await self._action("restart", "перезапущен")

    async def _action(self, verb: str, past: str) -> str:
        try:
            code, _, err = await _run("systemctl", verb, self.service_name)
        except Exception as e:
            return f"Ошибка выполнения {verb}: {e}"
        if code == 0:
            return f"{self.service_name} успешно {past}."
        return f"Ошибка {verb}: код {code} {err}".strip()

    @classmethod
    async def get_servers(cls) -> list[Server]:
        try:
            files = os.listdir("/etc/systemd/system")
        except OSError:
            files = []
        return [
            Server(id=f[: -len(".service")], name=f[: -len(".service")])
            for f in files
            if f.endswith(".service") and SERVICE_NAME_RE.match(f[: -len(".service")])
        ]
