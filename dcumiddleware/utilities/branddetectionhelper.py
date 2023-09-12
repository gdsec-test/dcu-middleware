import requests
import json
import logging


class BrandDetectionHelper:
    def __init__(self, url: str, cert_path: str, key_path: str):
        self._logger = logging.getLogger(__name__)
        self.url = url
        self._cert = (cert_path, key_path)
        self._jwt = None
        self._logger = logging.getLogger(__name__)

    def _get_jwt(self, force_refresh=False):
        if self._jwt is None or force_refresh:
            try:
                response = requests.post(self._sso_endpoint, data={'realm': 'cert'}, cert=self._cert)
                response.raise_for_status()
                self._jwt = json.loads(response.text)
            except Exception:
                self._logger.exception('Brand detection jwt failure')
        return self._jwt

    def get_plid_info(self, plid: str):
        self._logger.info(f'Fetching brand info for PLID {plid}')
        try:
            r = requests.get(f'{self.url}/plid', headers={'Authorization': f'sso-jwt {self._get_jwt()}'})
            if r.status_code in [401, 403]:
                r = requests.get(f'{self.url}/plid', headers={'Authorization': f'sso-jwt {self._get_jwt(force_refresh=True)}'})
            r.raise_for_status()
            return r.json()
        except Exception:
            self._logger.exception('Exception calling brand detection')
        return {}
