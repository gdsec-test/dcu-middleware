import abc


class Strategy(object):
    """
    Abstract base class for phishstory processing strategies
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def process(self, data, **kwargs):
        """
        Process the given incident data
        :param **kwargs:
        :param data:
        :return:
        """