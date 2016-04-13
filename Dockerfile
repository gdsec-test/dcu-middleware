# DCU Middleware
#
#

FROM ubuntu:14.04
MAINTAINER DCU ENG <DCUEng@godaddy.com>

RUN groupadd -r dcu && useradd -r -g dcu dcu
RUN usermod -aG syslog dcu

# apt-get installs
RUN apt-get update && \
    apt-get install -y build-essential \
    gcc \
    python-dev \
    python-pip

# Make directory for middleware
RUN mkdir -p /app

WORKDIR /app

# Move files to new dir
ADD . /app

RUN pip install --compile -r requirements.txt

# cleanup
RUN apt-get remove --purge -y build-essential \
    gcc \
    python-dev && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /app/private_pips

USER dcu

CMD ["/usr/local/bin/celery", "-A", "run", "worker", "-l", "INFO"]
