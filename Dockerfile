# DCU Middleware
#
#

FROM ubuntu:14.04
MAINTAINER DCU ENG <DCUEng@godaddy.com>

RUN groupadd -r dcu && useradd -r -m -g dcu dcu

# apt-get installs
RUN apt-get update && \
    apt-get install -y build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python-dev \
    python-pip \
    xvfb

RUN Xvfb :1 -screen 0 1024x768x16 &> xvfb.log  &

# Make directory for middleware
RUN mkdir -p /app

WORKDIR /app

# Move files to new dir
ADD . /app
RUN chown -R dcu:dcu /app
RUN dpkg -i firefox_45.0.2+build1-0ubuntu0.14.04.1_amd64.deb; \
    apt-mark hold firefox;apt-get -f -y install;dpkg -i firefox_45.0.2+build1-0ubuntu0.14.04.1_amd64.deb

# pip install private pips staged by Makefile
RUN for entry in dcdatabase blindAl; \
    do \
    pip install --compile "/app/private_pips/$entry"; \
    done

RUN pip install --compile -r requirements.txt

# cleanup
RUN apt-get remove --purge -y build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python-dev && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /app/private_pips && \
    rm -rf /app/*.deb

USER dcu

CMD ["/usr/local/bin/celery", "-A", "run", "worker", "-l", "INFO"]
