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
from dcumiddleware.reviews import FraudReview, BasicReview
from dcumiddleware.urihelper import URIHelper
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
    """
    Places the incident on a basic hold
    :param data:
    :return:
    """
    review = BasicReview(app_settings)
    review.place_in_review(data, datetime.utcnow() + timedelta(seconds=app_settings.HOLD_TIME))


@app.task(name='run.malicious')
def malicious(data):
    """
    Places the incident on a fraud hold, and notifies fraud via email if no holds currently
    exist for this domain
    :param data:
    :return:
    """
    review = FraudReview(app_settings)
    urihelper = URIHelper(app_settings)
    domain = urihelper.domain_for_ticket(data)
    fhold = urihelper.fraud_holds_for_domain(domain)
    if fhold:
        review.place_in_review(data, fhold)
    else:
        rdata = Incident(review.place_in_review(data, datetime.utcnow() + timedelta(seconds=app_settings.HOLD_TIME)))
        send_malicious_notification(rdata)


@app.task(name='run.process')
def process(data):
    """
    Processes data from the dcumiddleware queue.
    :param data:
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

    if strategy:
        rdata = strategy.process(incident)
        if rdata:
            logger.info("Successfully processed {}".format(rdata))
            post_process(rdata)
        else:
            logger.error("Unable to process incident {}, no data returned".format(incident))
    else:
        logger.warning("No strategy available for {}".format(incident.type))


def post_process(data):
    """
    This function handles post processing the data for basic fraud detection, grouping etc.
    :param data:
    :return:
    """
    try:
        logger.info("Post-processing {}".format(data))
        # If the s_create_date is less than x days old, put on review and send to fraud if not already on hold
        if data.phishstory_status == 'OPEN' \
                and data.s_create_date \
                and data.s_create_date > datetime.utcnow() - timedelta(days=app_settings.NEW_ACCOUNT) \
                and not data.fraud_hold_until:
            review = FraudReview(app_settings)
            rdata = Incident(
                review.place_in_review(data, datetime.utcnow() + timedelta(seconds=app_settings.HOLD_TIME)))
            send_young_account_notification(rdata)

        # Send to grouper for any open hosted phishing tickets
        if data.hosted_status == 'HOSTED' \
                and data.type == 'PHISHING' \
                and data.phishstory_status == 'OPEN':
            app.send_task('run.group', args=(data.ticketId,))
    except Exception as e:
        logger.error("Unable to post process data {}:{}".format(data, e.message))


def send_young_account_notification(data):
    """
   Sends a young account notification to fraud
   :param data:
   :return:
   """
    payload = {'from': app_settings.NOTIFY_FROM, 'to': app_settings.NOTIFY_TO, 'templateNamespacekey': 'Fraud',
               'templateTypeKey': 'YoungShopper',
               'substitutionValues': {'account number': data.sid, 'shopper creation date': data.s_create_date,
                                      'Domain name': data.sourceDomainOrIp, 'malicious activity': data.type,
                                      'sanitized URL': data.source}}
    app.send_task('run.sendmail', args=(payload,))


def send_malicious_notification(data):
    """
    Sends a malicious notification to fraud
    :param data:
    :return:
    """
    payload = {'from': app_settings.NOTIFY_FROM, 'to': app_settings.NOTIFY_TO, 'templateNamespacekey': 'Fraud',
               'templateTypeKey': 'SuspectedMalicious',
               'substitutionValues': {'account number': data.sid, 'Domain name': data.sourceDomainOrIp,
                                      'malicious activity': data.type, 'sanitized URL': data.source}}
    app.send_task('run.sendmail', args=(payload,))
