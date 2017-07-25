import abc


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