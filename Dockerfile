FROM python:3.7.10-slim
LABEL MAINTAINER=dcueng@godaddy.com

COPY dist/requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt

COPY dist/*.whl /tmp/
RUN pip install /tmp/*.whl
RUN rm /tmp/*.whl

COPY . /tmp
# install custom root certificates
RUN mkdir -p /usr/local/share/ca-certificates/
RUN cp /tmp/certs/* /usr/local/share/ca-certificates/
RUN update-ca-certificates

RUN mkdir /app
COPY health.sh /app
COPY logging.yaml /app
RUN chmod +x /app/health.sh
RUN addgroup dcu && adduser --disabled-password --disabled-login --no-create-home --ingroup dcu --system dcu
RUN chown -R dcu:dcu /app

WORKDIR /app
USER dcu
ENTRYPOINT [ "/usr/local/bin/celery", "-A", "dcumiddleware.run", "worker", "-l", "INFO", "--without-gossip", "--without-heartbeat", "--without-mingle" ]