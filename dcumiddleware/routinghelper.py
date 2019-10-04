import logging


class RoutingHelper:
    """
    Responsible for all routing responsibilities to the brand services.
    """
    _brands = {'GODADDY': 'run.process_gd',
               'FOREIGN': 'run.process_gd',
               'EMEA': 'run.process_emea',
               '123REG': 'run.process_gd'}

    _brands_routed_to_gd = {'GODADDY', '123REG', 'FOREIGN'}

    def __init__(self, capp, api):
        self._logger = logging.getLogger(__name__)
        self._capp = capp
        self._api = api

    def route(self, data):
        """
        Retrieves brands that need to process these tickets and routes them to the appropriate service
        :param data:
        :return:
        """
        host_brand = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('brand', None)
        registrar_brand = data.get('data', {}).get('domainQuery', {}).get('registrar', {}).get('brand', None)

        brands = self._find_brands_to_route(host_brand, registrar_brand)

        # Closing tickets that are EMEA only.
        if len(brands) == 1 and 'EMEA' in brands:
            self._close_emea_only_ticket(data.get('ticketId'))

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
        :return brands:
        """
        brands = set()
        if host_brand is None and registrar_brand is None:  # Anything we don't have data for go to GoDaddy
            brands.add('GODADDY')
        else:
            if host_brand in self._brands:
                brands.add(host_brand)
            if registrar_brand in self._brands:
                brands.add(registrar_brand)

        if len(brands) > 1 and brands.issubset(self._brands_routed_to_gd):
            brands = {'GODADDY'}

        return brands

    def _route_to_brand(self, service, data):
        """
        Routes the provided data to the specified service, else logs error
        :param service:
        :param data:
        :return:
        """
        try:
            self._logger.info("Routing {} to {} brand services".format(data['ticketId'], service))
            self._capp.send_task(self._brands.get(service), (data,))
        except Exception as e:
            self._logger.error("Error trying to route ticket to {} brand services: {}".format(service, e.message))

    def _close_emea_only_ticket(self, ticket):
        """
        Closes a ticket that is destined only for EMEA and returns the resulting data structure from AbuseAPI
        :param ticket:
        :return:
        """
        self._logger.info("Closing ticket: {}. No action able to be taken by GoDaddy.".format(ticket))
        self._api.close_incident(ticket, 'email_sent_to_emea')
