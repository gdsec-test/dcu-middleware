import os

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
    task_default_queue = app_settings.APIQUEUE
    task_acks_late = True
    worker_prefetch_multiplier = 1
    worker_send_task_events = False
    # Force kill a task if it takes longer than three minutes.
    task_time_limit = 180
    WORKER_ENABLE_REMOTE_CONTROL = False

    # TODO CMAPT-5032: set this to 'quorum'
    queue_type = app_settings.QUEUE_TYPE

    task_queues = (
        Queue(app_settings.APIQUEUE, Exchange(app_settings.APIQUEUE), routing_key=app_settings.APIQUEUE,
              queue_arguments={'x-queue-type': queue_type}),
    )

    task_routes = {
        'run.process_gd': {'queue': app_settings.GDBRANDSERVICESQUEUE, 'routing_key': app_settings.GDBRANDSERVICESQUEUE},
        'run.process_emea': {'queue': app_settings.EMEABRANDSERVICESQUEUE, 'routing_key': app_settings.EMEABRANDSERVICESQUEUE}
    }

    def __init__(self):
        self.broker_url = app_settings.BROKER_URL
