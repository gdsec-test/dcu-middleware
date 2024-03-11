import logging
from typing import Dict, Optional

import requests
from csetutils.services.jwt_base import CertJwtHttpClient


class CmapV2Helper(CertJwtHttpClient):
    def __init__(self, service_url: str, sso_host: str, client_cert_path: str, client_key_path: str):
        '''
        Initializes the CMAP V2 class.
        '''
        super().__init__(f'{sso_host}', client_cert_path, client_key_path)
        self.service_url = f'{service_url}'

    def lookup_host_by_authority(self, domain: str) -> Optional[Dict[str, str]]:
        '''
        Retrieves information about domains.

        :param domain: The domain being queried.
        :return: An optional dictionary of the domain's product data.
        '''
        if not domain:
            return None
        try:
            headers = {'Authorization': f'sso-jwt {self._get_jwt()}',
                       'Content-Type': 'application/json'}
            url = f'{self.service_url}/v1/cmap/lookupByHostAuthority?host={domain}'
            response = requests.get(url, headers=headers)
            if response.status_code in [401, 403]:
                headers['Authorization'] = f'sso-jwt {self._get_jwt(force_update=True)}'
                response = requests.get(url, headers=headers)
                return response.json()
            cmapV2_data = response.json()
            return {'productData': cmapV2_data}

        except Exception as e:
            logging.exception(f'Error querying CMAP V2 service for domain {domain}. Error message: {e} ')
            raise

    def convert_cmapv2data(self, productData: dict) -> Optional[Dict[str, str]]:
        '''
        Maps the fields in productData to match the fields in the old cmap's data.

        :param productData: The dictionary being mapped.
        :return: An optional dictionary of the new productData mappings.
        '''
        logging.info(f'\n\nOriginal productData\n {productData}')

        mappedData = {}
        _id = 'id-123'
        sslSub = []
        securitySub = {'sucuriProduct': [], 'products': []}

        if not productData:
            return None
        try:
            for id in productData['productData']['products']:
                if len(productData['productData']['products']) == 1:
                    _id = id
                elif len(productData['productData']['products'][id]['associatedProducts']) > 0:
                    _id = id

                if (productData['productData']['products'][id]['product'] == 'Standard SSL'):
                    sslSub.append(id)
                else:
                    securitySub['products'].append(id)

            # logging.info(f"\n\nid is {_id}")
            customer = productData['productData']['products'][_id].get('customerId')

            mappedData = {'cmapv2Data': {
                'domainQuery': {
                    'apiReseller': {
                        'parentCustomerId': productData['productData']['products'][_id].get('customerId')
                    },
                    'securitySubscription': securitySub,
                    'sslSubscription': sslSub,
                    'host': {
                        'dataCenter': productData['productData']['products'][_id]['attributes'].get('dataCenter'),
                        'guid': _id,
                        'containerId': productData['productData']['products'][_id]['attributes'].get('containerId'),
                        'brand': productData['productData'].get('brand'),
                        'hostingCompanyName': productData['productData']['products'].get('hostingCompanyName'),
                        'hostingAbuseEmail': [productData['productData'].get('abuseEmail')],
                        'hostname': productData['productData']['products'][_id]['attributes'].get('hostname'),
                        'ip': productData['productData']['products'][_id]['attributes'].get('id'),
                        'os': productData['productData']['products'][_id]['attributes'].get('os'),
                        'product': productData['productData']['products'][_id].get('product'),
                        'customerId': customer,
                        'entitlementId': _id,
                        'mwpId': productData['productData']['products'][_id]['attributes'].get('mwpId'),
                        'friendlyName': productData['productData']['products'][_id]['attributes'].get('friendlyName'),
                        'username': productData['productData']['products'][_id]['attributes'].get('username'),
                        'managedLevel': productData['productData']['products'][_id]['attributes'].get('managedLevel'),
                        'vip': {'blacklist': productData['productData']['customers'][customer].get('blacklist'),
                                'vipPortfolio': productData['productData']['customers'][customer]['attributes'].get('vipPortfolio'),
                                }
                    },
                    'registrar': {
                        'brand': productData['productData'].get('brand'),
                        'registrarAbuseEmail': [productData['productData']['products'].get('abuseEmail')],
                        'registrarName': productData['productData'].get('hostingCompanyName'),
                        'abuseReportEmail': productData['productData'].get('abuseEmail')
                    },
                    'shopperInfo': {}
                }
            }}

        except Exception as e:
            logging.exception(f'Error mapping CMAP V2 service for the dict {productData}. Some fields are missing or non-existing. {e}')
            raise

        logging.info(f'\n\nMapped cmapv2\n {mappedData}')
        return mappedData
