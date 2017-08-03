import logging


class RoutingHelper:
    """
    Responsible for all routing responsibilities to the brand services.
    """
    _brands = {'GODADDY': 'run.process_gd',
               'EMEA': 'run.process_emea',
               'HAINAIN': 'run.process_hainain'}

    def __init__(self, capp):
        self._logger = logging.getLogger(__name__)
        self._capp = capp

    def route(self, hostname, registrar, data):
        """
        Responsible for looking up the appropriate Brand Routing Helper and passing along the data to be routed.
        :param hostname:
        :param registrar:
        :param data:
        :return:
        """
        # hosted_by_brand = hostname in self._brands
        # registered_by_brand = registrar in self._brands
        #
        # brands = []
        #
        # if not registrar and not hostname:  # Anything we don't have data for go to GoDaddy
        #     self._route_to_brand('GODADDY', data)
        #     brands = ['GODADDY']
        # elif not registrar or not hostname:
        #     if not registrar:
        #         if hosted_by_brand:
        #             self._route_to_brand(hostname, data)
        #             brands.append(hostname)
        #     else:
        #         if registered_by_brand:
        #             self._route_to_brand(registrar, data)
        #             brands.append(registrar)
        # else:
        #     if hostname == registrar and hosted_by_brand:  # Don't route two tickets for one workflow
        #         self._route_to_brand(hostname, data)
        #         brands = [hostname]
        #     elif not hosted_by_brand and not registered_by_brand:  # Foreign tickets go to GoDaddy
        #         self._route_to_brand('GODADDY', data)
        #         brands = ['GODADDY']
        #     else:
        #         if hosted_by_brand:
        #             self._route_to_brand(hostname, data)
        #             brands.append(hostname)
        #         if registered_by_brand:
        #             self._route_to_brand(registrar, data)
        #             brands.append(registrar)

        # Temporary pass through for GoDaddy only routing
        self._route_to_brand('GODADDY', data)
        brands = ['GODADDY']

        return brands

    def _route_to_brand(self, service, data):
        try:
            self._logger.info("Routing {} to {} brand services".format(data['ticketId'], service))
            self._capp.send_task(self._brands.get(service), (data,))
        except Exception as e:
            self._logger.error("Error trying to route ticket to {} brand services: {}".format(service, e.message))
