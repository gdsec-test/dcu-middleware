# DCU Middleware

FROM alpine:3.5
MAINTAINER DCU ENG <DCUEng@godaddy.com>

RUN addgroup -S dcu && adduser -H -S -G dcu dcu
RUN apk update && \
    apk add --no-cache build-base \
    python-dev \
    py-pip

# Make directory for middleware
COPY ./run.py ./settings.py ./logging.yml ./celeryconfig.py ./*.sh /app/
COPY . /tmp/

RUN chown -R dcu:dcu /app

# pip install private pips staged by Makefile
RUN for entry in dcdatabase blindAl; \
    do \
    pip install --compile "/tmp/private_pips/$entry"; \
done

RUN pip install --compile /tmp && rm -rf /tmp/*

WORKDIR /app

ENTRYPOINT ["/app/run.sh"]