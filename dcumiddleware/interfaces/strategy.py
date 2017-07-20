import abc
import re


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

    def parse_hostname_and_registrar(self, data):
        """
        Returns the host and registrar as a tuple from the data provided.
        :param data:
        :return:
        """
        # regex to determine if godaddy is the host and registrar
        regex = re.compile('[^a-zA-Z]')

        host = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('name', None)
        hostname = regex.sub('', host) if host is not None else None
        reg = data.get('data', {}).get('domainQuery', {}).get('registrar', {}).get('name', None)
        registrar = regex.sub('', reg) if reg is not None else None

        return hostname, registrar

    def is_blacklisted(self, data):
        """
        Returns a Boolean that represents whether or not a shopper or a domain is blacklisted.
        :param data:
        :return:
        """
        shopper_blacklist = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('vip', {}).get('blacklist', True)
        domain_blacklist = data.get('data', {}).get('domainQuery', {}).get('blacklist', True)

        return shopper_blacklist is True or domain_blacklist is True

    def is_unconfirmed_vip(self, data):
        """
        Returns a Boolean representing whether or not a shopper has an unconfirmed VIP status or not.
        :param data:
        :return:
        """
        return data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('shopperId', None) is None
