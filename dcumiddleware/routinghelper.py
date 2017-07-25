import abc
import logging


class RoutingHelper:
    """
    Responsible for all routing responsibilities to the brand services.
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._brands = {'GoDaddy': GoDaddyRoutingHelper,
                        'EMEA': EMEARoutingHelper,
                        'HAINAIN': HainainRoutingHelper}

    def route(self, brand, data):
        """
        Responsible for looking up the appropriate Brand Routing Helper and passing along the data to be routed.
        :param brand:
        :param data:
        :return:
        """
        if brand in self._brands:
            self._brands.get('brand').route(data)
        else:
            self._logger.warn("No brand service found for brand: {}.".format(brand))


class BrandRoutingHelper(object):
    """
    Abstract base class for brand routing
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def route(self, data):
        """
        Given enriched data from the middleware, route the data to the appropriate services
        :param data:
        :return:
        """


class GoDaddyRoutingHelper(BrandRoutingHelper):
    """
    GoDaddy specific Brand Services routing logic
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def route(self, data):
        pass


class EMEARoutingHelper(BrandRoutingHelper):
    """
    EMEA specific Brand Services routing logic
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def route(self, data):
        pass


class HainainRoutingHelper(BrandRoutingHelper):
    """
    Hainain specific Brand Services routing logic
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def route(self, data):
        pass
