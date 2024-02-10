from __future__ import annotations

import random
import socket
import string
from pathlib import Path
from typing import Iterable, Optional

import urllib3
from docker import Client
from docker import DockerClient as Client
from docker import tls
from docker.client import ContainerCollection, ImageCollection
from docker.errors import (
    APIError,
    BuildError,
    ContainerError,
    DockerException,
    ImageNotFound,
)
from pkg_resources import resource_filename
from requests.exceptions import ReadTimeout
from simplejson.errors import JSONDecodeError


class DockerClient:
    CONNECTION_TIMEOUT = 180

    def __init__(self, address: str, port: int) -> None:
        self._address = address
        self._port = port
        if self.check_server_up() is False:
            raise ValueError(
                'The address "{}" does not correspond to an active server.\n Please'
                " check your connectivity.".format(self._address)
            )

        self._client = self._get_docker_client()

    def check_server_up(self) -> None:
        try:
            with socket.create_connection(
                (self._address, self._port), timeout=self.CONNECTION_TIMEOUT
            ):
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False

    def get_docker_host_operation_system_type(self) -> str:
        return self._client.version()["Os"]

    def _get_docker_client(self) -> Client:
        exception_text = (
            f'Unable to connect to Docker host "{self._address}:{self._port}".You can'
            ' do it by below command:\n"docker -H'
            f' {self._address}:{self._port} ps"\nto determine if access to it is possible.'
        )
        if self.check_server_up(self._address, self._port) == False:
            AssertionError(exception_text)

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        tls = tls.TLSConfig(ca_cert="./ca.pem")

        try:
            client = Client(
                base_url="tcp://{}:{}".format(self._address, self._port),
                timeout=self.CONNECTION_TIMEOUT,
            )
            if client.ping() is True:
                return client
            else:
                raise ValueError(exception_text)
        except DockerException:
            try:
                client = Client(
                    base_url="tcp://{}:{}".format(self._address, self._port),
                    tls=tls,
                    timeout=self.CONNECTION_TIMEOUT,
                )
                if client.ping() is True:
                    return client
                else:
                    raise ValueError(exception_text)
            except (ReadTimeout, DockerException):
                raise ValueError(exception_text)
        except (ReadTimeout, JSONDecodeError):
            raise ValueError(exception_text)

    def get_unique_image_name(self) -> str:
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
            raise BuildError("Could not build image\n{}".format(e))

    def run_container(self, image: ImageCollection, **kwrgs) -> ContainerCollection:
        try:
            return self._client.containers.run(image.id, **kwrgs)
        except (ContainerError, APIError):
            return ContainerError("Could not run container.")

    def remove_image(self, image: ImageCollection) -> bool:
        try:
            self._client.images.remove(image=image.id, force=True, noprune=False)
            return True
        except (ImageNotFound, APIError):
            raise ValueError("...")

    def remove_container(self, container: ContainerCollection) -> bool:
        try:
            self._client.containers.remove(container, force=True)
            return True
        except (ImageNotFound, APIError):
            raise ValueError(".....")

    def destroy_images(self, images: Iterable[ImageCollection]) -> None:
        for image in images:
            self.destroy_images(image)

    def destroy_image(self, image: ImageCollection) -> None:
        self.remove_image(image)

    def destroy_containers(self, containers: Iterable[ContainerCollection]) -> None:
        for container in containers:
            self.destroy_images(container)

    def destroy_container(self, container: ContainerCollection) -> None:
        self.remove_image(container)
