from __future__ import annotations

import random
import socket
import string
from pathlib import Path

import urllib3
from docker import DockerClient
from docker.client import ContainerCollection, ImageCollection
from docker.errors import (
    APIError,
    BuildError,
    ContainerError,
    DockerException,
    ImageNotFound,
)
from docker.models.containers import Container
from docker.tls import TLSConfig
from requests.exceptions import ReadTimeout


class DockerHost:
    CONNECTION_TIMEOUT = 180

    def __init__(self, address: str, port: int) -> None:
        self._address = address
        self._port = port
        self._exception_text = (
            f'Unable to connect to Docker host "{self._address}:{self._port}". '
            f"You can check connectivity using the command:\n"
            f'"docker -H {self._address}:{self._port} info"\n'
            "to determine if access is possible."
        )

        if self._check_server_up() is False:
            raise ValueError(
                f'The address "{self._address}" does not correspond to an active server. '
                "Please check your connectivity."
            )

        self._client = self._get_docker_client()

    def _check_server_up(self) -> bool:
        try:
            with socket.create_connection((self._address, self._port), timeout=self.CONNECTION_TIMEOUT):
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False

    def get_docker_host_operation_system_type(self) -> str:
        return str(self._client.version()["Os"])

    def _get_docker_client(self) -> DockerClient:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        try:
            client = DockerClient(
                base_url=f"tcp://{self._address}:{self._port}",
                timeout=self.CONNECTION_TIMEOUT,
            )
            if client.ping():
                return client
        except (DockerException, ReadTimeout):
            pass

        try:
            client = DockerClient(
                base_url=f"tcp://{self._address}:{self._port}",
                tls=TLSConfig(ca_cert="./ca.pem"),
                timeout=self.CONNECTION_TIMEOUT,
            )
            if client.ping():
                return client
        except (DockerException, ReadTimeout):
            pass

        raise ValueError(self._exception_text)

    def generate_unique_image_name(self) -> str:
        existing_image_names = {i.tags[0] for i in self._client.images.list() if i.tags}

        while True:
            image_name = "".join(random.choice(string.ascii_lowercase) for _ in range(10))
            if f"{image_name}:{image_name}" not in existing_image_names:
                return f"{image_name}:{image_name}"

    def build_image(self, dockerfile_path: str, image_name: str) -> ImageCollection:
        try:
            parent_directory = str(Path(dockerfile_path).parent.absolute())
            return self._client.images.build(
                path=parent_directory,
                dockerfile=dockerfile_path,
                tag=image_name,
                rm=True,
                timeout=self.CONNECTION_TIMEOUT,
            )[0]
        except (BuildError, APIError):
            raise ValueError(f"Surena cannot build image.\n{self._exception_text}")

    def run_container(self, image: ImageCollection, **kwrgs) -> ContainerCollection:
        try:
            return self._client.containers.run(image.id, **kwrgs)
        except (ContainerError, APIError):
            return ValueError(f"Surena cannot run a container on Docker host.\n{self._exception_text}")

    def remove_image(self, image: ImageCollection) -> None:
        try:
            self._client.images.remove(image=image.id, force=True)
        except (ImageNotFound, APIError):
            raise ValueError(
                f'Surena cannot remove image "{image.id}".'
                "You would be able to delete a docker image by running the command below:\n"
                f'"docker rmi -f -H tcp://{self._address}:{self._port} {image.id}"'
            )

    def remove_container(self, container: ContainerCollection) -> None:
        container_: Container = self._client.containers.get(container)
        try:
            container_.remove(force=True)
        except (ImageNotFound, APIError):
            raise ValueError(
                f'Surena cannot remove container "{container.name}".\n'
                "You would be able to delete a docker container by running the command below:\n"
                f'"docker rm -f -H tcp://{self._address}:{self._port} {container.name}"'
            )
