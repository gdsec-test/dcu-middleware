import logging
from datetime import datetime
from pprint import pformat

from dcdatabase.phishstorymongo import PhishstoryMongo

from dcumiddleware.dcuapi_functions import DCUAPIFunctions
from dcumiddleware.interfaces.strategy import Strategy
from dcumiddleware.urihelper import URIHelper
from dcumiddleware.viphelper import CrmClientApi, RegDbAPI, VipClients


class PhishingStrategy(Strategy):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._urihelper = URIHelper(settings)
        self._db = PhishstoryMongo(settings)
        self._api = DCUAPIFunctions(settings)
        self._premium = CrmClientApi()
        self._regdb = RegDbAPI()
        self._vip = VipClients(settings)

    def close_process(self, data, close_reason):
        data['close_reason'] = close_reason
        self._db.close_incident(data.get('ticketId'), data)
        # Close upstream ticket as well
        if self._api.close_ticket(data.get('ticketId')):
            self._logger.info("Ticket {} closed successfully".format(data.get('ticketId')))
        else:
            self._logger.warning("Unable to close upstream ticket {}".format(data.get('ticketId')))
        return data

    def process(self, data, **kwargs):
        # determine if domain is hosted at godaddy
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

        data['hosted_status'] = status
        if status in ["FOREIGN", "UNKNOWN"]:
            return self.close_process(data, "unworkable")

        # add domain create date if domain is registered only
        if status is "REGISTERED" and hosted_status[1] is not None:
            data['d_create_date'] = hosted_status[1]

        # add shopper info if we can find it
        sid, s_create_date = self._urihelper.get_shopper_info(data.get('sourceDomainOrIp'))
        if sid and s_create_date:
            data['sid'] = sid
            data['s_create_date'] = s_create_date

            # if shopper is premium, add it to their mongo record
            premier = self._premium.get_shopper_portfolio_information(sid)
            if premier is not None:
                data['premier'] = premier

            # get the number of domains in the shopper account
            domain_count = self._regdb.get_domain_count_by_shopper_id(sid)
            if domain_count is not None:
                data['domain_count'] = domain_count

            # get parent/child reseller api account status
            reseller_tuple = self._regdb.get_parent_child_shopper_by_domain_name(data.get('sourceDomainOrIp'))
            if reseller_tuple[0] is not False:
                data['parent_api_account'] = reseller_tuple[0]
                data['child_api_account'] = reseller_tuple[1]

            # get blacklist status - DO NOT SUSPEND special shopper accounts
            if self._vip.query_blacklist(sid):
                data['blacklist'] = True

            # get blacklist status - DO NOT SUSPEND special domain
            if self._vip.query_blacklist(data.get('sourceDomainOrIp')):
                data['blacklist'] = True

        else:
            data['vip_unconfirmed'] = True

        # Add hosted_status to incident
        res = self._urihelper.resolves(data.get('source'))
        if res or data.get('proxy'):
            iid = self._db.add_new_incident(data.get('ticketId'), data)
            if iid:
                self._logger.info("Incident {} inserted into database".format(iid))
                if res:
                    # Attach crits data if it resolves
                    source = data.get('source')
                    screenshot_id, sourcecode_id = self._db.add_crits_data(self._urihelper.get_site_data(source), source)
                    data = self._db.update_incident(iid, dict(screenshot_id=screenshot_id, sourcecode_id=sourcecode_id, last_screen_grab=datetime.utcnow()))
            else:
                self._logger.error("Unable to insert {} into database".format(iid))
        else:
            data = self.close_process(data, "unresolvable")

        return data
