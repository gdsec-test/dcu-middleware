#!/usr/bin/env sh

STATUS=$(celery -A run status | grep $(hostname) | awk '{print $2}')

if [ "${STATUS}" = "OK" ]; then
    exit 0
else
    exit 1
fi
