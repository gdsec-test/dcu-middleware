import logging
from functools import partial
from json import loads
from typing import Optional

import requests

from dcumiddleware.settings import AppConfig


class APIHelper(object):
    """
    This class handles access to the DCU API
    """

    def __init__(self, settings: AppConfig):
        self._logger = logging.getLogger(__name__)
        self._url = settings.ABUSE_API_URL
        self._sso_endpoint = f'{settings.SSO_URL}/v1/api/token'
        self._user = settings.SSO_USER
        self._password = settings.SSO_PASSWORD
        self._cached_jwt = None

    def close_incident(self, ticket_id, close_reason):
        """
        Closes out the given ticket
        :param ticket_id:
        :param close_reason
        :return
        """
        headers = {'Authorization': self.get_jwt()}
        payload = {
            'closed': 'true',
            'close_reason': close_reason
        }
        try:
            api_call = partial(requests.patch, f'{self._url}/{ticket_id}', json=payload, headers=headers)
            r = api_call()
            if r.status_code in [401, 403]:
                headers['Authorization'] = self.get_jwt(True)
                r = api_call()
            if r.status_code != 204:
                self._logger.warning('Unable to update ticket {} {}'.format(ticket_id, r.content))
        except Exception as e:
            self._logger.error('Exception while updating ticket {} {}'.format(ticket_id, e))

    def get_jwt(self, force_refresh: bool = False) -> Optional[str]:
        """
        Pull down JWT via username/password.
        """
        if self._cached_jwt is None or force_refresh:
            try:
                response = requests.post(self._sso_endpoint, json={'username': self._user, 'password': self._password}, params={'realm': 'idp'})
                response.raise_for_status()

                body = loads(response.text)
                # Expected return body.get {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
                self._cached_jwt = body.get('data')
            except Exception as e:
                self._logger.error(e)

        return self._cached_jwt
