import logging
import logging.config
import logging.handlers
import os
from datetime import datetime, timedelta
from pprint import pformat

import yaml
from celery import Celery, chain
from celery.utils.log import get_task_logger

from celeryconfig import CeleryConfig
from dcumiddleware.malwarestrategy import MalwareStrategy
from dcumiddleware.netabusestrategy import NetAbuseStrategy
from dcumiddleware.phishingstrategy import PhishingStrategy
from dcumiddleware.reviews import FraudReview, BasicReview
from dcumiddleware.urihelper import URIHelper
from settings import config_by_name

# Grab the correct settings based on environment
app_settings = config_by_name[os.getenv('sysenv') or 'dev']()

app = Celery()
app.config_from_object(CeleryConfig())
logger = get_task_logger('celery.tasks')

# setup logging
path = 'logging.yml'
value = os.getenv('LOG_CFG', None)
if value:
    path = value
if os.path.exists(path):
    with open(path, 'rt') as f:
        lconfig = yaml.safe_load(f.read())
    logging.config.dictConfig(lconfig)
else:
    logging.basicConfig(level=logging.INFO)

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


@app.task
def process(data):
    """
    Main processing pipeline for incidents submitted from the API
    :param data:
    :return:
    """
    chain(_catagorize_and_load.s(data),
          _new_fraud_check.s(),
          _check_group.s(),
          _printer.s(),
          link_error=_error_handler.s())()


@app.task
def hold(data):
    """
    Places the incident on a basic hold
    :param data:
    :return:
    """
    logger.info("Placing {} on review".format(data))
    review = BasicReview(app_settings)
    review.place_in_review(data, datetime.utcnow() + timedelta(seconds=app_settings.HOLD_TIME))


@app.task
def malicious(data):
    """
    Places the incident on a fraud hold, and notifies fraud via email if no holds currently
    exist for this domain
    :param data:
    :return:
    """
    logger.info("Marking {} as intentionally malicious".format(data))
    review = FraudReview(app_settings)
    urihelper = URIHelper(app_settings)
    domain = urihelper.domain_for_ticket(data)
    fhold = urihelper.fraud_holds_for_domain(domain)
    if fhold:
        review.place_in_review(data, fhold, 'intentionally_malicious')
    else:
        logger.warning("Sending {} to fraud for being intentionally malicious".format(data))
        rdata = review.place_in_review(data, datetime.utcnow() + timedelta(seconds=app_settings.HOLD_TIME), 'intentionally_malicious')
        send_malicious_notification(rdata)

##### PRIVATE TASKS #####

@app.task
def _catagorize_and_load(data):
    """
    Processes data from the dcumiddleware queue.
    :param data:
    :return:
    """
    strategy = None
    type = data.get('type')
    if type == "PHISHING":
        strategy = PhishingStrategy(app_settings)
    elif type == "MALWARE":
        strategy = MalwareStrategy(app_settings)
    elif type == "NETABUSE":
        strategy = NetAbuseStrategy(app_settings)

    if strategy:
        return strategy.process(data)
    else:
        logger.warning("No strategy available for {}".format(type))


@app.task
def _new_fraud_check(data):
    """
    This function handles new account fraud detection
    :param data:
    :return data:
    """
    try:
        # If the s_create_date is less than x days old, put on review and send to fraud if not already on hold
        if data.get('phishstory_status') == 'OPEN' \
                and data.get('s_create_date') \
                and data.get('s_create_date') > datetime.utcnow() - timedelta(days=app_settings.NEW_ACCOUNT):
            logger.info("Possible fraud detected on {}".format(pformat(data)))
            review = FraudReview(app_settings)
            urihelper = URIHelper(app_settings)
            fhold = urihelper.fraud_holds_for_domain(data.get('sourceDomainOrIp'))
            if fhold:
                data = review.place_in_review(data.get('ticketId'), fhold, 'new_account')
            else:
                logger.warning("Sending {} to fraud for young account investigation".format(data.get('ticketId')))
                data = review.place_in_review(data.get('ticketId'),
                                              datetime.utcnow() + timedelta(seconds=app_settings.HOLD_TIME), 'new_account')
                send_young_account_notification(data)
    except Exception as e:
        logger.error("Unable to perform new fraud check {}:{}".format(pformat(data), e.message))
    finally:
        return data


@app.task
def _check_group(data):
    """
    Send to grouper for any open hosted phishing tickets
    :param data:
    :return:
    """
    try:
        if data.get('hosted_status') == 'HOSTED' \
                and data.get('type') == 'PHISHING' \
                and data.get('phishstory_status') == 'OPEN':
            logger.info("Sending {} to grouper".format(data.get('ticketId')))
            app.send_task('run.group', args=(data.get('ticketId'),), serializer='json')
    except Exception as e:
        logger.error("Unable to check data for grouping {}:{}".format(pformat(data), e.message))
    finally:
        return data


@app.task
def _printer(data):
    if data:
        logger.info("Successfully processed {}".format(pformat(data)))

@app.task(bind=True)
def _error_handler(self, uuid):
    result = self.app.AsyncResult(uuid)
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
          uuid, result.result, result.traceback))


####### HELPER FUNCTIONS #######

def send_young_account_notification(data):
    """
   Sends a young account notification to fraud
   :param data:
   :return:
   """
    payload = {'from': app_settings.NOTIFY_FROM, 'to': app_settings.NOTIFY_TO, 'templateNamespacekey': 'Fraud',
               'templateTypeKey': 'YoungShopper',
               'substitutionValues': {'account number': data.get('sid'),
                                      'shopper creation date': data.get('s_create_date'),
                                      'Domain name': data.get('sourceDomainOrIp'),
                                      'malicious activity': data.get('type'),
                                      'sanitized URL': data.get('source')}}
    app.send_task('run.sendmail', args=(payload,))


def send_malicious_notification(data):
    """
    Sends a malicious notification to fraud
    :param data:
    :return:
    """
    payload = {'from': app_settings.NOTIFY_FROM, 'to': app_settings.NOTIFY_TO, 'templateNamespacekey': 'Fraud',
               'templateTypeKey': 'SuspectedMalicious',
               'substitutionValues': {'account number': data.get('sid'), 'Domain name': data.get('sourceDomainOrIp'),
                                      'malicious activity': data.get('type'), 'sanitized URL': data.get('source')}}
    app.send_task('run.sendmail', args=(payload,))
