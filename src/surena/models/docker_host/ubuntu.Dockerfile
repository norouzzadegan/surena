FROM ubuntu:20.04

RUN apt update && \
    apt install -y tor openssh-server iproute2 sshpass

ENTRYPOINT [ "/bin/bash", "-l", "-c" ]
