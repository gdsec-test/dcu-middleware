import logging

from dcumiddleware.interfaces.strategy import Strategy
from dcumiddleware.phishstorymongo import PhishstoryMongo
from dcumiddleware.urihelper import URIHelper


class NetAbuseStrategy(Strategy):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._urihelper = URIHelper(settings)
        self._db = PhishstoryMongo(settings)

    def process(self, data, **kwargs):
        # determine if IP is hosted with godaddy
        hosted_status = self._urihelper.get_status(data.domain)
        if hosted_status == URIHelper.HOSTED:
            status = "HOSTED"
        elif hosted_status == URIHelper.REG:
            status = "REGISTERED"
        elif hosted_status == URIHelper.NOT_REG_HOSTED:
            status = "FOREIGN"
        else:
            self._logger.warn("Unknown hosted status for incident: {}".format(data))
            status = "UNKNOWN"

        # Add hosted_status attribute to incident
        data.hosted_status = status
        # save the incident to the database
        if status is "HOSTED":
            iid = self._db.add_new_incident(data.ticketId, data.as_dict())
            if iid:
                self._logger.info("Incident {} inserted into database".format(iid))
            else:
                self._logger.error("Unable to insert {} into database".format(iid))
        else:
            data.close_reason = "not_hosted"
            self._db.close_incident(data.ticketId, data.as_dict())

