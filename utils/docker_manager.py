import asyncio
import re
from dataclasses import dataclass

CONTAINER_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")


@dataclass
class DockerContainer:
    id: str
    name: str
    status: str


class DockerManager:
    async def _run(self, args: list[str]) -> tuple[bool, str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
        except Exception as err:
            return False, str(err)

        if proc.returncode != 0:
            return False, (stderr or stdout).decode(errors="replace").strip()
        return True, stdout.decode(errors="replace").strip()

    async def get_containers(
        self, all_containers: bool = True
    ) -> tuple[list[DockerContainer], str | None]:
        cmd = ["docker", "ps"]
        if all_containers:
            cmd.append("-a")
        cmd += ["--format", "{{.ID}}|{{.Names}}|{{.Status}}"]

        ok, output = await self._run(cmd)
        if not ok:
            return [], output

        containers = []
        for line in output.splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3:
                containers.append(
                    DockerContainer(id=parts[0], name=parts[1], status=parts[2])
                )
        return containers, None

    async def start_container(self, container_id: str) -> str:
        return await self._action("start", "запущен", container_id)

    async def stop_container(self, container_id: str) -> str:
        return await self._action("stop", "остановлен", container_id)

    async def restart_container(self, container_id: str) -> str:
        return await self._action("restart", "перезапущен", container_id)

    async def _action(self, verb: str, past: str, container_id: str) -> str:
        if not CONTAINER_ID_RE.match(container_id or ""):
            return f"Ошибка: недопустимый идентификатор контейнера {container_id!r}."
        ok, output = await self._run(["docker", verb, container_id])
        if ok:
            return f"Контейнер {container_id} {past}."
        return f"Ошибка {verb}: {output}"
