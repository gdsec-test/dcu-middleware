import logging
import logging.config
import os
import yaml
import logging.handlers

from datetime import datetime, timedelta
from pprint import pformat
from celery import Celery, chain
from celery.utils.log import get_task_logger

from celeryconfig import CeleryConfig
from settings import config_by_name
from dcumiddleware.urihelper import URIHelper
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
          _check_godaddy_phish.s(),
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
    subdomain = data.get('sourceSubDomain')
    cmap_data = cmap_helper.domain_query(subdomain) if subdomain \
         else cmap_helper.domain_query(data['sourceDomainOrIp'])

    # return the result of merging the CMap data with data gathered from the API
    return cmap_helper.api_cmap_merge(data, cmap_data)

@app.task
def _route_to_brand_services(data):
    """
    Routes data to the appropriate Brand Service to be processed further
    :param data:
    :return:
    """
    routing_helper = RoutingHelper()
    brands = data.get('brands', ['GoDaddy']) # If we aren't given any brands, default route to GoDaddy

    for brand in brands: #aware of the type here. Should be 'brand' but suggesting making this a list.
        routing_helper.route(brand, data)
        logger.info("Routing {} to {} to be processed by brand services.".format(data, brand))
    return data

@app.task
def _check_godaddy_phish(data):
     """
     Placedholder in case we decided to have the middleware check whether or not a particular domain is a GD Phish
     :param data:
     :return:
     """
     urihelper = URIHelper(app_settings)
     res = urihelper.resolves(data.get('source', False))
     if res or data.get('proxy', False):
         if res:
             source = data.get('source', None)
             screenshot, sourcecode = urihelper.get_site_data(source)
             data['target'] = 'GoDaddy' if urihelper.gd_phish(sourcecode) else data.get('target', '')

     else:
         logger.warn("Unable to resolve incident {}.".format(data['ticketId']))
     return data

@app.task
def _printer(data):
    if data:
        logger.info("Successfully processed {}".format(pformat(data)))

# This task may get moved to another service but for now is being used by PhishNet to update screenshots.
@app.task
def refresh_screenshot(ticket):
    """
    Refresh the screenshot for the given ticket and update the db
    :param: ticket
    """
    dcu_db = db(app_settings)
    ticket_data = dcu_db.get_incident(ticket)
    sourcecode_id = ticket_data.get('sourcecode_id')
    screenshot_id = ticket_data.get('screenshot_id')
    last_screen_grab = ticket_data.get('last_screen_grab', datetime(1970, 1, 1))
    logger.info('Request screengrab refresh for {}'.format(ticket))
    if ticket_data.get('phishstory_status', '') == 'OPEN' \
            and last_screen_grab < (datetime.utcnow() - timedelta(minutes=15)):
        logger.info('Updating screengrab for {}'.format(ticket))
        urihelper = URIHelper(app_settings)
        data = urihelper.get_site_data(ticket_data.get('source'))
        if data:
            screenshot_id, sourcecode_id = dcu_db.add_crits_data(data, ticket_data.get('source'))
            last_screen_grab = datetime.utcnow()
            dcu_db.update_incident(ticket_data.get('ticketId'),
                                   dict(screenshot_id=screenshot_id, sourcecode_id=sourcecode_id,
                                        last_screen_grab=last_screen_grab))
        else:
            logger.error("Unable to refresh screenshot/sourcecode for {}, no data returned".format(ticket))
    return ((datetime.utcnow() - last_screen_grab).total_seconds()), screenshot_id, sourcecode_id
