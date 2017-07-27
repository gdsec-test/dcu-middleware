import os
import urllib

from blindal.crypter import Crypter
from kombu import Exchange, Queue

from settings import config_by_name

# Grab the correct settings based on environment
app_settings = config_by_name[os.getenv('sysenv') or 'dev']


class CeleryConfig:
    BROKER_TRANSPORT = 'pyamqp'
    BROKER_USE_SSL = True
    CELERY_TASK_SERIALIZER = 'pickle'
    CELERY_RESULT_SERIALIZER = 'pickle'
    CELERY_ACCEPT_CONTENT = ['json', 'pickle']
    CELERY_IMPORTS = 'run'
    CELERYD_HIJACK_ROOT_LOGGER = False
    CELERY_RESULT_BACKEND = 'redis://{}:6379'.format(os.getenv("REDIS", "redis"))
    CELERY_DEFAULT_QUEUE = app_settings.APIQUEUE
    CELERY_ACKS_LATE = True
    CELERYD_PREFETCH_MULTIPLIER = 1
    CELERY_QUEUES = (
        Queue(app_settings.APIQUEUE, Exchange(app_settings.APIQUEUE), routing_key=app_settings.APIQUEUE)
    )

    CELERY_ROUTES = {
        'run.process_gd': {'queue': app_settings.GDBRANDSERVICESQUEUE, 'routing_key': app_settings.GDBRANDSERVICESQUEUE},
        'run.process_emea': {'queue': app_settings.EMEABRANDSERVICESQUEUE, 'routing_key': app_settings.EMEABRANDSERVICESQUEUE},
        'run.process_hainain': {'queue': app_settings.HAINAINBRANDSERVICESQUEUE, 'routing_key': app_settings.HAINAINBRANDSERVICESQUEUE}
    }

    def __init__(self):
        self.BROKER_PASS = os.getenv('BROKER_PASS') or 'password'
        keyfile = os.getenv('KEYFILE') or None
        if keyfile:
            f = open(keyfile, "r")
            try:
                key, iv = f.readline().split()
                self.BROKER_PASS = Crypter.decrypt(self.BROKER_PASS, key, iv)
            finally:
                f.close()
        self.BROKER_PASS = urllib.quote(self.BROKER_PASS)
        self.BROKER_URL = 'amqp://02d1081iywc7A:' + self.BROKER_PASS + '@infosec-rmq-v01.prod.phx3.secureserver.net:5672/grandma'

