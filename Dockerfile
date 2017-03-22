# DCU Middleware
#
#

FROM ubuntu:16.04
MAINTAINER DCU ENG <DCUEng@godaddy.com>

RUN groupadd -r dcu && useradd -r -m -g dcu dcu

# apt-get installs
RUN apt-get update && \
    apt-get install -y build-essential \
    gcc \
    firefox=52.0.1+build2-0ubuntu0.16.04.1 \
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
RUN mv geckodriver /bin
RUN chown -R dcu:dcu /app

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
