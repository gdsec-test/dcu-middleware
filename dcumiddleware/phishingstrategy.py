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

        # Retrieve the cmap data and merge it with the data obtained from the API
        cmapdata = self._get_cmap_data(data)
        merged_data = self._merge_cmap_data(data, cmapdata)

        # if no shopper number found then no way to confirm vip status
        merged_data['vip_unconfirmed'] = self.is_unconfirmed_vip(merged_data)

        # get blacklist status - DO NOT SUSPEND special shopper accounts & DO NOT SUSPEND special domain
        merged_data['blacklist'] = self.is_blacklisted(merged_data)

        screenshot, sourcecode, source, target = '', '', '', ''
        res = self._urihelper.resolves(merged_data.get('source', False))
        if res or merged_data.get('proxy', False):
            if res:
                source = merged_data.get('source', None)
                screenshot, sourcecode = self._urihelper.get_site_data(source)
                target = 'GoDaddy' if self._urihelper.gd_phish(sourcecode) else merged_data.get('target', '')
        else:
            merged_data['hosted_status'] = self.UNKNOWN
            self._logger.warn("Unable to resolve incident {} at {}".format(merged_data['ticketId'], source))
            return self.close_process(merged_data, self.UNRESOLVABLE)

        # set hosted status: HOSTED, REGISTERED, FOREIGN, or UNKNOWN
        merged_data['hosted_status'] = self._get_hosted_status(merged_data)

        # close incident if it is unknown
        if merged_data['hosted_status'] == self.UNKNOWN:
            return self.close_process(merged_data, self.UNWORKABLE)

        # At this point we have a site that resolves/proxied and is either a FOREIGN site targeting GoDaddy or any
        # variation of a workable hosted status. Create an entry, and if the site resolves, add crits data.
        if (merged_data['hosted_status'] == self.FOREIGN and target == 'GoDaddy') \
                or merged_data['hosted_status'] in [self.HOSTED, self.REGISTERED]:
            iid = self._db.add_new_incident(merged_data['ticketId'], merged_data)
            if iid:
                self._logger.info("Incident {} inserted into database".format(iid))
                if res:
                    screenshot_id, sourcecode_id = self._db.add_crits_data((screenshot, sourcecode), source)
                    merged_data = self._db.update_incident(iid, dict(screenshot_id=screenshot_id,
                                                                     sourcecode_id=sourcecode_id,
                                                                     last_screen_grab=datetime.utcnow(),
                                                                     target=target))
            else:
                self._logger.error("Unable to insert {} into database".format(iid))
        else:
            merged_data = self.close_process(merged_data, self.UNWORKABLE)

        return merged_data

    def _get_cmap_data(self, data):
        """
        Returns a dictionary that is the result of querying the Domain Query CMAP Service with either
        the sourceSubDomain or with the sourceDomainOrIp.
        :param data:
        :return:
        """
        subdomain = data.get('sourceSubDomain')
        return self._cmapservice.domain_query(subdomain) if subdomain \
            else self._cmapservice.domain_query(data['sourceDomainOrIp'])

    def _merge_cmap_data(self, data, cmapdata):
        """
        Returns a merged dictionary that represents data obtained from the API as well as data obtained from CMAP.
        If unable to merge with CMAP data, the original data will be returned with an unknown hosted status.
        :param data:
        :param cmapdata:
        :return:
        """
        merged_data = self._cmapservice.api_cmap_merge(data, cmapdata)

        if merged_data == data:
            merged_data['hosted_status'] = self.UNKNOWN
            self._logger.warn("Unknown registrar/host status for incident: {}.".format(pformat(data)))
        return merged_data

    def _get_hosted_status(self, data):
        """
        Returns the hosted status of a particular domain. Status may be HOSTED, REGISTERED, UNKNOWN, or FOREIGN.
        :param data:
        :return:
        """
        status = None

        hostname, registrar = self.parse_hostname_and_registrar(data)

        # set status based on API domain/IP and returned cmap service data
        if hostname and 'GODADDY' in hostname.upper():
            status = self.HOSTED
        elif registrar and re.search(r'(?:GODADDY|WILDWESTDOMAINS)', registrar.upper()):
            status = self.REGISTERED
        elif hostname is None or registrar is None:
            self._logger.warn("Unknown registrar/host status for incident: {}.".format(data['ticketId']))
            status = self.UNKNOWN
        elif 'GODADDY' not in hostname.upper() and 'GODADDY' not in registrar.upper():
            self._logger.warn("Foreign registrar and host status for incident: {}.".format(data['ticketId']))
            status = self.FOREIGN

        return status

    def parse_hostname_and_registrar(self, data):
        """
        Returns the host and registrar as a tuple from the data provided.
        :param data:
        :return:
        """
        # regex to determine if godaddy is the host and registrar
        regex = re.compile('[^a-zA-Z]')

        host = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('name', None)
        hostname = regex.sub('', host) if host is not None else None
        reg = data.get('data', {}).get('domainQuery', {}).get('registrar', {}).get('name', None)
        registrar = regex.sub('', reg) if reg is not None else None

        return hostname, registrar

    def is_blacklisted(self, data):
        """
        Returns a Boolean that represents whether or not a shopper or a domain is blacklisted.
        :param data:
        :return:
        """
        shopper_blacklist = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('vip', {}).get('blacklist', True)
        domain_blacklist = data.get('data', {}).get('domainQuery', {}).get('blacklist', True)

        return shopper_blacklist is True or domain_blacklist is True

    def is_unconfirmed_vip(self, data):
        """
        Returns a Boolean representing whether or not a shopper has an unconfirmed VIP status or not.
        :param data:
        :return:
        """
        return data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('shopperId', None) is None
