from __future__ import annotations

import random
import socket
import string
from pathlib import Path
from typing import Iterable

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
from simplejson.errors import JSONDecodeError


class DockerHost:
    CONNECTION_TIMEOUT = 180

    def __init__(self, address: str, port: int) -> None:
        self._address = address
        self._port = port
        self._exception_text = (
            f'Unable to connect to Docker host "{self._address}:{self._port}".You can'
            f' do it by below command:\n"docker -H {self._address}:{self._port} ps"\nto'
            " determine if access to it is possible."
        )
        if self.check_server_up() is False:
            raise ValueError(
                'The address "{}" does not correspond to an active server.\n Please'
                " check your connectivity.".format(self._address)
            )

        self._client = self._get_docker_client()

    def check_server_up(self) -> bool:
        try:
            with socket.create_connection(
                (self._address, self._port), timeout=self.CONNECTION_TIMEOUT
            ):
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False

    def get_docker_host_operation_system_type(self) -> str:
        return str(self._client.version()["Os"])

    def _get_docker_client(self) -> DockerClient:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try:
            client = DockerClient(
                base_url="tcp://{}:{}".format(self._address, self._port),
                timeout=self.CONNECTION_TIMEOUT,
            )
            if bool(client.ping()) is True:
                return client
            else:
                raise ValueError(self._exception_text)
        except DockerException:
            try:
                client = DockerClient(
                    base_url="tcp://{}:{}".format(self._address, self._port),
                    tls=TLSConfig(ca_cert="./ca.pem"),
                    timeout=self.CONNECTION_TIMEOUT,
                )
                if bool(client.ping()) is True:
                    return client
                else:
                    raise ValueError(self._exception_text)
            except (ReadTimeout, DockerException):
                raise ValueError(self._exception_text)
        except (ReadTimeout, JSONDecodeError):
            raise ValueError(self._exception_text)

    def get_image_unique_name(self) -> str:
        existing_image_names = {i.tags[0] for i in self._client.images.list() if i.tags}

        while True:
            image_name = "".join(
                random.choice(string.ascii_lowercase) for _ in range(10)
            )
            if f"{image_name}:{image_name}" not in existing_image_names:
                return f"{image_name}:{image_name}"

    def build_image(self, dockerfile_path: str, image_name: str) -> ImageCollection:
        try:
            return self._client.images.build(
                path=Path(dockerfile_path).parent.absolute(),
                dockerfile=dockerfile_path,
                tag=image_name,
                rm=True,
                timeout=self.CONNECTION_TIMEOUT,
            )[0]
        except (BuildError, APIError) as e:
            raise BuildError(f"Cannot build image\n{e}.\n{self._exception_text}")

    def run_container(self, image: ImageCollection, **kwrgs) -> ContainerCollection:
        try:
            return self._client.containers.run(image.id, **kwrgs)
        except (ContainerError, APIError):
            return ContainerError(
                f"Could not run a container on Docker host.\n{self._exception_text}"
            )

    def remove_images(self, images: Iterable[ImageCollection]) -> None:
        for image in images:
            self.remove_image(image)

    def remove_image(self, image: ImageCollection) -> None:
        try:
            self._client.images.remove(image=image.id, force=True, noprune=False)
        except (ImageNotFound, APIError):
            raise ValueError(
                f'Cannot remove image "{image.name}".\n{self._exception_text}'
            )

    def remove_containers(self, containers: Iterable[ContainerCollection]) -> None:
        for container in containers:
            self.remove_container(container)

    def remove_container(self, container: ContainerCollection) -> None:
        try:
            container_: Container = self._client.containers.get(container)
            container_.remove(force=True)
        except (ImageNotFound, APIError):
            raise ValueError(
                f'Cannot remove container "{container.name}".\n{self._exception_text}'
            )
