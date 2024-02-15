import random
import time

from paramiko import SSHClient
from paramiko.client import AutoAddPolicy


class SSHServer:
    def __init__(self, address: str, port: int, username: str, password: str) -> None:
        self._client = SSHClient()
        self._client.set_missing_host_key_policy(AutoAddPolicy())
        self._client.connect(
            address, username=username, password=password, port=port
        )

    def execute_command(self, command: str) -> None:
        _, stdout, _ = self._client.exec_command(command)
        if stdout.channel.recv_exit_status() != 0:
            raise ValueError()

    def restart_sshd_service(self) -> None:
        self._client.exec_command("systemctl restart sshd.service")

    def enable_gateway_port_on_public_server(self) -> None:
        self.execute_command(
            "sed -i 's@#GatewayPorts no @GatewayPorts clientspecified@' /etc/ssh/sshd_config"
        )

    def get_free_port(self) -> int:
        while True:
            free_port = random.randint(35000, 60000)
            try:
                self.execute_command("lsof -i:{}".format(free_port))
            except ValueError:
                break
        return free_port

    def config_ssh_server(self):
        self.enable_gateway_port_on_public_server()
        time.sleep(5)

    def start_ssh_server(self):
        self.restart_sshd_service()
        time.sleep(5)
