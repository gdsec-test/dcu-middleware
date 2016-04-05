import os

from kombu import Exchange, Queue

from settings import config_by_name

# Grab the correct settings based on environment
app_settings = config_by_name[os.getenv('sysenv') or 'dev']

BROKER_TRANSPORT = 'pyamqp'
BROKER_URL = 'amqp://02d1081iywc7A:7%7CRc8jE1Sn0%2BA%23@infosec-rmq-v01.prod.phx3.secureserver.net:5672/grandma'
# BROKER_PASSWORD = '***REMOVED***'
BROKER_USE_SSL = True
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_IMPORTS = 'run'
CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_QUEUES = (
    Queue(app_settings.APIQUEUE, Exchange(app_settings.APIQUEUE), routing_key=app_settings.APIQUEUE),
)
