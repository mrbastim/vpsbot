from dataclasses import dataclass
import os

@dataclass
class Server:
    id: str
    name: str

class ServiceManager:
    def __init__(self, service_name):
        self.service_name = service_name

    def get_status(self):
        import subprocess
        try:
            result = subprocess.run(
                ["systemctl", "is-active", self.service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                return "🟢 Active"
            elif result.returncode == 3:
                return "🔴 Inactive"
            else:
                return "Unknown"
            # return result.stdout.strip()
        except Exception as e:
            return f"Error checking status: {e}"

    def start_service(self):
        import subprocess
        try:
            subprocess.run(["systemctl", "start", self.service_name], check=True)
            return f"{self.service_name} started successfully."
        except subprocess.CalledProcessError as e:
            return f"Error starting service: {e}"

    def stop_service(self):
        import subprocess
        try:
            subprocess.run(["systemctl", "stop", self.service_name], check=True)
            return f"{self.service_name} stopped successfully."
        except subprocess.CalledProcessError as e:
            return f"Error stopping service: {e}"

    @classmethod
    async def get_servers(cls):
        directory = "/etc/systemd/system"
        try:
            files = os.listdir(directory)
        except Exception as e:
            files = []
        return [
            Server(id=file[:-len(".service")], name=file[:-len(".service")])
            for file in files if file.endswith(".service")
        ]