import logging
from pprint import pformat

from dcdatabase.phishstorymongo import PhishstoryMongo

from dcumiddleware.dcuapi_functions import DCUAPIFunctions
from dcumiddleware.interfaces.strategy import Strategy
from dcumiddleware.urihelper import URIHelper


class NetAbuseStrategy(Strategy):

    def __init__(self, settings):
        super(NetAbuseStrategy, self).__init__()
        self._logger = logging.getLogger(__name__)
        self._urihelper = URIHelper(settings)
        self._db = PhishstoryMongo(settings)
        self._api = DCUAPIFunctions(settings)

    def process(self, data, **kwargs):
        # determine if IP is hosted with godaddy
        self._logger.info("Received request {}".format(pformat(data)))
        hosted_status = self._urihelper.get_status(data.get('sourceDomainOrIp'))
        if hosted_status[0] == URIHelper.HOSTED:
            status = "HOSTED"
        elif hosted_status[0] == URIHelper.REG:
            status = "REGISTERED"
        elif hosted_status[0] == URIHelper.NOT_REG_HOSTED:
            status = "FOREIGN"
        else:
            self._logger.warn("Unknown hosted status for incident: {}".format(pformat(data)))
            status = "UNKNOWN"

        # Add hosted_status attribute to incident
        data['hosted_status'] = status
        # save the incident to the database
        if status is "HOSTED":
            iid = self._db.add_new_incident(data.get('ticketId'), data)
            if iid:
                self._logger.info("Incident {} inserted into database".format(iid))
            else:
                self._logger.error("Unable to insert {} into database".format(iid))
        else:
            data['close_reason'] = "not_hosted"
            self._db.close_incident(data.get('ticketId'), data)
            # Close upstream ticket as well
            if self._api.close_ticket(data.get('ticketId')):
                self._logger.info("Ticket {} closed successfully".format(data.get('ticketId')))
            else:
                self._logger.warning("Unable to close upstream ticket {}".format(data.get('ticketId')))

        return data
