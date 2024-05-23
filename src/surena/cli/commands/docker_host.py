import logging

import click

from surena.cli.options import Port
from surena.models.docker_host import DockerHost

logger = logging.getLogger()


@click.command(name="is-docker-host")
@click.option("--docker-host-address", required=True, help="The Docker host address.")
@click.option("--docker-host-port", required=True, type=Port(), help="The Docker host port.")
def is_docker_host(docker_host_address: str, docker_host_port: int) -> None:
    """
    Check if the Docker daemon port is exposed and accessible via TCP.
    """
    try:
        DockerHost(docker_host_address, docker_host_port)
        logger.info(f'Address "{docker_host_address}:{docker_host_port}" is a Docker host.')
    except ValueError:
        logger.error(
            f'Surena could not understand address "{docker_host_address}:{docker_host_port}" as a Docker host.\n'
            f"You can test it by using the command: "
            '"docker -H tcp://{docker_host_address}:{docker_host_port} --version"'
        )
