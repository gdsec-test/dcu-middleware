import logging
import re
from datetime import datetime
from pprint import pformat

from dcdatabase.phishstorymongo import PhishstoryMongo

from dcumiddleware.dcuapi_functions import DCUAPIFunctions
from dcumiddleware.interfaces.strategy import Strategy
from dcumiddleware.urihelper import URIHelper
from dcumiddleware.cmapservicehelper import CmapServiceHelper


class PhishingStrategy(Strategy):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._urihelper = URIHelper(settings)
        self._db = PhishstoryMongo(settings)
        self._api = DCUAPIFunctions(settings)
        self._cmapservice = CmapServiceHelper(settings)

    def close_process(self, data, close_reason):
        data['close_reason'] = close_reason
        self._db.close_incident(data['ticketId'], data)
        # Close upstream ticket as well
        if self._api.close_ticket(data['ticketId']):
            self._logger.info("Ticket {} closed successfully".format(data['ticketId']))
        else:
            self._logger.warning("Unable to close upstream ticket {}".format(data['ticketId']))
        return data

    def process(self, data, **kwargs):
        """
        Returns a dictionary that is the combination of the provided abuse API data and cmap service along with
        additional information based on cmap service data including the hosted/registered status.
        :param data: dict provided by abuse API
        :return merged_data: dict of merged abuse API dict and cmap servide dict plus other enriched data
        """

        self._logger.info("Received request {}".format(pformat(data)))

        # query cmap service with domain or ip from API data
        subdomain = data.get('sourceSubDomain')
        if subdomain is not None:
            cmapdata = self._cmapservice.domain_query(subdomain)
        else:
            cmapdata = self._cmapservice.domain_query(data['sourceDomainOrIp'])

        status = None

        # determine if domain is hosted at godaddy
        try:
            # merge API dict data with cmap service dict data
            merged_data = self._cmapservice.api_cmap_merge(data, cmapdata)

            # regex to determine if godaddy is the host and registrar
            regex = re.compile('[^a-zA-Z]')
            host = merged_data.get('data', {}).get('domainQuery', {}).get('host', {}).get('name', None)
            hostname = regex.sub('', host) if host is not None else None
            reg = merged_data.get('data', {}).get('domainQuery', {}).get('registrar', {}).get('name', None)
            registrar = regex.sub('', reg) if reg is not None else None

            # set status based on API domain/IP and returned cmap service data
            if hostname and 'GODADDY' in hostname.upper():
                status = "HOSTED"
            elif registrar and re.search(r'(?:GODADDY|WILDWESTDOMAINS)', registrar.upper()):
                status = "REGISTERED"
            elif hostname is None or registrar is None:
                self._logger.warn("Unknown registrar/host status for incident: {}.".format(data['ticketId']))
                status = "UNKNOWN"
            elif 'GODADDY' not in hostname.upper() and 'GODADDY' not in registrar.upper():
                status = "FOREIGN"
        except Exception as e:
            # if cmap service query has a problem with the given domain/IP, status is set to UNKNOWN and merged_data
            # is set only to API data
            self._logger.warn("Unknown registrar/host status for incident: {}. {}".format(pformat(data), e.message))
            status = "UNKNOWN"
            merged_data = data

        # set hosted status: HOSTED, REGISTERED, FOREIGN, or UNKNOWN
        merged_data['hosted_status'] = status

        # close incident if it is foreign or unknown
        if status in ["FOREIGN", "UNKNOWN"]:
            return self.close_process(merged_data, "unworkable")

        # if no shopper number found then no way to confirm vip status
        vip = merged_data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('shopperId', None)
        if vip is None:
            merged_data['vip_unconfirmed'] = True

        # get blacklist status - DO NOT SUSPEND special shopper accounts & DO NOT SUSPEND special domain
        shopper_blacklist = merged_data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('vip', {}).get('blacklist', True)
        domain_blacklist = merged_data.get('data', {}).get('domainQuery', {}).get('blacklist', True)
        if shopper_blacklist is True or domain_blacklist is True:
            merged_data['blacklist'] = True

        # Add hosted_status to incident
        res = self._urihelper.resolves(merged_data.get('source', False))
        if res or merged_data.get('proxy', False):
            iid = self._db.add_new_incident(merged_data['ticketId'], merged_data)
            if iid:
                self._logger.info("Incident {} inserted into database".format(iid))
                if res:
                    # Attach crits data if it resolves
                    source = merged_data.get('source', None)
                    screenshot, sourcecode = self._urihelper.get_site_data(source)
                    target = 'GoDaddy' if self._urihelper.gd_phish(sourcecode) else merged_data.get('target', '')
                    screenshot_id, sourcecode_id = self._db.add_crits_data((screenshot, sourcecode), source)
                    merged_data = self._db.update_incident(iid, dict(screenshot_id=screenshot_id,
                                                                     sourcecode_id=sourcecode_id,
                                                                     last_screen_grab=datetime.utcnow(),
                                                                     target=target))
            else:
                self._logger.error("Unable to insert {} into database".format(iid))
        else:
            merged_data = self.close_process(merged_data, "unresolvable")

        return merged_data
