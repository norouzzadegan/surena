FROM ubuntu:20.04

RUN apt update && \
    apt install -y \
    tor \
    openssh-server \
    iproute2 \
    sshpass && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Mount /data as a volume
VOLUME /data

ENTRYPOINT [ "/bin/bash", "-l", "-c" ]
