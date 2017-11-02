# DCU Middleware
#
#

FROM ubuntu:16.10
MAINTAINER DCU ENG <DCUEng@godaddy.com>

RUN groupadd -r dcu && useradd -r -m -g dcu dcu

# apt-get installs
RUN apt-get update && \
    apt-get install -y build-essential \
    fontconfig \
    gcc \
    libffi-dev \
    libssl-dev \
    python-dev \
    python-pip \
    curl

RUN cd /usr/local/share && \
curl -L https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 | tar xj && \
ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/bin/phantomjs

# Make directory for middleware
COPY ./run.py ./settings.py ./logging.yml ./celeryconfig.py ./health.sh /app/
COPY . /tmp/

# pip install private pips staged by Makefile
RUN for entry in dcdatabase blindAl; \
    do \
    pip install --compile "/tmp/private_pips/$entry"; \
    done

RUN pip install --compile /tmp

# cleanup
RUN apt-get remove --purge -y build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python-dev && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp && \
    chown -R dcu:dcu /app


USER dcu
WORKDIR /app

CMD ["/usr/local/bin/celery", "-A", "run", "worker", "-l", "INFO", "--without-gossip", "--without-mingle", "--without-heartbeat"]
