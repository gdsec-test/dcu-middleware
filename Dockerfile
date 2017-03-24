# DCU Middleware
#
#

FROM alpine:3.5
MAINTAINER DCU ENG <DCUEng@godaddy.com>

RUN addgroup -S dcu && adduser -H -S -G dcu dcu

# apt-get installs
RUN apk update && apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    python-dev \
    py-pip 

# Make directory for middleware
RUN mkdir -p /app

WORKDIR /app

# Move files to new dir
ADD . /app
RUN chown -R dcu:dcu /app

# pip install private pips staged by Makefile
RUN for entry in dcdatabase blindAl; \
    do \
    pip install --compile "/app/private_pips/$entry"; \
    done

RUN pip install --compile -r requirements.txt
RUN rm -rf private_pips

ENTRYPOINT ["/app/run.sh"]
