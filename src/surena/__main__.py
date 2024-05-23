import click

from surena.cli.commands import get_docker_host, is_docker_host


@click.group(
    commands={
        is_docker_host.name: is_docker_host,
        get_docker_host.name: get_docker_host,
    }
)
def surena() -> None:
    """
    Surena is a security tool designed to access the Docker host
    """
    pass


def cli() -> None:
    surena(auto_envvar_prefix="SURENA")


if __name__ == "__main__":
    cli()
