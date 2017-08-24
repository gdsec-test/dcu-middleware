import re
import os
import yaml
import logging.config

from pprint import pformat
from celery import Celery, chain
from celery.utils.log import get_task_logger

from celeryconfig import CeleryConfig
from settings import config_by_name
from dcumiddleware.cmapservicehelper import CmapServiceHelper
from dcumiddleware.routinghelper import RoutingHelper
from dcdatabase.phishstorymongo import PhishstoryMongo as db


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
    chain(_load_and_enrich_data.s(data),
          _add_data_to_database.s(),
          _route_to_brand_services.s(),
          _printer.s())()

##### PRIVATE TASKS #####


@app.task
def _load_and_enrich_data(data):
    """
    Loads the data from CMAP and merges it with information gained from CMAP Service
    :param data:
    :return:
    """
    cmap_helper = CmapServiceHelper(app_settings)

    # Retreive CMAP data from CMapServiceHelper
    subdomain = data.get('sourceSubDomain', None)
    cmap_data = cmap_helper.domain_query(subdomain) if subdomain \
        else cmap_helper.domain_query(data.get('sourceDomainOrIp', None))

    # return the result of merging the CMap data with data gathered from the API
    return cmap_helper.api_cmap_merge(data, cmap_data)


@app.task
def _add_data_to_database(data):
    dcu_db = db(app_settings)
    iid = dcu_db.add_new_incident(data.get('ticketId', None), data)
    if iid:
        logger.info("Incident {} inserted into the database.".format(iid))
        # Put the ticket in an intermediary stage while it is being processed by brand services.
        data = dcu_db.update_incident(iid, dict(phishstory_status='PROCESSING'))
    else:
        logger.error("Unable to insert {} into the database.".format(iid))
    return data


@app.task
def _route_to_brand_services(data):
    """
    Routes data to the appropriate Brand Service to be processed further
    :param data:
    :return:
    """
    routing_helper = RoutingHelper(app)

    host_brand = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('brand', None)
    registrar_brand = data.get('data', {}).get('domainQuery', {}).get('registrar', {}).get('brand', None)
    routing_helper.route(host_brand, registrar_brand, data)

    return data


@app.task
def _printer(data):
    if data:
        logger.info("Successfully processed {}".format(pformat(data)))
