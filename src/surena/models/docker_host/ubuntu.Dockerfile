FROM ubuntu:20.04

RUN apt update && \
    apt install -y tor openssh-server iproute2 sshpass

# Mount /data
VOLUME /data

ENTRYPOINT [ "/bin/bash", "-l", "-c" ]
