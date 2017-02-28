import re
import pickle
import logging

import xml.etree.ElementTree as ET

from redis import Redis
from pymongo import MongoClient


# Query the CRM API to determine if they are a special portfolio customer
class CrmClientApi(object):
    _WSDL = 'https://crmclient-api.prod.phx3.int.godaddy.com/Shopper.svc?singleWsdl'
    _FACTORY = '{http://schemas.datacontract.org/2004/07/GoDaddy.CRM.ClientAPI.DataContracts}ShopperPortfolioInformationRequest'

    def __init__(self, redis_cache):
        from suds.client import Client
        self._client = Client(self._WSDL)
        self._request = self._client.factory.create(self._FACTORY)
        self._redis_cache = redis_cache

    def get_shopper_portfolio_information(self, shopper_id):
        redis_key = '{}-portfolio'.format(shopper_id)
        query_value = self._redis_cache.get_value(redis_key)
        if query_value is None:
            self._request.shopperID = shopper_id
            resp = self._client.service.GetShopperPortfolioInformation(self._request)
            match = re.search('<data count=.(\d+).>', resp.ResultXml)
            if match.group(1) == '0':
                # Since the call to get_value() returns None if the redis key doesnt exist, I'll need to
                #  set the value to a blank string here, and then return None later if a blank string
                #  is the value returned from an existing redis key
                self._redis_cache.set_value(redis_key, '')
                return None
            doc = ET.fromstring(resp.ResultXml)
            info_dict = doc.find(".//*[@PortfolioType]").attrib
            query_value = info_dict.get('PortfolioType')
            self._redis_cache.set_value(redis_key, query_value)
        elif query_value == '':
            query_value = None
        return query_value


# Use the RegDB to query the number of domains a shopper has, or if they are a reseller api parent/child
class RegDbAPI(object):
    _WSDL = 'https://dsweb.prod.phx3.gdg/RegDBWebSvc/RegDBWebSvc.dll?Handler=GenRegDBWebSvcWSDL'

    def __init__(self, redis_cache):
        from suds.client import Client
        self._client = Client(self._WSDL)
        self._redis_cache = redis_cache

    def get_domain_count_by_shopper_id(self, shopper_id):
        redis_key = '{}-domaincount'.format(shopper_id)
        query_value = self._redis_cache.get_value(redis_key)
        if query_value is None:
            xml_query = '<request><shopper shopperid="{}"/></request>'.format(shopper_id)
            xml_response = self._client.service.GetDomainCountByShopperID(xml_query)
            match = re.search('domaincount="(\d+)"', xml_response)
            query_value = int(match.group(1))
            self._redis_cache.set_value(redis_key, query_value)
        return query_value

    def get_parent_child_shopper_by_domain_name(self, domain_name):
        redis_key = '{}-parentchild'.format(domain_name)
        query_value = self._redis_cache.get_value(redis_key)
        if query_value is not None:
            query_value = pickle.loads(query_value)
        else:
            xml_response = self._client.service.GetParentChildShopperByDomainName(domain_name)
            match = re.search('<PARENT_SHOPPER_ID>(\d+)</PARENT_SHOPPER_ID><CHILD_SHOPPER_ID>(\d+)</CHILD_SHOPPER_ID>', xml_response)
            if match is None:
                query_value = False, False
            else:
                query_value = match.group(1), match.group(2)
            self._redis_cache.set_value(redis_key, pickle.dumps(query_value))
        return query_value


# Query the Blacklist table in Mongo, to see if the provided domain name or shopper id is
#  VIP, meaning: Do Not Suspend!!!
class VipClients(object):
    _logger = logging.getLogger(__name__)

    def __init__(self, settings, redis_cache):
        self._redis_cache = redis_cache
        try:
            conn = MongoClient(settings.DBURL, connect=False)
            db = conn[settings.DB]
            self._blacklist = db[settings.BLACKLIST_COLLECTION]
        except Exception as e:
            self._logger.error(e.message)

    def query_blacklist(self, entity_id):
        redis_key = '{}-blacklist'.format(entity_id)
        query_value = self._redis_cache.get_value(redis_key)
        if query_value is None:
            db_key = 'entity'
            try:
                result = self._blacklist.find({db_key: str(entity_id).lower()})
                # If the shopper or domain entity exists, they are VIP
                query_value = True
                # Since result is a cursor...
                if len(list(result)) == 0:
                    query_value = False
                self._redis_cache.set_value(redis_key, query_value)
            except Exception as e:
                self._logger.error(e.message)
                query_value = None
        return query_value


# Cache queries for shoppers and domains to improve performance
class RedisCache(object):
    redis_ttl = 86400  # 24hrs

    def __init__(self, settings):
        self.redis = Redis(settings.REDIS_CACHE)

    def get_value(self, redis_key):
        try:
            redis_value = self.redis.get(redis_key)
        except Exception:
            redis_value = None
        return redis_value

    def set_value(self, redis_key, redis_value, redis_ttl=None):
        if redis_ttl is None:
            redis_ttl = self.redis_ttl
        self.redis.set(redis_key, redis_value)
        self.redis.expire(redis_key, redis_ttl)
