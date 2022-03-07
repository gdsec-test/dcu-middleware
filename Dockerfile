FROM python:3.7.10-slim as base

LABEL MAINTAINER="dcueng@godaddy.com"

# pip installs
RUN pip3 install -U pip

FROM base as deliverable

COPY ./run.py ./settings.py ./logging.yaml ./celeryconfig.py ./*.sh ./apm.py /app/

# Compile the Flask API
RUN mkdir /tmp/build
COPY . /tmp/build
RUN PIP_CONFIG_FILE=/tmp/build/pip_config/pip.conf pip3 install --compile /tmp/build
RUN rm -rf /tmp/build

# Fix permissions.
RUN addgroup dcu && adduser --disabled-password --disabled-login --no-create-home --ingroup dcu --system dcu
RUN chown -R dcu:dcu /app

WORKDIR /app

ENTRYPOINT ["/app/run.sh"]
