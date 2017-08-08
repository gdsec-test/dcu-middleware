import json
import logging

from datetime import datetime
from requests import sessions


class CmapServiceHelper(object):

    _post_headers = {'Content-Type': 'application/graphql'}

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._graphene_url = settings.CMAP_SERVICE + '/graphql'

    def cmap_query(self, query, domain):
        """
        Returns query result of cmap service given a query
        :param query:
        :param domain:
        :return query result:
        """
        try:
            with sessions.Session() as session:
                self._logger.info("Fetching query for {}".format(domain))
                re = session.request(method='POST', url=self._graphene_url, headers=self._post_headers, data=query)
                return json.loads(re.text)
        except Exception as e:
            self._logger.error("Unable to query CMAP service for: {}. {}".format(domain, e.message))
            return {'data': {'domainQuery': {'blacklist': None,
                                             'host': {'guid': None, 'hostingCompanyName': None},
                                             'registrar': {'domainCreateDate': None, 'registrarName': None},
                                             'shopperInfo': {'shopperCreateDate': None, 'shopperId': None, 'vip': {'blacklist': None}}}}}

    def domain_query(self, domain):
        """
        Returns query result of cmap service given a domain
        :param domain:
        :return query result: query result host, registrar, domain create date, vip profile, shopperID,
        shopper create date, shopper domain count, API parent/child account numbers
        """
        query = ('''
             {
              domainQuery(domain: "''' + domain + '''") {
                alexaRank
                apiReseller {
                  child
                  parent
                }
                blacklist
                domain
                domainStatus {
                  statusCode
                }
                host {
                  dataCenter
                  guid
                  hostingCompanyName
                  hostingAbuseEmail
                  hostname
                  ip
                  os
                  product
                  shopperId
                  vip {
                    accountRepEmail
                    accountRepFirstName
                    accountRepLastName
                    blacklist
                    portfolioType
                    shopperId
                  }
                }
                registrar {
                  domainCreateDate
                  registrarAbuseEmail
                  registrarName
                }
                shopperInfo {
                  domainCount
                  domainSearch(regex: "a") {
                    results {
                      domain
                      domainid
                    }
                  }
                  shopperCreateDate
                  shopperEmail
                  shopperFirstName
                  shopperId
                  vip {
                    accountRepEmail
                    accountRepFirstName
                    accountRepLastName
                    blacklist
                    portfolioType
                    shopperId
                  }
                }
              }
            }
          ''')
        query_result = self.cmap_query(query, domain)

        if not isinstance(query_result, dict):
            query_result = dict()

        reg_create_date = query_result.get('data', {}).get('domainQuery', {}).get('registrar', {}).get(
            'domainCreateDate', None)
        query_result['data']['domainQuery']['registrar']['domainCreateDate'] = self._date_time_format(reg_create_date)

        shp_create_date = query_result.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get(
            'shopperCreateDate', None)
        query_result['data']['domainQuery']['shopperInfo']['shopperCreateDate'] = self._date_time_format(
            shp_create_date)

        return query_result

    def _date_time_format(self, date):
        """
        Returns date/time formatted object
        :param date:
        :return iso_date:
        """
        try:
            return datetime.strptime(date, '%Y-%m-%d')
        except Exception as e:
            self._logger.error("Unable to format date string to ISO date object: {}. {}".format(
                date, e.message))
            return date

    def api_cmap_merge(self, apidata, cmapdata):
        """
        Returns query result of cmap service given a domain
        :param apidata:
        :param cmapdata:
        :return merged_data: dictionary that is the result of merging the api data and cmap data dictionaries
        """
        try:
            return dict(apidata.items() + cmapdata.items())
        except Exception as e:
            self._logger.error("Unable to merge API and CMAP service dictionaries: {}. {}".format(
                apidata['ticketId'], e.message))
            return apidata
