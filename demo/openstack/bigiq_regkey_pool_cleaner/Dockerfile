FROM ubuntu:latest
LABEL maintainer="John Gruber <j.gruber@f5.com>"

WORKDIR /

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    python-jsonschema \
    python-yaml \
    python-pip \
    python-setuptools \
    git

## INJECT_PATCH_INSTRUCTION ##
RUN git clone https://github.com/jgruber/tmos-cloudinit.git

ENV USER 'root'

ENTRYPOINT [ "/tmos-cloudinit/demo/openstack/bigiq_regkey_pool_cleaner/bigiq_regkey_pool_cleaner.py", '-d' ]

