import logging


class RoutingHelper:
    """
    Responsible for all routing responsibilities to the brand services.
    """
    _brands = {'GODADDY': 'run.process_gd',
               'FOREIGN': 'run.process_gd',
               'EMEA': 'run.process_emea',
               'HAINAIN': 'run.process_hainain'}

    def __init__(self, capp, db):
        self._logger = logging.getLogger(__name__)
        self._capp = capp
        self._db = db

    def route(self, data):
        """
        Retrieves brands that need to process these tickets and routes them to the appropriate service
        :param data:
        :return:
        """
        host_brand = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('brand', None)
        registrar_brand = data.get('data', {}).get('domainQuery', {}).get('registrar', {}).get('brand', None)

        brands = self._find_brands_to_route(host_brand, registrar_brand)

        if len(brands) == 1 and 'EMEA' in brands:
            # Need to be sure to return the updated data structure to Celery and EMEABS Container
            data = self._close_emea_only_ticket(data.get('ticketId'))

        # All foreign tickets get sent to GoDaddy so this prevents two tickets being sent to GDBS Container
        if 'FOREIGN' in brands and 'GODADDY' in brands:
            brands = ['GODADDY']

        for brand in brands:
            self._route_to_brand(brand, data)

        return data

    def _find_brands_to_route(self, host_brand, registrar_brand):
        """
        Returns a list of either length 1 or 2, of all the brands that need to process this ticket.
        :param host_brand:
        :param registrar_brand:
        :return:
        """
        hosted_by_brand = host_brand in self._brands
        registered_by_brand = registrar_brand in self._brands

        brands = []

        if host_brand is None and registrar_brand is None:  # Anything we don't have data for go to GoDaddy
            brands.append('GODADDY')
        else:
            if hosted_by_brand and host_brand == registrar_brand:  # Don't route two tickets for one workflow
                brands = [host_brand]
            else:
                if hosted_by_brand:
                    brands.append(host_brand)
                if registered_by_brand:
                    brands.append(registrar_brand)
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
        Closes a ticket that is destined only for EMEA and returns the resulting data structure from MongoDB
        :param ticket:
        :return:
        """
        self._logger.info("Closing ticket: {}. No action able to be taken by GoDaddy.".format(ticket))
        return self._db.close_incident(ticket, dict(close_reason='email_sent_to_emea'))
