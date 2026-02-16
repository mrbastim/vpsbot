from dataclasses import dataclass
import subprocess


@dataclass
class DockerContainer:
    id: str
    name: str
    status: str


class DockerManager:
    def _run(self, args: list[str]) -> tuple[bool, str]:
        try:
            result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except Exception as err:
            return False, str(err)

        if result.returncode != 0:
            return False, (result.stderr or result.stdout).strip()
        return True, result.stdout.strip()

    def list_containers(self):
        ok, output = self._run(["docker", "ps", "-a"])
        if ok:
            return output
        return f"Error listing containers: {output}"

    def list_running_containers(self):
        ok, output = self._run(["docker", "ps"])
        if ok:
            return output
        return f"Error listing running containers: {output}"

    def list_images(self):
        ok, output = self._run(["docker", "images"])
        if ok:
            return output
        return f"Error listing images: {output}"

    def get_containers(self, all_containers: bool = True) -> tuple[list[DockerContainer], str | None]:
        cmd = ["docker", "ps"]
        if all_containers:
            cmd.append("-a")
        cmd += ["--format", "{{.ID}}|{{.Names}}|{{.Status}}"]

        ok, output = self._run(cmd)
        if not ok:
            return [], output

        containers: list[DockerContainer] = []
        if not output:
            return containers, None

        for line in output.splitlines():
            parts = line.split("|", 2)
            if len(parts) != 3:
                continue
            containers.append(DockerContainer(id=parts[0], name=parts[1], status=parts[2]))
        return containers, None

    def start_container(self, container_id: str) -> str:
        ok, output = self._run(["docker", "start", container_id])
        if ok:
            return f"Контейнер {container_id} запущен."
        return f"Ошибка запуска: {output}"

    def stop_container(self, container_id: str) -> str:
        ok, output = self._run(["docker", "stop", container_id])
        if ok:
            return f"Контейнер {container_id} остановлен."
        return f"Ошибка остановки: {output}"

    def restart_container(self, container_id: str) -> str:
        ok, output = self._run(["docker", "restart", container_id])
        if ok:
            return f"Контейнер {container_id} перезапущен."
        return f"Ошибка перезапуска: {output}"