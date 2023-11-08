import logging
import os

from dcdatabase.phishstorymongo import PhishstoryMongo

from dcumiddleware.settings import AppConfig, config_by_name

env = os.getenv('sysenv', 'unit-test')
app_settings: AppConfig = config_by_name[env]()


class RoutingHelper:
    EMEA = 'EMEA'
    CLOSE_REASON = 'email_sent_to_emea'
    GODADDY = 'GODADDY'
    KEY_BRAND = 'brand'
    KEY_TICKET_ID = 'ticketId'
    KEY_ABUSE_META = 'abuseMeta'
    KEY_PHISHSTORY_STATUS = 'phishstory_status'
    """
    Responsible for all routing responsibilities to the brand services.
    """
    _brands = {'GODADDY': 'run.process_gd',
               'FOREIGN': 'run.process_gd',
               'EMEA': 'run.process_emea',
               '123REG': 'run.process_gd'}

    _brands_routed_to_gd = {'GODADDY', '123REG', 'FOREIGN'}

    def __init__(self, capp, api, db):
        """
        :param capp: handle to Celery
        :param api: handle to abuse api
        :param db: handle to db
        """
        self._logger = logging.getLogger(__name__)
        self._capp = capp
        self._api = api
        self._db = db

    def route(self, data):
        """
        Retrieves brands that need to process these tickets and routes them to the appropriate service
        :param data:
        :return: dict data passed in
        """
        dq = data.get('data', {}).get('domainQuery', {})
        host_brand = dq.get('host', {}).get(self.KEY_BRAND)
        registrar_brand = dq.get('registrar', {}).get(self.KEY_BRAND)

        abuse_meta = data.get(self.KEY_ABUSE_META, '')
        if abuse_meta == 'DSA':
            ticket_id = data.get(self.KEY_TICKET_ID)
            self._capp.send_task('routing.run.process_external_report', args=[ticket_id])
            db = PhishstoryMongo(app_settings)
            db.update_incident(ticket_id, {self.KEY_PHISHSTORY_STATUS: 'FORWARDED_TO_EXTERNAL_SERVICE'})
            data[self.KEY_PHISHSTORY_STATUS] = 'FORWARDED_TO_EXTERNAL_SERVICE'
            return data

        brands = self._find_brands_to_route(host_brand, registrar_brand)

        # Closing tickets that are EMEA only.
        if len(brands) == 1 and self.EMEA in brands:
            self._close_emea_only_ticket(data.get(self.KEY_TICKET_ID))

        for brand in brands:
            self._route_to_brand(brand, data)

        return data

    def _find_brands_to_route(self, host_brand, registrar_brand):
        """
        Returns a set of either length 1 or 2, of all the brands that need to process this ticket.
        All combinations of brands that are a subset of {'GODADDY', '123REG', 'FOREIGN'} will be routed to GoDaddy.
        This prevents two tickets from being sent to the GDBS Container.
        For ex.
            1. GODADDY and 123REG will be routed to GODADDY.
            2. 123REG and FOREIGN will be routed to GODADDY.
            3. GODADDY and FOREIGN will be routed to GODADDY.
        :param host_brand:
        :param registrar_brand:
        :return: set of brands
        """
        brands = set()
        if host_brand is None and registrar_brand is None:  # Anything we don't have data for go to GoDaddy
            brands.add(self.GODADDY)
        else:
            if host_brand in self._brands:
                brands.add(host_brand)
            if registrar_brand in self._brands:
                brands.add(registrar_brand)

        # Are ALL elements in brands present in _brands_routed_to_gd ?
        if len(brands) > 1 and brands.issubset(self._brands_routed_to_gd):
            brands = {self.GODADDY}

        return brands

    def _route_to_brand(self, service, data):
        """
        Routes the provided data to the specified service, else logs error
        :param service:
        :param data:
        :return: None
        """
        try:
            self._logger.info('Routing {} to {} brand services'.format(data[self.KEY_TICKET_ID], service))
            self._capp.send_task(self._brands.get(service), (data,))
        except Exception as e:
            self._logger.error('Error trying to route ticket to {} brand services: {}'.format(service, e))

    def _close_emea_only_ticket(self, ticket):
        """
        Closes a ticket that is destined only for EMEA.
        :param ticket: dict of ticket key/value pairs
        :return: None
        """
        try:
            self._logger.info('Closing ticket: {}. No action able to be taken by GoDaddy.'.format(ticket))
            self._api.close_incident(ticket, self.CLOSE_REASON)
            self._db.update_actions_sub_document(ticket, 'closed as {}'.format(self.CLOSE_REASON))
        except Exception as e:
            self._logger.error('Error trying to close emea ticket {}: {}'.format(ticket, e))
