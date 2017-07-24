import abc


class Strategy(object):
    """
    Abstract base class for phishstory processing strategies
    """
    __metaclass__ = abc.ABCMeta

    UNRESOLVABLE = "unresolvable"
    UNWORKABLE = "unworkable"

    HOSTED = "HOSTED"
    REGISTERED = "REGISTERED"
    FOREIGN = "FOREIGN"
    UNKNOWN = "UNKNOWN"

    @abc.abstractmethod
    def close_process(self, data, close_reason):
        """
        Close a particular ticket given a close_reason
        :param data:
        :param close_reason:
        :return:
        """

    @abc.abstractmethod
    def process(self, data, **kwargs):
        """
        Process the given incident data
        :param **kwargs:
        :param data:
        :return:
        """
