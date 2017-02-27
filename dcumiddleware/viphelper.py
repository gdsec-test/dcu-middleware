import re
import logging

import xml.etree.ElementTree as ET

from pymongo import MongoClient


# Query the CRM API to determine if they are a special portfolio customer
class CrmClientApi(object):
    _WSDL = 'https://crmclient-api.prod.phx3.int.godaddy.com/Shopper.svc?singleWsdl'
    _FACTORY = '{http://schemas.datacontract.org/2004/07/GoDaddy.CRM.ClientAPI.DataContracts}ShopperPortfolioInformationRequest'

    def __init__(self):
        from suds.client import Client
        self._client = Client(self._WSDL)
        self._request = self._client.factory.create(self._FACTORY)

    def get_shopper_portfolio_information(self, shopper_id):
        self._request.shopperID = shopper_id
        resp = self._client.service.GetShopperPortfolioInformation(self._request)
        match = re.search('<data count=.(\d+).>', resp.ResultXml)
        if match.group(1) == '0':
            return None
        doc = ET.fromstring(resp.ResultXml)
        self._elem = doc.find(".//*[@PortfolioType]").attrib
        return self._elem


# Use the RegDB to query the number of domains a shopper has, or if they are a reseller api parent/child
class RegDbAPI(object):
    _WSDL = 'https://dsweb.prod.phx3.gdg/RegDBWebSvc/RegDBWebSvc.dll?Handler=GenRegDBWebSvcWSDL'

    def __init__(self):
        from suds.client import Client
        self._client = Client(self._WSDL)

    def get_domain_count_by_shopper_id(self, shopper_id):
        xml_query = '<request><shopper shopperid="{}"/></request>'.format(shopper_id)
        xml_response = self._client.service.GetDomainCountByShopperID(xml_query)
        match = re.search('domaincount="(\d+)"', xml_response)
        return match.group(1)

    def get_parent_child_shopper_by_domain_name(self, domain_name):
        xml_response = self._client.service.GetParentChildShopperByDomainName(domain_name)
        match = re.search('<PARENT_SHOPPER_ID>(\d+)</PARENT_SHOPPER_ID><CHILD_SHOPPER_ID>(\d+)</CHILD_SHOPPER_ID>', xml_response)
        if match is None:
            return False, False
        return match.group(1), match.group(2)


# Query the Blacklist table in Mongo, to see if the provided domain name or shopper id is
#  VIP, meaning: Do Not Suspend!!!
class VipClients(object):
    _logger = logging.getLogger(__name__)

    def __init__(self, settings):
        try:
            conn = MongoClient(settings.DBURL, connect=False)
            db = conn[settings.DB]
            self._blacklist = db[settings.BLACKLIST_COLLECTION]
        except Exception as e:
            self._logger.error(e.message)

    def query_blacklist(self, entity_id):
        db_key = 'entity'
        try:
            result = self._blacklist.find({db_key: str(entity_id).lower()})
            # If the shopper or domain entity exists, they are VIP
            vip_status = True
            # Since result is a cursor...
            if len(list(result)) == 0:
                vip_status = False
            return vip_status
        except Exception as e:
            self._logger.error(e.message)
            return None
