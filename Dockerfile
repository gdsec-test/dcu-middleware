# DCU Middleware
#
#

FROM ubuntu:14.04
MAINTAINER DCU ENG <DCUEng@godaddy.com>

# apt-get installs
RUN apt-get update && \
    apt-get install -y build-essential \
    gcc \
    firefox \
    python-dev \
    python-pip \
    xvfb

RUN Xvfb :1 -screen 0 1024x768x16 &> xvfb.log  &

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

CMD ["/usr/local/bin/celery", "-A", "run", "worker", "-l", "INFO"]
