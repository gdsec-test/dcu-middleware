import logging

from dcumiddleware.interfaces.strategy import Strategy
from dcumiddleware.phishstorymongo import PhishstoryMongo
from dcumiddleware.urihelper import URIHelper


class PhishingStrategy(Strategy):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._urihelper = URIHelper(settings)
        self._db = PhishstoryMongo(settings)

    def process(self, data, **kwargs):
        # determine if domain is hosted at godaddy
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

        # Add hosted_status to incident
        data.hosted_status = status
        if self._urihelper.resolves(data.sources):
            # Attach crits data
            screenshot_id, sourcecode_id = self._db.add_crits_data(self._urihelper.get_site_data(data.sources))
            data.screenshot_id = screenshot_id
            data.sourcecode_id = sourcecode_id
            iid = self._db.add_new_incident(data.ticketId, data.as_dict())
            if iid:
                self._logger.info("Incident {} inserted into database".format(iid))
            else:
                self._logger.error("Unable to insert {} into database".format(iid))
        else:
            data.close_reason = "unresolvable"
            self._db.close_incident(data.ticketId, data.as_dict())
