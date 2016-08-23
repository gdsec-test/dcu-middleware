import logging

from dcdatabase.phishstorymongo import PhishstoryMongo

from dcumiddleware.dcuapi_functions import DCUAPIFunctions
from dcumiddleware.incident import Incident
from dcumiddleware.interfaces.strategy import Strategy
from dcumiddleware.urihelper import URIHelper

class PhishingStrategy(Strategy):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._urihelper = URIHelper(settings)
        self._db = PhishstoryMongo(settings)
        self._api = DCUAPIFunctions(settings)

    def close_process(self, data, close_reason):
        data.close_reason = close_reason
        self._db.close_incident(data.ticketId, data.as_dict())
        # Close upstream ticket as well
        if self._api.close_ticket(data.ticketId):
            self._logger.info("Ticket {} closed successfully".format(data.ticketId))
        else:
            self._logger.warning("Unable to close upstream ticket {}".format(data.ticketId))
        return data

    def process(self, data, **kwargs):
        # determine if domain is hosted at godaddy
        self._logger.info("Received request {}".format(data))
        hosted_status = self._urihelper.get_status(data.sourceDomainOrIp)
        if hosted_status == URIHelper.HOSTED:
            status = "HOSTED"
        elif hosted_status == URIHelper.REG:
            status = "REGISTERED"
        elif hosted_status == URIHelper.NOT_REG_HOSTED:
            status = "FOREIGN"
        else:
            self._logger.warn("Unknown hosted status for incident: {}".format(data))
            status = "UNKNOWN"

        data.hosted_status = status
        if status in ["FOREIGN", "UNKNOWN"]:
            return self.close_process(data, "unworkable")

        # add shopper info if we can find it
        sid, s_create_date = self._urihelper.get_shopper_info(data.sourceDomainOrIp)
        if sid and s_create_date:
            data.sid = sid
            data.s_create_date = s_create_date

        # set any existing fraud hold times for this domain
        hold = self._urihelper.fraud_holds_for_domain(domain=data.sourceDomainOrIp)
        if hold:
            data.fraud_hold_until = hold

        # Add hosted_status to incident
        res = self._urihelper.resolves(data.source)
        if res or data.proxy:
            iid = self._db.add_new_incident(data.ticketId, data.as_dict())
            if iid:
                self._logger.info("Incident {} inserted into database".format(iid))
                if res:
                    # Attach crits data if it resolves
                    screenshot_id, sourcecode_id = self._db.add_crits_data(self._urihelper.get_site_data(data.source), data.source)
                    data = Incident(self._db.update_incident(iid, dict(screenshot_id=screenshot_id, sourcecode_id=sourcecode_id)))
            else:
                self._logger.error("Unable to insert {} into database".format(iid))
        else:
            data = self.close_process(data, "unresolvable")

        return data
