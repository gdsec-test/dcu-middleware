import requests
from requests import sessions
import json
from datetime import datetime
import logging


class CmapServiceHelper(object):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._graphene_url = settings.CMAP_SERVICE + '/graphql'
        self._post_headers = {'Content-Type': 'application/graphql'}

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
            self._logger.error("Unable to query CMAP service for: {}. {}".
                               format(domain, e.message))
            return None

    def domain_query(self, domain):
        """
    Returns query result of cmap service given a domain
      :param domain:
      :return query result: query result host, registrar, domain create date, vip profile, shopperID, shopper create date,
      shopper domain count, API parent/child account numbers
    """
        try:
            query = ('''
          {
            domainQuery(domain: "''' + domain + '''") {
              host {
                name
              }
              registrar {
                name
                createDate
              }
              apiReseller {
                parent
                child
              }
              shopperInfo {
                shopperId
                dateCreated
                domainCount
                vip {
                  blacklist
                  PortfolioType
                }
              }
              blacklist
            }
          }
          ''')
            query_result = self.cmap_query(query, domain)
            query_result['data']['domainQuery']['registrar']['createDate'] = \
             self._date_time_format(query_result['data']['domainQuery']['registrar']['createDate'])
            query_result['data']['domainQuery']['shopperInfo']['dateCreated'] = \
             self._date_time_format(query_result['data']['domainQuery']['shopperInfo']['dateCreated'])
            return query_result
        except Exception as e:
            self._logger.error("Unable to complete domain query for : {}. {}".
                               format(domain, e.message))
            return None

    def _date_time_format(self, date):
        """
    Returns date/time formated object
    :param date:
    :return iso_date:
    """
        try:
            iso_date = datetime.strptime(date, '%Y-%m-%d')
            return iso_date
        except Exception as e:
            self._logger.error(
                "Unable to format date string to ISO date object: {}. {}".
                format(date, e.message))
            return date

    def api_cmap_merge(self, apidata, cmapdata):
        """
    Returns query result of cmap service given a domain
    :param apidata:
    :param cmapdata:
    :return merged_data: dictionary that is the result of merging the api data and cmap data dictionaries
    """
        try:
            merged_data = dict(apidata.items() + cmapdata.items())
            return merged_data
        except Exception as e:
            self._logger.error(
                "Unable to merge API and CMAP service dictionaries: {}. {}".
                format(apidata['ticketId'], e.message))
            return apidata
