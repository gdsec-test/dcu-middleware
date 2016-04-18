import logging
import logging.handlers
import os

from celery import Celery
from celery.utils.log import get_task_logger

import celeryconfig
from dcumiddleware.incident import Incident
from dcumiddleware.malwarestrategy import MalwareStrategy
from dcumiddleware.netabusestrategy import NetAbuseStrategy
from dcumiddleware.phishingstrategy import PhishingStrategy
from settings import config_by_name

# Grab the correct settings based on environment
app_settings = config_by_name[os.getenv('sysenv') or 'dev']

# Define log level, location, and formatting
logging.basicConfig(format=app_settings.FORMAT,
                    datefmt=app_settings.DATE_FORMAT,
                    level=app_settings.LOGLEVEL)
fileh = logging.handlers.RotatingFileHandler('/var/log/middleware.log', maxBytes=10485760, backupCount=5)
fileh.setLevel(app_settings.LOGLEVEL)
formatter = logging.Formatter(app_settings.FORMAT)
fileh.setFormatter(formatter)
logging.getLogger('').addHandler(fileh)
logger = get_task_logger(__name__)

app = Celery()
app.config_from_object(celeryconfig)

"""
Sample data:
{'info': u'My spam Farm is better than yours...',
 'domain': u'spam.com',
 'ticketId': u'DCU000001053',
 'target': u'The spam Brothers',
 'reporter': u'bxberry',
 'intentional': False,
 'sources': u'http://spam.com/thegoodstuff/jonas.php?g=a&itin=1324',
 'proxy': u'Must be viewed from an German IP',
 'moreInfo': u'http://report.busters.com?report=714',
 'type': u'PHISHING'}
"""


@app.task(name='run.process')
def process(data):
    """
    Processes data from the phishworker queue.
    :param irispullerdata:
    :return:
    """
    incident = Incident(data)
    strategy = None
    if incident.type == "PHISHING":
        strategy = PhishingStrategy(app_settings)
    elif incident.type == "MALWARE":
        strategy = MalwareStrategy(app_settings)
    elif incident.type == "NETABUSE":
        strategy = NetAbuseStrategy(app_settings)

    try:
        strategy.process(incident)
    except Exception as e:
        logger.error("Unable to process incident {}:{}".format(incident, e.message))
