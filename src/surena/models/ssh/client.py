import random
import time

import paramiko


class SSHServer:
    def __init__(self, address: str, port: int, username: str, password: str) -> None:
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(address, port=port, username=username, password=password)

    def execute_command(self, command: str) -> None:
        stdin, stdout, stderr = self._client.exec_command(command)
        if stdout.channel.recv_exit_status() != 0:
            raise ValueError("Command execution failed")

    def restart_sshd_service(self) -> None:
        self.execute_command("systemctl restart sshd.service")

    def enable_gateway_port_on_public_server(self) -> None:
        self.execute_command("sed -i 's@#GatewayPorts no @GatewayPorts clientspecified@' /etc/ssh/sshd_config")

    def get_free_port(self) -> int:
        while True:
            free_port = random.randint(35000, 60000)
            try:
                self.execute_command(f"lsof -i:{free_port}")
            except ValueError:
                break
        return free_port

    def config_ssh_server(self) -> None:
        self.enable_gateway_port_on_public_server()
        time.sleep(5)
        self.restart_sshd_service()
