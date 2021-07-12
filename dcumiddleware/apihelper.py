import logging
from functools import partial
from json import loads

import requests

from settings import AppConfig


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
        self._header = {'Authorization': self._get_jwt()}

    def close_incident(self, ticket_id, close_reason):
        """
        Closes out the given ticket
        :param ticket_id:
        :param close_reason
        :return
        """

        payload = {
            'closed': 'true',
            'close_reason': close_reason
        }
        try:
            api_call = partial(requests.patch, f'{self._url}/{ticket_id}', json=payload, headers=self._header)
            r = api_call()
            if r.status_code in [401, 403]:
                self._header['Authorization'] = self._get_jwt()
                r = api_call()
            if r.status_code != 204:
                self._logger.warning('Unable to update ticket {} {}'.format(ticket_id, r.content))
        except Exception as e:
            self._logger.error('Exception while updating ticket {} {}'.format(ticket_id, e))

    def _get_jwt(self):
        """
        Pull down JWT via username/password.
        """
        try:
            response = requests.post(self._sso_endpoint, json={'username': self._user, 'password': self._password}, params={'realm': 'idp'})
            response.raise_for_status()

            body = loads(response.text)
            # Expected return body.get {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
            return body.get('data')
        except Exception as e:
            self._logger.error(e)
        return None
