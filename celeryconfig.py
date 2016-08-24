import os
import urllib

from blindal.crypter import Crypter
from kombu import Exchange, Queue

from settings import config_by_name

# Grab the correct settings based on environment
app_settings = config_by_name[os.getenv('sysenv') or 'dev']


class CeleryConfig():
    BROKER_TRANSPORT = 'pyamqp'
    BROKER_USE_SSL = True
    CELERY_TASK_SERIALIZER = 'pickle'
    CELERY_RESULT_SERIALIZER = 'pickle'
    CELERY_ACCEPT_CONTENT = ['json', 'pickle']
    CELERY_IMPORTS = 'run'
    CELERYD_HIJACK_ROOT_LOGGER = False
    CELERY_RESULT_BACKEND = 'redis://redis:6379'
    CELERY_DEFAULT_QUEUE = app_settings.APIQUEUE
    CELERY_QUEUES = (
        Queue(app_settings.APIQUEUE, Exchange(app_settings.APIQUEUE), routing_key=app_settings.APIQUEUE),
    )

    CELERY_ROUTES = {
       'run.group': {'queue': app_settings.COMPACTORQUEUE},
       'run.sendmail': {'queue': app_settings.MAILQUEUE}
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

