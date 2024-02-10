FROM ubuntu:20.04
RUN apt update && \
    apt install -y tor openssh-server iproute2 sshpass
RUN sed -i '/#HiddenServiceDir \/var\/lib\/tor\/hidden_service\//s/^#//g' /etc/tor/torrc
ENTRYPOINT [ "/bin/bash", "-l", "-c" ]