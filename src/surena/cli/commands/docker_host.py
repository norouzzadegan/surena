import click
from docker import DockerClient
from docker.errors import DockerException


@click.command(name="is-docker-host")
@click.option("--docker-host-address", required=True, help="")
@click.option("--docker-host-port", required=True, help="")
def is_docker_host(docker_host_address: str, docker_host_port: int) -> None:
    tcp_url = "tcp://{}:{}".format(docker_host_address, docker_host_port)

    try:
        DockerClient(base_url=tcp_url)
        print('Address "{}" is a docker host.')
    except DockerException:
        print(
            'Surena could not understand address "{docker_host_address}:{port}" is a'
            ' docker host.\nYou can test it by using below command\n "docker -H'
            ' tcp://{docker_host_address}:{port} --version"'.format(
                docker_host_address=docker_host_address, port=docker_host_port
            )
        )
