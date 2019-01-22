import logging.config
import os
from pprint import pformat

import yaml
from celery import Celery, chain
from celery.utils.log import get_task_logger
from dcdatabase.phishstorymongo import PhishstoryMongo

from celeryconfig import CeleryConfig
from dcumiddleware.cmapservicehelper import CmapServiceHelper
from dcumiddleware.routinghelper import RoutingHelper
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

db = PhishstoryMongo(app_settings)
routing_helper = RoutingHelper(app, db)

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
    chain(_load_and_enrich_data.s(data),
          _route_to_brand_services.s(),
          _printer.s())()


''' PRIVATE TASKS'''


@app.task(bind=True, default_retry_delay=app_settings.TASK_TIMEOUT, max_retries=app_settings.TASK_MAX_RETRIES)
def _load_and_enrich_data(self, data):
    """
    Loads the data from CMAP and merges it with information gained from CMAP Service
    :param data:
    :return:
    """
    cmap_data = {}
    cmap_helper = CmapServiceHelper(app_settings)
    domain = data.get('sourceSubDomain') if data.get('sourceSubDomain') else data.get('sourceDomainOrIp')

    try:
        # Retreive CMAP data from CMapServiceHelper
        cmap_data = cmap_helper.domain_query(domain)
    except Exception as e:
        ticket = data.get('ticketId')
        # If we have reached the max retries allowed, abort the process and nullify the task chain
        if self.request.retries == self.max_retries:
            logger.error("Max retries exceeded for {} : {}".format(ticket, e.message))
            # Flag DB for the enrichment failure
            data['failedEnrichment'] = True

        else:
            logger.error("Error while processing: {}. Retrying...".format(ticket))
            self.retry(exc=e)

    # return the result of merging the CMap data with data gathered from the API
    return db.update_incident(data.get('ticketId'), cmap_helper.api_cmap_merge(data, cmap_data))


@app.task
def _route_to_brand_services(data):
    """
    Routes data to the appropriate Brand Service to be processed further
    :param data:
    :return:
    """
    return routing_helper.route(data)


@app.task
def _printer(data):
    if data:
        logger.info("Successfully processed {}".format(pformat(data)))
