import logging.config
import os
import socket
from pprint import pformat

import yaml
from celery import Celery, chain
from celery.utils.log import get_task_logger
from dcdatabase.phishstorymongo import PhishstoryMongo
from dcuprometheuscelery.metrics import getRegistry, setupMetrics
from func_timeout import FunctionTimedOut, func_timeout
from prometheus_client import Counter

from celeryconfig import CeleryConfig
from dcumiddleware.apihelper import APIHelper
from dcumiddleware.cmapservicehelper import CmapServiceHelper
from dcumiddleware.routinghelper import RoutingHelper
from settings import config_by_name

# Grab the correct settings based on environment
env = os.getenv('sysenv', 'dev')
app_settings = config_by_name[env]()

app = Celery()
app.config_from_object(CeleryConfig())
logger = get_task_logger('celery.tasks')
log_level = os.getenv('LOG_LEVEL', 'INFO')

FAILED_ENRICHMENT_KEY = 'failedEnrichment'
DATA_KEY = 'data'
DOMAIN_Q_KEY = 'domainQuery'
BRAND_KEY = 'brand'
SHOPPER_KEY = 'shopperId'
PRODUCT_KEY = 'product'
GUID_KEY = 'guid'
DOMAIN_ID_KEY = 'domainId'
HOST_KEY = 'host'
REGISTRAR_KEY = 'registrar'
GODADDY_BRAND = 'GODADDY'
SHOPPER_INFO_KEY = 'shopperInfo'

# Configure DCU celery metrics
setupMetrics(logger)
failedEnrichmentCounter = Counter(
    'failed_enrichment',
    'Count enrichment failures for processed tickets',
    ['env'],
    registry=getRegistry()
)
enrichmentCounter = Counter(
    'enrichment',
    'Count enrichment attempts for processed tickets',
    ['env'],
    registry=getRegistry()
)


def replace_dict(dict_to_replace):
    """
    Replace empty logging levels in logging.yaml with environment appropriate levels
    :param dict_to_replace: logging.yaml is read into a dict which is passed in
    :return:
    """
    for k, v in list(dict_to_replace.items()):
        if type(v) is dict:
            replace_dict(dict_to_replace[k])
        else:
            if v == 'NOTSET':
                dict_to_replace[k] = log_level


def enrichment_succeeded(data):
    """
    Mark enrichment as failed if we identified the brand as GoDaddy, but do not
    have the information needed to determine the shopper.
    :param data: A dictionary returned by the CMAP service.
    :return:
    """
    hosted = data.get(DATA_KEY, {}).get(DOMAIN_Q_KEY, {}).get(HOST_KEY, {})
    domain = data.get(DATA_KEY, {}).get(DOMAIN_Q_KEY, {}).get(REGISTRAR_KEY, {})
    shopper = data.get(DATA_KEY, {}).get(DOMAIN_Q_KEY, {}).get(SHOPPER_INFO_KEY, {})

    host_here = hosted.get(BRAND_KEY, None) == GODADDY_BRAND

    miss_shopper = hosted.get(SHOPPER_KEY, None) is None
    miss_product = hosted.get(PRODUCT_KEY, None) is None
    miss_guid = hosted.get(GUID_KEY, None) is None
    host_enrich_fail = host_here and (miss_shopper or miss_product or miss_guid)

    registered_here = domain.get(BRAND_KEY, None) == GODADDY_BRAND
    missing_domain = domain.get(DOMAIN_ID_KEY, None) is None
    missing_domain_shopper = shopper.get(SHOPPER_KEY, None) is None
    domain_enrich_fail = registered_here and (missing_domain or missing_domain_shopper)

    if host_enrich_fail or domain_enrich_fail:
        return False
    return True


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
        if not enrichment_succeeded(cmap_data):
            data[FAILED_ENRICHMENT_KEY] = True
    except Exception as e:
        # If we have reached the max retries allowed, abort the process and nullify the task chain
        if self.request.retries == self.max_retries:
            logger.error("Max retries exceeded for {} : {}".format(ticket_id, e))
            # Flag DB for the enrichment failure
            data[FAILED_ENRICHMENT_KEY] = True

        else:
            logger.error("Error while processing: {}. Retrying...".format(ticket_id))
            self.retry(exc=e)

    enrichmentCounter.labels(env=env).inc()
    if data.get(FAILED_ENRICHMENT_KEY, False):
        failedEnrichmentCounter.labels(env=env).inc()

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
