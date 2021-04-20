import os
import urllib.parse

from kombu import Exchange, Queue

from settings import config_by_name

# Grab the correct settings based on environment
app_settings = config_by_name[os.getenv('sysenv') or 'dev']


class CeleryConfig:
    broker_transport = 'pyamqp'
    broker_use_ssl = not bool(os.getenv('DISABLESSL', ''))
    task_serializer = 'pickle'
    result_serializer = 'pickle'
    accept_content = ['json', 'pickle']
    imports = 'run'
    worker_hijack_root_logger = False
    task_default_queue = app_settings.APIQUEUE
    task_acks_late = True
    worker_prefetch_multiplier = 1
    worker_send_task_events = False
    task_queues = (
        Queue(app_settings.APIQUEUE, Exchange(app_settings.APIQUEUE), routing_key=app_settings.APIQUEUE),
    )

    task_routes = {
        'run.process_gd': {'queue': app_settings.GDBRANDSERVICESQUEUE, 'routing_key': app_settings.GDBRANDSERVICESQUEUE},
        'run.process_emea': {'queue': app_settings.EMEABRANDSERVICESQUEUE, 'routing_key': app_settings.EMEABRANDSERVICESQUEUE}
    }

    def __init__(self):
        self.BROKER_PASS = urllib.parse.quote(os.getenv('BROKER_PASS', 'password'))
        if os.getenv('BROKER_URL'):
            self.broker_url = os.getenv('BROKER_URL')
        else:
            self.broker_url = 'amqp://02d1081iywc7A:' + self.BROKER_PASS + '@rmq-dcu.int.godaddy.com:5672/grandma'
