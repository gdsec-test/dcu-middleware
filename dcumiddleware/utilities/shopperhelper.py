import logging

import requests


class ShopperApiHelper:
    SHOPPER_PARAMS = {'auditClientIp': 'cmap.service.int.godaddy.com'}
    SHOPPER_KEY = 'shopperId'

    def __init__(self, shopper_url: str, cert_file_path: str, key_file_path: str):
        self._logger = logging.getLogger(__name__)
        self._shopper_url = shopper_url
        self._cert_file_path = cert_file_path
        self._key_file_path = key_file_path

    def get_shopper_id(self, customer_id: str) -> str:
        url = f'{self._shopper_url}/v1/customers/{customer_id}/shopper'
        cert = (self._cert_file_path, self._key_file_path)
        try:
            resp = requests.get(url, params=self.SHOPPER_PARAMS, cert=cert)
            resp.raise_for_status()
            data = resp.json()
            return data[self.SHOPPER_KEY]
        except Exception as e:
            self._logger.exception(f'Error in shopper request. {e}')
            return ''
