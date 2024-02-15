import logging

import click

from surena.cli.options import Port
from surena.models.docker_client import DockerHost

logger = logging.getLogger()


@click.command(name="is-docker-host")
@click.option("--docker-host-address", required=True, help="The Docker host address.")
@click.option(
    "--docker-host-port", required=True, type=Port(), help="The Docker host port."
)
def is_docker_host(docker_host_address: str, docker_host_port: int) -> None:
    try:
        DockerHost(docker_host_address, docker_host_port)
        logger.info('Address "{}" is a docker host.')
    except ValueError:
        logger.error(
            'Surena could not understand address "{docker_host_address}:{port}" is a'
            ' docker host.\nYou can test it by using below command\n "docker -H'
            ' tcp://{docker_host_address}:{port} --version"'.format(
                docker_host_address=docker_host_address, port=docker_host_port
            )
        )
