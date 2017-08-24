import logging


class RoutingHelper:
    """
    Responsible for all routing responsibilities to the brand services.
    """
    _brands = {'GODADDY': 'run.process_gd',
               'FOREIGN': 'run.process_gd',
               'EMEA': 'run.process_emea',
               'HAINAIN': 'run.process_hainain'}

    def __init__(self, capp):
        self._logger = logging.getLogger(__name__)
        self._capp = capp

    def route(self, host_brand, registrar_brand, data):
        """
        Responsible for looking up the appropriate Brand Routing Helper and passing along the data to be routed.
        :param host_brand:
        :param registrar_brand:
        :param data:
        :return:
        """
        hosted_by_brand = host_brand in self._brands
        registered_by_brand = registrar_brand in self._brands

        brands = []

        if host_brand is None and registrar_brand is None:  # Anything we don't have data for go to GoDaddy
             self._route_to_brand('GODADDY', data)
             brands.append('GODADDY')
        else:
            if hosted_by_brand and host_brand == registrar_brand:  # Don't route two tickets for one workflow
                self._route_to_brand(host_brand, data)
                brands = [host_brand]
            else:
                if hosted_by_brand:
                    self._route_to_brand(host_brand, data)
                    brands.append(host_brand)
                if registered_by_brand:
                    self._route_to_brand(registrar_brand, data)
                    brands.append(registrar_brand)
        return brands

    def _route_to_brand(self, service, data):
        try:
            self._logger.info("Routing {} to {} brand services".format(data['ticketId'], service))
            self._capp.send_task(self._brands.get(service), (data,))
        except Exception as e:
            self._logger.error("Error trying to route ticket to {} brand services: {}".format(service, e.message))
