import logging
import random
import time

import paramiko

logger = logging.getLogger()


class SSHServer:
    def __init__(self, address: str, port: int, username: str, password: str) -> None:
        self._address = address
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(self._address, port=port, username=username, password=password)

    def execute_command(self, command: str) -> int:
        _, stdout, _ = self._client.exec_command(command)
        return stdout.channel.recv_exit_status()

    def check_gatewayport_is_enable_on_server(self) -> None:
        exit_status = self.execute_command(
            r"grep -q '^GatewayPorts yes$\|^GatewayPorts clientspecified$' '/etc/ssh/sshd_config' " "|| exit 1"
        )

        if exit_status != 0:
            raise ValueError(
                'Please first update the configuration of "sshd_config" located at '
                f'"/etc/ssh/sshd_config" on the SSH remote server with address "{self._address}" '
                'by changing the value of "GatewayPorts no" to "GatewayPorts clientspecified" '
                "to enable support for GatewayPorts in SSH. After that, please restart the SSH "
                "service on the remote server. Then, please run Surena."
            )

    def get_free_port(self) -> int:
        while True:
            free_port = random.randint(35000, 60000)
            exit_status = self.execute_command(f"(lsof -i :{free_port}) && exit 1 || exit 0")
            if exit_status == 0:
                break
        return free_port
