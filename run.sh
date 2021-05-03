#!/usr/bin/env sh

python -c "import re;f=open('/etc/resolv.conf','r');t=f.read();t=re.sub(r'ndots:\d+',r'ndots:1',t);open('/etc/resolv.conf','w').write(t)"

exec su -s /bin/sh dcu -c "/usr/local/bin/celery -A run worker -l INFO --without-gossip --without-heartbeat --without-mingle"