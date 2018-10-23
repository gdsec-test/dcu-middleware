import os
import urllib

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
    CELERY_DEFAULT_QUEUE = app_settings.APIQUEUE
    CELERY_ACKS_LATE = True
    CELERYD_PREFETCH_MULTIPLIER = 1
    CELERY_SEND_EVENTS = False
    CELERY_QUEUES = (
        Queue(app_settings.APIQUEUE, Exchange(app_settings.APIQUEUE), routing_key=app_settings.APIQUEUE),
    )

    CELERY_ROUTES = {
        'run.process_gd': {'queue': app_settings.GDBRANDSERVICESQUEUE, 'routing_key': app_settings.GDBRANDSERVICESQUEUE},
        'run.process_emea': {'queue': app_settings.EMEABRANDSERVICESQUEUE, 'routing_key': app_settings.EMEABRANDSERVICESQUEUE}
    }

    def __init__(self):
        self.BROKER_PASS = urllib.quote(os.getenv('BROKER_PASS', 'password'))
        self.BROKER_URL = 'amqp://02d1081iywc7A:' + self.BROKER_PASS + '@rmq-dcu.int.godaddy.com:5672/grandma'
