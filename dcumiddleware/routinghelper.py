import logging

from dcumiddleware.interfaces.brandroutinghelper import BrandRoutingHelper


class RoutingHelper:
    """
    Responsible for all routing responsibilities to the brand services.
    """

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._brands = {'GODADDY': GoDaddyRoutingHelper(settings),
                        'EMEA': EMEARoutingHelper(settings),
                        'HAINAIN': HainainRoutingHelper(settings)}

    def route(self, hostname, registrar, data):
        """
        Responsible for looking up the appropriate Brand Routing Helper and passing along the data to be routed.
        :param brand:
        :param data:
        :return:
        """
        if hostname and hostname in self._brands:
            self._logger.info("Ticket {} is hosted with {} routing to {} brand service.".format(data['ticketId'],
                                                                                                hostname, hostname))
            self._brands.get(hostname).route(data)

        if registrar and registrar in self._brands:
            self._logger.info("Ticket {} is registered with {} routing to {} brand service.".format(data['ticketId'],
                                                                                                registrar, registrar))
            self._brands.get(registrar).route(data)


class GoDaddyRoutingHelper(BrandRoutingHelper):
    """
    GoDaddy specific Brand Services routing logic
    """

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)

    def route(self, data):
        pass


class EMEARoutingHelper(BrandRoutingHelper):
    """
    EMEA specific Brand Services routing logic
    """

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)

    def route(self, data):
        pass


class HainainRoutingHelper(BrandRoutingHelper):
    """
    Hainain specific Brand Services routing logic
    """

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)

    def route(self, data):
        pass
