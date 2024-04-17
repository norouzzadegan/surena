FROM ubuntu:20.04

RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y \
    openssh-server \
    tor \
    iproute2 \
    sshpass && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Mount /data as a volume
VOLUME /data

ENTRYPOINT ["/bin/bash", "-l", "-c"]
