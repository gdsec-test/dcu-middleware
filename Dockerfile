FROM python:3.7.10-slim as base

LABEL MAINTAINER="dcueng@godaddy.com"

# pip installs
RUN pip3 install -U pip
COPY requirements.txt .
COPY ./private_pips /tmp/private_deps

RUN pip3 install --compile /tmp/private_deps/dcdatabase
RUN pip3 install --compile /tmp/private_deps/dcu-prometheus-celery
RUN pip3 install --compile /tmp/private_deps/dcu-structured-logging-celery
RUN pip3 install -r requirements.txt

RUN rm requirements.txt
RUN rm -rf /tmp/private_deps

FROM base as deliverable

COPY ./run.py ./settings.py ./logging.yaml ./celeryconfig.py ./*.sh /app/

# Compile the Flask API
RUN mkdir /tmp/build
COPY . /tmp/build
RUN pip3 install --compile /tmp/build
RUN rm -rf /tmp/build

# Fix permissions.
RUN addgroup dcu && adduser --disabled-password --disabled-login --no-create-home --ingroup dcu --system dcu
RUN chown -R dcu:dcu /app

WORKDIR /app

ENTRYPOINT ["/app/run.sh"]
