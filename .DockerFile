FROM debian:stable

ENV HOME=/root

RUN \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get -y install --no-install-recommends \
    python-dev python-setuptools python-pip python-pytest \
    python3-dev python3-setuptools python3-pip python3-pytest \
    && \
  apt-get clean

CMD [ "bash" ]
