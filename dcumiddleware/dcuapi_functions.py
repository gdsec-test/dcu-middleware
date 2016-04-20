import requests
import logging


class DCUAPIFunctions:
    """
    This class handles access to the DCU API
    """

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._url = settings.API_UPDATE_URL
        self._header = {'Authorization': settings.API_TOKEN}

    def close_ticket(self, ticket_id):
        """
        Closes out the given ticket
        :param ticket_id:
        :return True on success, false otherwise:
        """
        payload = {
            "closed": "true"
        }
        data = False
        try:
            r = requests.patch('{}/{}'.format(self._url, ticket_id), json=payload, headers=self._header)
            if r.status_code == 204:
                data = True
            else:
                self._logger.warning("Unable to update ticket {} {}".format(ticket_id, r.content))
        except Exception as e:
            self._logger.error("Exception while updating ticket {} {}".format(ticket_id, e.message))
        finally:
            return data
