import logging
import re
from datetime import datetime
from pprint import pformat

from dcdatabase.phishstorymongo import PhishstoryMongo

from dcumiddleware.dcuapi_functions import DCUAPIFunctions
from dcumiddleware.interfaces.strategy import Strategy
from dcumiddleware.urihelper import URIHelper
from dcumiddleware.viphelper import CrmClientApi, RegDbAPI, VipClients, RedisCache


class PhishingStrategy(Strategy):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._urihelper = URIHelper(settings)
        self._db = PhishstoryMongo(settings)
        self._api = DCUAPIFunctions(settings)
        _redis = RedisCache(settings)
        self._premium = CrmClientApi(_redis)
        self._regdb = RegDbAPI(_redis)
        self._vip = VipClients(settings, _redis)

    def close_process(self, data, close_reason):
        data['close_reason'] = close_reason
        self._db.close_incident(data.get('ticketId'), data)
        # Close upstream ticket as well
        if self._api.close_ticket(data.get('ticketId')):
            self._logger.info("Ticket {} closed successfully".format(data.get('ticketId')))
        else:
            self._logger.warning("Unable to close upstream ticket {}".format(data.get('ticketId')))
        return data

    def process(self, data, **kwargs):
        # determine if domain is hosted at godaddy
        # TODO call to cmapservicehelpf for domain/host info

        self._logger.info("Received request {}".format(pformat(data)))

        # regex to determine if godaddy is the host
        regex = re.compile('[^a-zA-Z]')
        host = data['data']['domainQuery']['host']['name']
        hostname = regex.sub('', host)

        # regex to determine if godaddy is the registrar
        reg = data['data']['domainQuery']['registrar']['name']
        registrar = regex.sub('', reg)

        # TODO change following get host info from returned cmap service data
        if 'GODADDY' in hostname.upper():
            status = "HOSTED"
        elif 'GODADDY' in registrar.upper():
            status = "REGISTERED"
        elif 'GODADDY' not in hostname.upper() and 'GODADDY' not in registrar.upper():
            status = "FOREIGN"
        else:
            self._logger.warn("Unknown hosted status for incident: {}".format(pformat(data)))
            status = "UNKNOWN"

        data['hosted_status'] = status
        if status in ["FOREIGN", "UNKNOWN"]:
            return self.close_process(data, "unworkable")

        # add domain create date if domain is registered only
        # TODO must have domain create date from cmap service, need to update element name - placeholder 'create_date'
        if status is "REGISTERED":
            data['d_create_date'] = data['data']['domainQuery']['create_date']

        # add shopper info if we can find it
        # TODO must have shopper create date from cmap service, need to update element name - placeholder 'create_date'
        sid = data['data']['shopperQuery']['id']
        s_create_date = data['data']['shopperQuery']['create_date']

        if sid and s_create_date:
            data['sid'] = sid
            data['s_create_date'] = s_create_date

            # if shopper is premium, add it to their mongo record
            # TODO must have shopper VIP status, PortfolioType or, PortfolioTypeID from cmap service, need to update element name - placeholder 'VIP'
            premier = data['data']['shopperQuery']['profile']['VIP']
            if premier is not None:
                data['premier'] = premier

            # get the number of domains in the shopper account
            # TODO must have shopper domain count from cmap service, need to update element name - placeholder 'domaincount'
            domain_count = data['data']['shopperQuery']['shopperid']['domaincount']
            if domain_count is not None:
                data['domain_count'] = domain_count

            # get parent/child reseller api account status
            # TODO: This code should be moved outside of the (if sid and s_create_date) block, as it is independent
            parentchild = str(data['data']['domainQuery']['reseller']['parentChild']).split(',')
            if parentchild is not "null":
                data['parent_api_account'] = parentchild[0].split(':')[1]
                data['child_api_account'] = parentchild[1].split(':')[1]

            # get blacklist status - DO NOT SUSPEND special shopper accounts
            if self._vip.query_blacklist(sid):
                data['blacklist'] = True

            # get blacklist status - DO NOT SUSPEND special domain
            # TODO: This code should be moved outside of the (if sid and s_create_date) block, as it is independent
            if self._vip.query_blacklist(data.get('sourceDomainOrIp')):
                data['blacklist'] = True

        else:
            # TODO: Implement a better way to determine if the vip status is Unconfirmed
            data['vip_unconfirmed'] = True

        # Add hosted_status to incident
        res = self._urihelper.resolves(data.get('source'))
        if res or data.get('proxy'):
            iid = self._db.add_new_incident(data.get('ticketId'), data)
            if iid:
                self._logger.info("Incident {} inserted into database".format(iid))
                if res:
                    # Attach crits data if it resolves
                    source = data.get('source')
                    screenshot_id, sourcecode_id = self._db.add_crits_data(self._urihelper.get_site_data(source),
                                                                           source)
                    data = self._db.update_incident(iid, dict(screenshot_id=screenshot_id,
                                                              sourcecode_id=sourcecode_id,
                                                              last_screen_grab=datetime.utcnow()))
            else:
                self._logger.error("Unable to insert {} into database".format(iid))
        else:
            data = self.close_process(data, "unresolvable")

        return data
