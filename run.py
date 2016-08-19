import logging
import logging.handlers
import os
from datetime import datetime, timedelta

from celery import Celery
from celery.utils.log import get_task_logger

from celeryconfig import CeleryConfig
from dcumiddleware.incident import Incident
from dcumiddleware.malwarestrategy import MalwareStrategy
from dcumiddleware.netabusestrategy import NetAbuseStrategy
from dcumiddleware.phishingstrategy import PhishingStrategy
from dcumiddleware.reviews import FraudReview
from settings import config_by_name

# Grab the correct settings based on environment
app_settings = config_by_name[os.getenv('sysenv') or 'dev']()

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
app.config_from_object(CeleryConfig())

"""
Sample data:
{'info': u'My spam Farm is better than yours...',
 'sourceDomainOrIp': u'spam.com',
 'ticketId': u'DCU000001053',
 'target': u'The spam Brothers',
 'reporter': u'bxberry',
 'source': u'http://spam.com/thegoodstuff/jonas.php?g=a&itin=1324',
 'proxy': u'Must be viewed from an German IP',
 'type': u'PHISHING'}
"""


@app.task(name='run.hold')
def hold(data):
    pass


@app.task(name='run.malicious')
def malicious(data):
    pass


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
    rdata = strategy.process(incident)
    if rdata:
        logger.info("Successfully processed {}".format(rdata))
        post_process(rdata)
    else:
        logger.error("Unable to process incident {}, no data returned".format(incident))


def post_process(data):
    """
    This function handles post processing the data for basic fraud detection, grouping etc.
    :param data:
    :return:
    """
    incident = Incident(data)
    try:
        # If the s_create_date is less than x days old, put on review and send to fraud
        if incident.phihstory_status == 'OPEN' \
                and incident.s_create_date \
                and incident.s_create_date > datetime.utcnow() - timedelta(days=app_settings.NEW_ACCOUNT):
            review = FraudReview(app_settings)
            doc = review.place_in_review(incident.ticketId, app_settings.HOLD_TIME)
            if doc.get('fraud_notified', None):
                #TODO send ticket to fraud queue
                pass
        # Send to grouper for any open hosted phishing tickets
        if incident.hosted_status == 'HOSTED' \
                and incident.type == 'PHISHING' \
                and incident.phishstory_status == 'OPEN':
            app.send_task('run.group', args=(incident.ticketId,))
    except Exception as e:
        logger.error("Unable to post process data {}:{}".format(incident, e.message))
