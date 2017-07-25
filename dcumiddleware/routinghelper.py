import logging

from celery import Celery
from celeryconfig import CeleryConfig


class RoutingHelper:
    """
    Responsible for all routing responsibilities to the brand services.
    """

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._capp = Celery().config_from_object(CeleryConfig())
        self._brands = {'GODADDY': 'run.process_gd',
                        'EMEA': 'run.process_emea',
                        'HAINAIN': 'run.process_hainain'}

    def route(self, hostname, registrar, data):
        """
        Responsible for looking up the appropriate Brand Routing Helper and passing along the data to be routed.
        :param hostname:
        :param registrar:
        :param data:
        :return:
        """
        hosted_by_brand = hostname in self._brands
        registered_by_brand = registrar in self._brands
        same_host_and_registrar = hostname == registrar

        if not registrar and not hostname:
            self._route_to_brand('GODADDY', data)
        elif not registrar or not hostname:
            if not registrar:
                if hosted_by_brand:
                    self._route_to_brand(hostname, data)
            else:
                if registered_by_brand:
                    self._route_to_brand(registrar, data)
        else:
            # If we have the same registrar and host don't route two tickets/workflows.
            if same_host_and_registrar and hosted_by_brand:
                self._route_to_brand(hostname, data)
            elif (same_host_and_registrar and not hosted_by_brand) or (not hosted_by_brand and not registered_by_brand):
                self._route_to_brand(hostname, data)
            else:
                if hosted_by_brand:
                    self._route_to_brand(hostname, data)
                if registered_by_brand:
                    self._route_to_brand(registrar, data)

    def _route_to_brand(self, service, data):
        try:
            self._logger.info("Routing {} to {} brand services".format(data['ticketId'], service))
            self._capp.send_task(self._brands.get(service), data) #This is temporary and needs to be moved
        except Exception as e:
            self._logger.error("Error trying to route ticket to GoDaddy brand services: {}".format(e.message))
