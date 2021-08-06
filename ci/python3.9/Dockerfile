FROM python:3.9-slim-buster

ENV HOME=/root

RUN \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get -y install --no-install-recommends \
    python3-dev python3-setuptools python3-pip python3-pytest \
    && \
  apt-get clean

# Update python paths
RUN \
  update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
  update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

CMD [ "bash" ]
