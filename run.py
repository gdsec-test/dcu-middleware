import logging.config
import os
import socket
from pprint import pformat

import yaml
from celery import Celery, chain
from celery.utils.log import get_task_logger
from dcdatabase.phishstorymongo import PhishstoryMongo
from func_timeout import FunctionTimedOut, func_timeout

from celeryconfig import CeleryConfig
from dcumiddleware.apihelper import APIHelper
from dcumiddleware.cmapservicehelper import CmapServiceHelper
from dcumiddleware.routinghelper import RoutingHelper
from settings import config_by_name

# Grab the correct settings based on environment
app_settings = config_by_name[os.getenv('sysenv', 'dev')]()

app = Celery()
app.config_from_object(CeleryConfig())
logger = get_task_logger('celery.tasks')
log_level = os.getenv('LOG_LEVEL', 'INFO')


def replace_dict(dict_to_replace):
    """
    Replace empty logging levels in logging.yaml with environment appropriate levels
    :param dict_to_replace: logging.yaml is read into a dict which is passed in
    :return:
    """
    for k, v in dict_to_replace.iteritems():
        if type(v) is dict:
            replace_dict(dict_to_replace[k])
        else:
            if v == 'NOTSET':
                dict_to_replace[k] = log_level


# setup logging
path = 'logging.yaml'
if os.path.exists(path):
    with open(path, 'rt') as f:
        lconfig = yaml.safe_load(f.read())
    replace_dict(lconfig)
    logging.config.dictConfig(lconfig)
else:
    logging.basicConfig(level=logging.INFO)

db = PhishstoryMongo(app_settings)
api = APIHelper(app_settings)
routing_helper = RoutingHelper(app, api, db)


"""
Sample data:
{'info': u'My spam Farm is better than yours...',
 'sourceDomainOrIp': u'spam.com',
 'ticketId': u'DCU000001053',
 'target': u'The spam Brothers',
 'reporter': u'10101010',
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
    ticket_id = data.get('ticketId')
    domain_name = data.get('sourceDomainOrIp')
    sub_domain_name = data.get('sourceSubDomain')
    timeout_in_seconds = 2
    domain_name_ip = sub_domain_ip = None
    cmap_data = {}
    cmap_helper = CmapServiceHelper(app_settings)

    data.pop('failedEnrichment', None)

    try:
        domain_name_ip = func_timeout(timeout_in_seconds, socket.gethostbyname, args=(domain_name,))
    except (FunctionTimedOut, socket.gaierror) as e:
        logger.error("Error while determining domain IP for {} : {}".format(ticket_id, e))

    try:
        sub_domain_ip = func_timeout(timeout_in_seconds, socket.gethostbyname, args=(sub_domain_name,))
    except (FunctionTimedOut, socket.gaierror) as e:
        logger.error("Error while determining sub-domain IP for {} : {}".format(ticket_id, e))

    # If the domain and sub-domain ips match, then send a CMAP query for the domain, as the domain
    # query is more likely to return a guid than the sub-domain query
    domain = domain_name
    if sub_domain_name and sub_domain_ip and domain_name_ip != sub_domain_ip:
        domain = sub_domain_name
    elif domain_name in app_settings.ENRICH_ON_SUBDOMAIN:
        domain = sub_domain_name

    try:
        # Retrieve CMAP data from CMapServiceHelper
        cmap_data = cmap_helper.domain_query(domain)

    except Exception as e:
        # If we have reached the max retries allowed, abort the process and nullify the task chain
        if self.request.retries == self.max_retries:
            logger.error("Max retries exceeded for {} : {}".format(ticket_id, e.message))
            # Flag DB for the enrichment failure
            data['failedEnrichment'] = True

        else:
            logger.error("Error while processing: {}. Retrying...".format(ticket_id))
            self.retry(exc=e)

    # return the result of merging the CMap data with data gathered from the API
    return db.update_incident(ticket_id, cmap_helper.api_cmap_merge(data, cmap_data))


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
        logger.info("Successfully processed {}".format(data['_id']))
        logger.debug("Successfully processed {}".format(pformat(data)))
