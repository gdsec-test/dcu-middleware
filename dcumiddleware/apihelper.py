import logging

import requests


class APIHelper(object):
    """
    This class handles access to the DCU API
    """

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._url = settings.ABUSE_API_URL
        self._header = {'Authorization': settings.API_TOKEN}

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
            r = requests.patch('{}/{}'.format(self._url, ticket_id), json=payload, headers=self._header)
            if r.status_code != 204:
                self._logger.warning("Unable to update ticket {} {}".format(ticket_id, r.content))
        except Exception as e:
            self._logger.error("Exception while updating ticket {} {}".format(ticket_id, e.message))
