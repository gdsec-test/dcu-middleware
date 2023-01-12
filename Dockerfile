FROM docker-dcu-local.artifactory.secureserver.net/dcu-python3.11:1.1
LABEL MAINTAINER=dcueng@godaddy.com
USER root

COPY dist/requirements.txt /tmp/
RUN python -m pip install --upgrade pip pip==20.2.4
RUN apt-get update && apt-get install gcc libffi-dev -y
RUN pip install -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt
RUN apt-get remove gcc libffi-dev -y

COPY dist/*.whl /tmp/
RUN pip install /tmp/*.whl
RUN rm /tmp/*.whl

RUN mkdir /app
COPY health.sh /app
COPY logging.yaml /app
RUN chmod +x /app/health.sh
RUN chown -R dcu:dcu /app

WORKDIR /app
USER dcu
ENTRYPOINT [ "/usr/local/bin/celery", "-A", "dcumiddleware.run", "worker", "-l", "INFO", "--without-gossip", "--without-heartbeat", "--without-mingle" ]