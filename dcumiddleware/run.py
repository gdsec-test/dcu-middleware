import logging.config
import os
import socket
from typing import Union
from urllib.parse import quote, urlparse
from uuid import UUID

import yaml
from celery import Celery, bootsteps, chain
from celery.utils.log import get_task_logger
from csetutils.celery import instrument
from dcdatabase.kelvinmongo import KelvinMongo
from dcdatabase.phishstorymongo import PhishstoryMongo
from func_timeout import FunctionTimedOut, func_timeout
from kombu.common import QoS
from pymongo import MongoClient

from dcumiddleware.celeryconfig import CeleryConfig
from dcumiddleware.settings import config_by_name
from dcumiddleware.utilities.apihelper import APIHelper
from dcumiddleware.utilities.cmapservicehelper import CmapServiceHelper
from dcumiddleware.utilities.kelvinhelper import KelvinHelper
from dcumiddleware.utilities.routinghelper import RoutingHelper
from dcumiddleware.utilities.shopperhelper import ShopperApiHelper

# Grab the correct settings based on environment
env = os.getenv('sysenv', 'unit-test')
app_settings = config_by_name[env]()

app = Celery()
app.config_from_object(CeleryConfig())
logger = get_task_logger('celery.tasks')
log_level = os.getenv('LOG_LEVEL', 'INFO')

ACTION_KEY = 'action'
BLACKLIST_KEY = 'blacklist'
BLACKLIST_ENTITY_KEY = 'entity'
BRAND_KEY = 'brand'
DATA_KEY = 'data'
DIABLO_WHMCS = 'Diablo WHMCS'
DOMAIN_ID_KEY = 'domainId'
DOMAIN_Q_KEY = 'domainQuery'
FAILED_ENRICHMENT_KEY = 'failedEnrichment'
FALSE_POSITIVE = 'false_positive'
GODADDY_BRAND = 'GODADDY'
GUID_KEY = 'guid'
HOST_KEY = 'host'
KEY_ABUSE_VERIFIED = 'abuseVerified'
KEY_BLACKLIST = 'blacklist'
KEY_CONTAINER_ID = 'containerId'
KEY_CREATED_DATA = 'createdDate'
KEY_DC = 'dataCenter'
KEY_FRIENDLY_NAME = 'friendlyName'
KEY_GUID = 'guid'
KEY_HOSTNAME = 'hostname'
KEY_IP = 'ip'
KEY_METADATA = 'metadata'
KEY_MWP_ID = 'mwpId'
KEY_PRODUCT = 'product'
KEY_PORTFOLIO_TYPE = 'portfolioType'
KEY_PRIVATE_LABEL_ID = 'privateLabelId'
KEY_REPORTER = 'reporter'
KEY_REPORTER_CID = 'reporting_customer_id'
KEY_RESELLER = 'reseller'
KEY_SHOPPER_ID = 'shopperId'
KEY_CUSTOMER_ID = 'customerId'
KEY_USERNAME = 'username'
KEY_VIP = 'vip'
KEY_ENTITLEMENT_ID = 'entitlementId'
NOT_FOUND = 'NotFound'
REGISTRAR_KEY = 'registrar'
RESOLVED = 'resolved'
SHOPPER_INFO_KEY = 'shopperInfo'
SHOPPER_KEY = 'shopperId'
CUSTOMER_KEY = 'customerId'
SOURCE_KEY = 'sourceDomainOrIp'
TICKET_ID_KEY = '_id'
VIP_KEY = 'vip'

apm = instrument('middleware', env=env, metric_sets=['dcumiddleware.metrics.Metrics'])


# turning off global qos in celery
class NoChannelGlobalQoS(bootsteps.StartStopStep):
    requires = {'celery.worker.consumer.tasks:Tasks'}

    def start(self, c):
        qos_global = False

        c.connection.default_channel.basic_qos(0, c.initial_prefetch_count, qos_global)

        def set_prefetch_count(prefetch_count):
            return c.task_consumer.qos(
                prefetch_count=prefetch_count,
                apply_global=qos_global,
            )

        c.qos = QoS(set_prefetch_count, c.initial_prefetch_count)


app.steps['consumer'].add(NoChannelGlobalQoS)

# Configure DCU celery metrics
metricset = apm._metrics.get_metricset('dcumiddleware.metrics.Metrics')


def get_blacklist_info(source: str, domain_shopper: str, host_shopper: str) -> Union[list, None]:
    source_bl_record = blacklist_collection.find_one({BLACKLIST_ENTITY_KEY: source})
    if source_bl_record:
        return source_bl_record.get(ACTION_KEY) if source_bl_record else None

    host_shopper_bl_record = blacklist_collection.find_one({BLACKLIST_ENTITY_KEY: host_shopper})
    domain_shopper_bl_record = blacklist_collection.find_one({BLACKLIST_ENTITY_KEY: domain_shopper})

    if host_shopper and not domain_shopper:
        return host_shopper_bl_record.get(ACTION_KEY) if host_shopper_bl_record else None

    if domain_shopper and not host_shopper:
        return domain_shopper_bl_record.get(ACTION_KEY) if domain_shopper_bl_record else None

    if domain_shopper and host_shopper and domain_shopper_bl_record and host_shopper_bl_record:
        return host_shopper_bl_record.get(ACTION_KEY) if host_shopper_bl_record else None

    return None


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

    product = hosted.get(KEY_PRODUCT, None)
    host_here = hosted.get(BRAND_KEY, None) == GODADDY_BRAND and product not in app_settings.REGISTERED_ONLY_PRODUCTS

    miss_shopper = hosted.get(SHOPPER_KEY, None) is None
    miss_customer = hosted.get(CUSTOMER_KEY, None) is None
    miss_product = product is None
    miss_guid = hosted.get(GUID_KEY, None) is None
    miss_whmcs_user = product == DIABLO_WHMCS and hosted.get(KEY_USERNAME, None) in (None, NOT_FOUND)
    host_enrich_fail = host_here and (miss_shopper or miss_customer or miss_product or miss_guid or miss_whmcs_user)

    registered_here = domain.get(BRAND_KEY, None) == GODADDY_BRAND
    missing_domain = domain.get(DOMAIN_ID_KEY, None) is None
    missing_domain_shopper = shopper.get(SHOPPER_KEY, None) is None
    missing_domain_customer = shopper.get(CUSTOMER_KEY, None) is None
    domain_enrich_fail = registered_here and (missing_domain or missing_domain_shopper or missing_domain_customer)

    if host_enrich_fail or domain_enrich_fail:
        return False
    return True


def validate_abuse_verified(ticket: dict, enrichment: dict, domain: str, ip: str) -> None:
    cmap_helper = CmapServiceHelper(app_settings)
    metadata = ticket.get(KEY_METADATA, {})
    hosted_enrichment = enrichment.get(DATA_KEY, {}).get(DOMAIN_Q_KEY, {}).get(HOST_KEY, {})
    mismatch = False

    if metadata.get(KEY_PRODUCT) != hosted_enrichment.get(KEY_PRODUCT):
        hosted_enrichment[KEY_PRODUCT] = metadata.get(KEY_PRODUCT)
        mismatch = True
        # If product doesn't match, the hosted GUID is definitely wrong.
        hosted_enrichment.pop(KEY_GUID, None)

    if metadata.get(KEY_GUID) != hosted_enrichment.get(KEY_GUID):
        hosted_enrichment[KEY_GUID] = metadata.get(KEY_GUID)
        mismatch = True

    if metadata.get(KEY_SHOPPER_ID) != hosted_enrichment.get(KEY_SHOPPER_ID):
        hosted_enrichment[KEY_SHOPPER_ID] = metadata.get(KEY_SHOPPER_ID)
        hosted_enrichment.pop(KEY_CREATED_DATA, None)

    if mismatch:
        # Remove all other enriched fields.
        hosted_enrichment.pop(KEY_DC, None)
        hosted_enrichment.pop(KEY_CONTAINER_ID, None)
        hosted_enrichment.pop(KEY_HOSTNAME, None)
        hosted_enrichment.pop(KEY_IP, None)
        hosted_enrichment.pop(KEY_SHOPPER_ID, None)
        hosted_enrichment.pop(KEY_MWP_ID, None)
        hosted_enrichment.pop(KEY_CREATED_DATA, None)
        hosted_enrichment.pop(KEY_FRIENDLY_NAME, None)
        hosted_enrichment.pop(KEY_PRIVATE_LABEL_ID, None)
        hosted_enrichment.pop(KEY_RESELLER, None)
        hosted_enrichment[KEY_VIP] = {
            KEY_BLACKLIST: False,
            KEY_PORTFOLIO_TYPE: None,
            KEY_SHOPPER_ID: None
        }

        product = hosted_enrichment.get(KEY_PRODUCT, '')
        # Perform a product specific enrichment.
        hosted_enrichment = cmap_helper.product_lookup(
            domain,
            hosted_enrichment[KEY_GUID],
            ip,
            product
        )

        hosted_enrichment.update(cmap_helper.shopper_lookup(hosted_enrichment[KEY_SHOPPER_ID]))
        enrichment.get(DATA_KEY, {}).get(DOMAIN_Q_KEY, {})[HOST_KEY] = hosted_enrichment


# setup logging
path = '/app/logging.yaml'
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
blacklist_client = MongoClient(app_settings.DBURL)
blacklist_db = blacklist_client[app_settings.DB]
blacklist_collection = blacklist_db[app_settings.BLACKLIST_COLLECTION]

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


# We want to ack late here - if we get exceptions for any reason, we want the task to keep trying.
@app.task(name='run.sync_child_safety', acks_late=True, max_retries=0, autoretry_for=(Exception,))
def sync_child_safety(data):
    # Migrate some fields to match legacy kelvin-service behavior.
    data['ticketID'] = data['ticketId']
    data['sourceDomainOrIP'] = data['sourceDomainOrIp']
    if data.get('target') is None:
        data['target'] = ''
    if data.get('info') is None:
        data['info'] = ''
    kelvin_helper = KelvinHelper(config=app_settings)
    kelvin_helper.process(data)


@app.task(name='run.sync_customer_security', acks_late=True, max_retries=0, autoretry_for=(Exception,))
def sync_customer_security(data):
    # We only want to process each ticket once, we will get a large number of these events
    # during ticket backfills.
    ticketId = data.get('ticketId')
    result = db.get_incident(ticketId)
    if not result:
        db.add_new_incident(ticketId, data)
        chain(process.s(data))()


@app.task(name='run.process')
def process(data):
    """
    Main processing pipeline for incidents submitted from the API
    :param data:
    :return:
    """
    data = db.get_incident(data.get('ticketId'))
    chain(_load_and_enrich_data.s(data),
          _check_for_blacklist_auto_actions.s(),
          _route_to_brand_services.s())()


@app.task(name='run.sync_attribute', acks_late=True, max_retries=0, autoretry_for=(Exception,))
def sync_attribute(ticket_id, field, value):
    """
    Updates P3 mongo ticketId field name with new value.
    :param ticket_id:
    :param field:
    :param value:
    :return:
    """
    if ticket_id.startswith('DCUK'):
        kdb = KelvinMongo(app_settings.KELVIN_DBNAME, app_settings.KELVIN_DB_URL, 'incidents')
        return kdb.update_incident(ticket_id, {field: value})
    else:
        return db.update_incident(ticket_id, {field: value})


''' PRIVATE TASKS'''


def _is_uuid(uuid_str: str) -> bool:
    try:
        UUID(uuid_str)
        return True
    except:  # noqa: E722
        pass
    return False


@app.task(name='run._load_and_enrich_data', bind=True, default_retry_delay=app_settings.TASK_TIMEOUT,
          max_retries=app_settings.TASK_MAX_RETRIES)
def _load_and_enrich_data(self, data):
    """
    Loads the data from CMAP and merges it with information gained from CMAP Service
    :param data:
    :return:
    """
    ticket_id = data.get('ticketId')
    domain_name = data.get('sourceDomainOrIp')
    sub_domain_name = data.get('sourceSubDomain')
    source = data.get('source')
    reporter: str = data.get(KEY_REPORTER)

    # Ensure we correctly encode all special characters.
    url_path = quote(urlparse(source).path)
    timeout_in_seconds = 2
    domain_name_ip = sub_domain_ip = ip = None
    cmap_data = {}
    cmap_helper = CmapServiceHelper(app_settings)
    shopper_api_helper = ShopperApiHelper(app_settings.SHOPPER_API_URL, app_settings.SHOPPER_API_CERT_PATH,
                                          app_settings.SHOPPER_API_KEY_PATH)
    had_failed_enrichment = data.pop(FAILED_ENRICHMENT_KEY, False)

    # The transition to customer IDs instead of shopper IDs is starting, but we need to move a portion of the pipeline at a time.
    if _is_uuid(reporter):
        data[KEY_REPORTER_CID] = reporter
        data[KEY_REPORTER] = shopper_api_helper.get_shopper_id(reporter)
    elif reporter and reporter.isnumeric():
        data[KEY_REPORTER_CID] = shopper_api_helper.get_customer_id(reporter)
    else:
        data[KEY_REPORTER_CID] = None

    if KEY_METADATA in data and (
            KEY_SHOPPER_ID not in data[KEY_METADATA] or data[KEY_METADATA][KEY_SHOPPER_ID] == '') and KEY_CUSTOMER_ID in \
            data[KEY_METADATA]:
        data[KEY_METADATA][KEY_SHOPPER_ID] = shopper_api_helper.get_shopper_id(data[KEY_METADATA][KEY_CUSTOMER_ID])
        logger.info(
            f'Obtained shopper id {data[KEY_METADATA][KEY_SHOPPER_ID]} for customer id {data[KEY_METADATA][KEY_CUSTOMER_ID]}')

    try:
        domain_name_ip = func_timeout(timeout_in_seconds, socket.gethostbyname, args=(domain_name,))
    except (FunctionTimedOut, socket.gaierror) as e:
        logger.error(f'Error while determining domain IP for {ticket_id} : {e}')

    try:
        sub_domain_ip = func_timeout(timeout_in_seconds, socket.gethostbyname, args=(sub_domain_name,))
    except (FunctionTimedOut, socket.gaierror) as e:
        logger.error(f'Error while determining sub-domain IP for {ticket_id} : {e}')

    # If the domain and sub-domain ips match, then send a CMAP query for the domain, as the domain
    # query is more likely to return a guid than the sub-domain query
    domain = domain_name
    ip = domain_name_ip
    if sub_domain_name and sub_domain_ip and domain_name_ip != sub_domain_ip:
        domain = sub_domain_name
        ip = sub_domain_ip
    elif domain_name in app_settings.ENRICH_ON_SUBDOMAIN:
        domain = sub_domain_name

    try:
        # Retrieve CMAP data from CMapServiceHelper
        cmap_data = cmap_helper.domain_query(domain, url_path)

        if KEY_METADATA in data and KEY_ENTITLEMENT_ID in data[KEY_METADATA] and KEY_CUSTOMER_ID in data[KEY_METADATA]:
            entitlement_id = data[KEY_METADATA][KEY_ENTITLEMENT_ID]
            customer_id = data[KEY_METADATA][KEY_CUSTOMER_ID]
            host_data = cmap_helper.product_lookup_entitlement(customer_id, entitlement_id)
            cmap_data.get(DATA_KEY, {}).get(DOMAIN_Q_KEY, {})[HOST_KEY] = host_data
        elif data.get(KEY_ABUSE_VERIFIED):
            validate_abuse_verified(data, cmap_data, domain, ip)

        if not enrichment_succeeded(cmap_data):
            data[FAILED_ENRICHMENT_KEY] = True
            metricset.counter('failed_enrichment', reset_on_collect=True).inc(1)
        elif had_failed_enrichment:
            db.remove_field(ticket_id, FAILED_ENRICHMENT_KEY)
    except Exception as e:
        # If we have reached the max retries allowed, abort the process and nullify the task chain
        if self.request.retries == self.max_retries:
            logger.error(f'Max retries exceeded for {ticket_id} : {e}')
            # Flag DB for the enrichment failure
            data[FAILED_ENRICHMENT_KEY] = True
            metricset.counter('failed_enrichment', reset_on_collect=True).inc(1)
        else:
            logger.error(f'Error while processing: {ticket_id}. Retrying...')
            self.retry(exc=e)

    metricset.counter('successful_enrichment', reset_on_collect=True).inc(1)
    # TODO CMAPT-5069: remove 'shopperID' from cmap_data before sending it to the DB
    # return the result of merging the CMap data with data gathered from the API
    return db.update_incident(ticket_id, cmap_helper.api_cmap_merge(data, cmap_data))


@app.task(name='run._check_for_blacklist_auto_actions')
def _check_for_blacklist_auto_actions(data):
    """
    Checks if ticket is on blocklist and performs automated actions if applicable
    :param data:
    :return:
    """
    if data.get(DATA_KEY, {}).get(DOMAIN_Q_KEY, {}).get(BLACKLIST_KEY) and not data.get(FAILED_ENRICHMENT_KEY, False):
        domain_shopper = data.get(DATA_KEY, {}).get(DOMAIN_Q_KEY, {}).get(SHOPPER_INFO_KEY, {}).get(SHOPPER_KEY, None)
        host_shopper = data.get(DATA_KEY, {}).get(DOMAIN_Q_KEY, {}).get(HOST_KEY, {}).get(SHOPPER_KEY, None)
        source = data.get('sourceSubDomain')
        ticket = data.get(TICKET_ID_KEY)

        result_action = get_blacklist_info(source, domain_shopper, host_shopper)

        if result_action:
            if isinstance(result_action, list):
                result_action = result_action[0]
            if result_action in [FALSE_POSITIVE, RESOLVED]:
                api.close_incident(ticket, result_action)
                db.update_actions_sub_document(ticket, f'closed as {result_action}')
                return
    return data


@app.task(name='run._route_to_brand_services')
def _route_to_brand_services(data):
    """
    Routes data to the appropriate Brand Service to be processed further
    :param data:
    :return:
    """
    if not isinstance(data, dict):
        return

    return routing_helper.route(data)
