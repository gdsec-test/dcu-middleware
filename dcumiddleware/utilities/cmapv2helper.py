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

        except Exception:
            logging.exception(f'Error querying CMAP V2 service for domain {domain}')
            raise
