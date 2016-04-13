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

        # Add hosted_status, phishstory status, and valid flag attributes to incident
        data.hosted_status = status
        data.phishstory_status= "OPEN"
        data.valid = True if self._urihelper.resolves(data.sources) else False
        # save the incident to the database
        iid = self._db.add_new_incident(data.ticketId, data.as_dict())

        if iid and data.valid:
            # Attach crits data
            self._db.add_crits_data(data.ticketId, self._urihelper.get_site_data(data.sources))
