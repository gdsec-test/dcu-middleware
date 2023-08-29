import json
import logging
from typing import Optional

import requests
from dateutil import parser
from requests import sessions


class CmapServiceHelper(object):
    DATA_KEY = 'data'
    DOMAIN_Q_KEY = 'domainQuery'
    HOST_KEY = 'host'
    SHOPPER_CREATE_KEY = 'shopperCreateDate'

    _post_headers = {'Content-Type': 'application/graphql'}
    _domain_query_dicts = ['apiReseller', 'host', 'registrar', 'securitySubscription', 'shopperInfo']

    # Map of reseller private label ids that need to be enriched:
    _reseller_id_map = {'525844': '123REG'}

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._base_url = settings.CMAP_SERVICE

        self._sso_endpoint = settings.SSO_URL + '/v1/secure/api/token'
        self._cert = (settings.CMAP_CLIENT_CERT, settings.CMAP_CLIENT_KEY)
        self._cached_jwt = None

    def cmap_query(self, query: str, url: str = '/graphql') -> dict:
        self._post_headers.update({'Authorization': f'sso-jwt {self.get_jwt()}'})
        with sessions.Session() as session:
            re = session.post(url=self._base_url + url, headers=self._post_headers, data=query.encode('utf-8'))
            if re.status_code == 401 or re.status_code == 403:
                self._post_headers.update({'Authorization': f'sso-jwt {self.get_jwt(True)}'})
                re = session.post(url=self._base_url + url, headers=self._post_headers, data=query.encode('utf-8'))
            return json.loads(re.text)

    def _validate_dq_structure(self, data: dict) -> None:
        """
        Ensure the data.domainQuery.* objects are all dictionaries.
        Throw a TypeError if we find malformed data.
        """
        d = data.get('data')
        if not isinstance(d, dict):
            raise TypeError('Returned object for data not a dict')
        dq = d.get('domainQuery')
        if not isinstance(dq, dict):
            raise TypeError('Returned object for domainQuery not a dict')

        for field in self._domain_query_dicts:
            if not isinstance(dq.get(field), dict):
                raise TypeError(f'Returned object for {field} not a dict')

    def product_lookup(self, domain: str, guid: str, ip: str, product: str) -> dict:
        return self.cmap_query(
            json.dumps({
                'domain': domain,
                'guid': guid,
                'ip': ip,
                'product': product
            }),
            '/v1/hosted/lookup'
        )

    def product_lookup_entitlement(self, customerId: str, entitlementId: str) -> dict:
        # cmap entitlement endpoint is: /v1/nes/<customerId>/<entitlementId> This returns an array of
        #   the products for that account
        entitlements_array = self.cmap_query('', f'/v1/nes/{customerId}/{entitlementId}')

        # Return the first element in the array.  This array *should* only have one element, since we are
        #   assuming that there can only be one product per entitlement ID
        return entitlements_array[0]

    def shopper_lookup(self, shopper: str) -> dict:
        return self.cmap_query(
            json.dumps({
                'shopper_id': shopper
            }),
            '/v1/shopper/lookup'
        )

    def _format_cmap_response_dates(self, data: dict):
        ddq = data.get('data', {}).get('domainQuery', {})
        reg_create_date = ddq.get('registrar', {}).get('domainCreateDate')
        if reg_create_date:
            data['data']['domainQuery']['registrar']['domainCreateDate'] = \
                self._date_time_format(reg_create_date)

        shp_create_date = ddq.get('shopperInfo', {}).get('shopperCreateDate')
        if shp_create_date:
            data['data']['domainQuery']['shopperInfo']['shopperCreateDate'] = \
                self._date_time_format(shp_create_date)

        host_sh_create = ddq.get('host', {}).get('shopperCreateDate')
        if host_sh_create:
            data[self.DATA_KEY][self.DOMAIN_Q_KEY][self.HOST_KEY][self.SHOPPER_CREATE_KEY] = self._date_time_format(host_sh_create)

        hosting_create_date = ddq.get('host', {}).get('createdDate')
        if hosting_create_date:
            data['data']['domainQuery']['host']['createdDate'] = self._date_time_format(hosting_create_date)
        return data

    def domain_query_for_kelvindb(self, domain: str) -> dict:
        query = ('''
        {
            domainQuery(domain: "''' + domain + '''") {
                domain
                host {
                    brand
                    guid
                    hostingAbuseEmail
                    hostingCompanyName
                    ip
                    product
                    shopperId
                    customerId
                    shopperPlid
                    entitlementId
                }
                registrar {
                    brand
                    domainCreateDate
                    domainId
                    registrarAbuseEmail
                    registrarName
                }
                shopperInfo {
                    shopperCreateDate
                    shopperId
                    customerId
                    shopperPlid
                }
            }
        }''')
        query_result = self.cmap_query(query)
        if not isinstance(query_result, dict) or 'errors' in query_result:
            raise Exception('Unexpected query result')
        query_result = self._format_cmap_response_dates(query_result)
        return query_result

    def domain_query(self, domain: str, path: str) -> dict:
        """
        Query CMAP service for information related to a domain.
        """
        query = ('''
             {
              domainQuery(domain: "''' + domain + '''", path: "''' + path + '''") {

                alexaRank
                apiReseller {
                  child
                  parent
                  parentCustomerId
                  childCustomerId
                }
                blacklist
                domain
                isDomainHighValue
                securitySubscription {
                  sucuriProduct
                  products {
                    createdDate
                    sucuriProduct
                    entitlementId
                  }
                }
                sslSubscriptions {
                  certCommonName
                  certType
                  createdAt
                  expiresAt
                  entitlementId
                }
                host {
                  dataCenter
                  guid
                  containerId
                  brand
                  hostingCompanyName
                  hostingAbuseEmail
                  hostname
                  ip
                  os
                  product
                  shopperId
                  shopperCountry
                  shopperPlid
                  customerId
                  entitlementId
                  shopperCreateDate
                  mwpId
                  createdDate
                  friendlyName
                  privateLabelId
                  username
                  managedLevel
                  firstPassEnrichment
                  secondPassEnrichment,
                  abuseReportEmail
                  hostingPlan
                  subscriptionStatus
                  startedAsFreeTrial
                  vip {
                    blacklist
                    portfolioType
                    shopperId
                  }
                }
                registrar {
                  brand
                  domainCreateDate
                  domainId
                  registrarAbuseEmail
                  registrarName
                  firstPassEnrichment,
                  abuseReportEmail
                }
                shopperInfo {
                  domainCount
                  shopperCreateDate
                  shopperId
                  shopperCountry
                  customerId
                  shopperPlid
                  vip {
                    blacklist
                    portfolioType
                    shopperId
                  }
                }
              }
            }
          ''')
        query_result = self.cmap_query(query)

        if not isinstance(query_result, dict) or 'errors' in query_result:
            raise Exception('Unexpected query result')

        self._validate_dq_structure(query_result)

        query_result = self._format_cmap_response_dates(query_result)

        ddq = query_result.get('data', {}).get('domainQuery', {})
        private_label_id = ddq.get('host', {}).get('privateLabelId')
        query_result['data']['domainQuery']['host']['reseller'] = self._reseller_id_map.get(private_label_id)

        return query_result

    def _date_time_format(self, date):
        """
        Returns date/time formatted object
        :param date:
        :return
        """
        try:
            return parser.parse(date, ignoretz=True)
        except Exception as e:
            self._logger.error('Unable to format date string to ISO date object: {}. {}'.format(date, e))

    def api_cmap_merge(self, apidata, cmapdata):
        """
        Returns query result of cmap service given a domain
        :param apidata:
        :param cmapdata:
        :return merged_data: dictionary that is the result of merging the api data and cmap data dictionaries
        """
        try:
            return dict(list(apidata.items()) + list(cmapdata.items()))
        except Exception as e:
            self._logger.error('Unable to merge API and CMAP service dictionaries: {}. {}'.format(
                apidata['ticketId'], e))
            return apidata

    def get_jwt(self, force_refresh: bool = False) -> Optional[str]:
        """
        Attempt to retrieve the JWT associated with the cert/key pair from SSO
        """
        if self._cached_jwt is None or force_refresh:
            try:
                response = requests.post(self._sso_endpoint, data={'realm': 'cert'}, cert=self._cert)
                response.raise_for_status()

                body = json.loads(response.text)
                self._cached_jwt = body.get('data')  # {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
            except Exception as e:
                self._logger.error(e)

        return self._cached_jwt
