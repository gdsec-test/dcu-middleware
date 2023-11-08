import os

from celery import Celery
from kombu import Exchange, Queue

from dcumiddleware.settings import AppConfig, config_by_name

# Grab the correct settings based on environment
app_settings: AppConfig = config_by_name[os.getenv('sysenv') or 'dev']


class CeleryConfig:
    broker_transport = 'pyamqp'
    broker_use_ssl = not bool(os.getenv('DISABLESSL', ''))
    task_serializer = 'pickle'
    result_serializer = 'pickle'
    accept_content = ['json', 'pickle']
    imports = 'dcumiddleware.run'
    worker_hijack_root_logger = False
    task_acks_late = True
    worker_prefetch_multiplier = 1
    worker_send_task_events = False
    # Force kill a task if it takes longer than three minutes.
    task_time_limit = 180
    # Generate soft time limit exceptions before the hard time limits
    # so our retry logic is correctly applied.
    task_soft_time_limit = 120
    WORKER_ENABLE_REMOTE_CONTROL = True

    queue_args = {'x-queue-type': 'quorum'}
    api_queue = Queue(app_settings.APIQUEUE, Exchange(app_settings.APIQUEUE), routing_key=app_settings.APIQUEUE,
                      queue_arguments=queue_args)
    task_default_queue = app_settings.APIQUEUE
    task_queues = (
        api_queue,
    )

    task_routes = {
        'run.process_gd': {
            'queue': Queue(app_settings.GDBRANDSERVICESQUEUE, Exchange(app_settings.GDBRANDSERVICESQUEUE),
                           routing_key=app_settings.GDBRANDSERVICESQUEUE, queue_arguments=queue_args)},
        'run.process_emea': {
            'queue': Queue(app_settings.EMEABRANDSERVICESQUEUE, Exchange(app_settings.EMEABRANDSERVICESQUEUE),
                           routing_key=app_settings.EMEABRANDSERVICESQUEUE, queue_arguments=queue_args)},
        'routing.run.process_external_report': {
            'queue': Queue(app_settings.ROUTINGQUEUE, Exchange(app_settings.ROUTINGQUEUE),
                           routing_key=app_settings.ROUTINGQUEUE, queue_arguments=queue_args)},
    }

    def __init__(self):
        self.broker_url = app_settings.BROKER_URL


app = Celery()
app.config_from_object(CeleryConfig())
